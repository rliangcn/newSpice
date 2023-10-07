#!/usr/bin/env python

# -------------------------------------------------------------------------------
#
#  ███████╗██████╗ ██╗ ██████╗███████╗██╗     ██╗██████╗
#  ██╔════╝██╔══██╗██║██╔════╝██╔════╝██║     ██║██╔══██╗
#  ███████╗██████╔╝██║██║     █████╗  ██║     ██║██████╔╝
#  ╚════██║██╔═══╝ ██║██║     ██╔══╝  ██║     ██║██╔══██╗
#  ███████║██║     ██║╚██████╗███████╗███████╗██║██████╔╝
#  ╚══════╝╚═╝     ╚═╝ ╚═════╝╚══════╝╚══════╝╚═╝╚═════╝
#
# Name:        sim_stepping.py
# Purpose:     Spice Simulation Library intended to automate the exploring of
#              design corners, try different models and different parameter
#              settings.
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Created:     31-07-2020
# Licence:     refer to the LICENSE file
# -------------------------------------------------------------------------------

__author__ = "Nuno Canto Brum <nuno.brum@gmail.com>"
__copyright__ = "Copyright 2017, Fribourg Switzerland"

from typing import Callable, Any, Union
from typing import Iterable
import pathlib
from functools import wraps
import logging
_logger = logging.getLogger("newSpice.SimStepper")
from ..editor.base_editor import BaseEditor
from .sim_runner import AnyRunner, SimRunner


class StepInfo(object):
    def __init__(self, what: str, elem: str, iterable: Iterable):
        self.what = what
        self.elem = elem
        self.iter = iterable

    def __len__(self):
        return len(list(self.iter))

    def __str__(self):
        return f"Iteration on {self.what} {self.elem} : {self.iter}"


