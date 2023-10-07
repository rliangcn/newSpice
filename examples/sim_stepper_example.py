import os

from newSpice import SpiceEditor, SimRunner
from newSpice.simulators.ltspice_simulator import LTspice
from newSpice.sim.sim_stepping import SimStepper


def processing_data(raw_file, log_file):
    print("Handling the simulation data of %s" % log_file)

runner = SimRunner(parallel_sims=4, output_folder='./temp2', simulator=LTspice)

# select spice model
Stepper = SimStepper(SpiceEditor("./testfiles/Batch_Test.net"), runner)
# set default arguments

Stepper.set_parameters(res=0, cap=100e-6)
Stepper.set_component_value('R2', '2k')
Stepper.set_component_value('R1', '4k')
Stepper.set_element_model('V3', "SINE(0 1 3k 0 0 0)")
# define simulation
Stepper.add_instructions(
    "; Simulation settings",
    ";.param run = 0"
)
Stepper.set_parameter('run', 0)
Stepper.set_parameter('test_param2', 20)
Stepper.add_model_sweep('XU1', ('AD712', 'AD820'))
Stepper.add_value_sweep('V1', (5, 10, 15))
# Stepper.add_value_sweep('V1', (-5, -10, -15))

# run_netlist_file = "{}_{}_{}.net".format(Stepper.circuit_radic, opamp, supply_voltage)
Stepper.run_all(callback=processing_data)

# Sim Statistics
print('Successful/Total Simulations: ' + str(Stepper.okSim) + '/' + str(Stepper.runno))
runner.file_cleanup()