class SimStepper(object):
    """This class is intended to be used for simulations with many parameter sweeps. This provides a more
    user-friendly interface than the SpiceEditor/SimRunner class when there are many parameters to be stepped.

    Using the SpiceEditor/SimRunner classes a loop needs to be added for each dimension of the simulations.
    A typical usage would be as follows:
    ```
    netlist = SpiceEditor("my_circuit.asc")
    runner = SimRunner(parallel_sims=4)
    for dmodel in ("BAT54", "BAT46WJ")
        netlist.set_element_model("D1", model)  # Sets the Diode D1 model
        for res_value1 in sweep(2.2, 2,4, 0.2):  # Steps from 2.2 to 2.4 with 0.2 increments
            netlist.set_component_value('R1', res_value1)  # Updates the resistor R1 value to be 3.3k
            for temperature in sweep(0, 80, 20):  # Makes temperature step from 0 to 80 degrees in 20 degree steps
                netlist.set_parameters(temp=80)  # Sets the simulation temperature to be 80 degrees
                for res_value2 in (10, 25, 32):
                    netlist.set_component_value('R2', res_value2)  # Updates the resistor R2 value to be 3.3k
                    runner.run(netlist)

    runner.wait_completion()  # Waits for the Spice simulations to complete
    ```

    With SimStepper the same thing can be done as follows, resulting in a cleaner code.

    ```
    netlist = SpiceEditor("my_circuit.asc")
    Stepper = SimStepper(netlist, SimRunner(parallel_sims=4, output_folder="./output"))
    Stepper.add_model_sweep('D1', "BAT54", "BAT46WJ")
    Stepper.add_component_sweep('R1', sweep(2.2, 2,4, 0.2))  # Steps from 2.2 to 2.4 with 0.2 increments
    Stepper.add_parameter_sweep('temp', sweep(0, 80, 20))  # Makes temperature step from 0 to 80 degrees in 20
                                                           # degree steps
    Stepper.add_component_sweep('R2', (10, 25, 32)) #  Updates the resistor R2 value to be 3.3k
    Stepper.run_all()

    ```

    Another advantage of using SimStepper is that it can optionally use the .SAVEBIAS in the first simulation and
    then use the .LOADBIAS command at the subsequent ones to speed up the simulation times.
    """

    def __init__(self, circuit: BaseEditor, runner: AnyRunner):
        self.runner = runner
        self.netlist = circuit
        self.iter_list = []

    @wraps(BaseEditor.add_instruction)
    def add_instruction(self, instruction: str):
        self.netlist.add_instruction(instruction)

    @wraps(BaseEditor.add_instructions)
    def add_instructions(self, *instructions) -> None:
        self.netlist.add_instructions(*instructions)

    @wraps(BaseEditor.remove_instruction)
    def remove_instruction(self, instruction) -> None:
        self.netlist.remove_instruction(instruction)

    @wraps(BaseEditor.set_parameters)
    def set_parameters(self, **kwargs):
        self.netlist.set_parameters(**kwargs)

    @wraps(BaseEditor.set_parameter)
    def set_parameter(self, param: str, value: Union[str, int, float]) -> None:
        self.netlist.set_parameter(param, value)

    @wraps(BaseEditor.set_component_values)
    def set_component_values(self, **kwargs):
        self.netlist.set_component_values(**kwargs)

    @wraps(BaseEditor.set_component_value)
    def set_component_value(self, device: str, value: Union[str, int, float]) -> None:
        self.netlist.set_component_value(device, value)

    @wraps(BaseEditor.set_element_model)
    def set_element_model(self, element: str, model: str) -> None:
        self.netlist.set_element_model(element, model)

    def add_param_sweep(self, param: str, iterable: Iterable):
        """Adds a dimension to the simulation, where the param is swept."""
        self.iter_list.append(StepInfo("param", param, iterable))

    def add_value_sweep(self, comp: str, iterable: Iterable):
        """Adds a dimension to the simulation, where a component value is swept."""
        # The next line raises an ComponentNotFoundError if the component doesn't exist
        _ = self.netlist.get_component_value(comp)
        self.iter_list.append(StepInfo("component", comp, iterable))

    def add_model_sweep(self, comp: str, iterable: Iterable):
        """Adds a dimension to the simulation, where a component model is swept."""
        # The next line raises an ComponentNotFoundError if the component doesn't exist
        _ = self.netlist.get_component_value(comp)
        self.iter_list.append(StepInfo("model", comp, iterable))

    def total_number_of_simulations(self):
        """Returns the total number of simulations foreseen."""
        total = 1
        for step in self.iter_list:
            l = len(step)
            if l:
                total *= l
            else:
                _logger.debug(f"'{step}' is empty.")
        return total

    def run_all(self, callback: Callable[[str, str], Any] = None, use_loadbias='Auto', wait_completion=True):
        assert use_loadbias in ('Auto', 'Yes', 'No'), "use_loadbias argument must be 'Auto', 'Yes' or 'No'"
        if (use_loadbias == 'Auto' and self.total_number_of_simulations() > 10) or use_loadbias == 'Yes':
            # It will choose to use .SAVEBIAS/.LOADBIAS if the number of simulaitons is higher than 10
            # TODO: Make a first simulation and storing the bias
            pass
        iter_no = 0
        iterators = [iter(step.iter) for step in self.iter_list]
        while True:
            while 0 <= iter_no < len(self.iter_list):
                try:
                    value = iterators[iter_no].__next__()
                except StopIteration:
                    iterators[iter_no] = iter(self.iter_list[iter_no].iter)
                    iter_no -= 1
                    continue
                if self.iter_list[iter_no].what == 'param':
                    self.netlist.set_parameter(self.iter_list[iter_no].elem, value)
                elif self.iter_list[iter_no].what == 'component':
                    self.netlist.set_component_value(self.iter_list[iter_no].elem, value)
                elif self.iter_list[iter_no].what == 'model':
                    self.netlist.set_element_model(self.iter_list[iter_no].elem, value)
                else:
                    # TODO: develop other types of sweeps EX: add .STEP instruction
                    raise ValueError("Not Supported sweep")
                iter_no += 1
            if iter_no < 0:
                break
            self.runner.run(self.netlist, callback=callback)  # Like this a recursion is avoided
            iter_no = len(self.iter_list) - 1  # Resets the counter to start next iteration
        if wait_completion:
            # Now waits for the simulations to end
            self.runner.wait_completion()

    def run(self):
        """Rather uses run_all instead"""
        self.run_all()

    @property
    def okSim(self):
        return self.runner.okSim

    @property
    def runno(self):
        return self.runner.runno


if __name__ == "__main__":
    from newSpice.utils.sweep_iterators import *

    test = SimStepper("../../tests/DC sweep.asc")
    test.verbose = True
    test.set_parameter('R1', 3)
    test.add_param_sweep("res", [10, 11, 9])
    test.add_value_sweep("R1", sweep_log(0.1, 10))
    # test.add_model_sweep("D1", ("model1", "model2"))
    test.run_all()
    print("Finished")
    exit(0)
