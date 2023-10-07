#!/usr/bin/env python
# coding=utf-8

# -------------------------------------------------------------------------------
#
#  ███████╗██████╗ ██╗ ██████╗███████╗██╗     ██╗██████╗
#  ██╔════╝██╔══██╗██║██╔════╝██╔════╝██║     ██║██╔══██╗
#  ███████╗██████╔╝██║██║     █████╗  ██║     ██║██████╔╝
#  ╚════██║██╔═══╝ ██║██║     ██╔══╝  ██║     ██║██╔══██╗
#  ███████║██║     ██║╚██████╗███████╗███████╗██║██████╔╝
#  ╚══════╝╚═╝     ╚═╝ ╚═════╝╚══════╝╚══════╝╚═╝╚═════╝
#
# Name:        srv_sim_runner.py
# Purpose:     Manager of the simulation sim_tasks on the server side
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Created:     23-02-2023
# Licence:     refer to the LICENSE file
# -------------------------------------------------------------------------------
import threading
import time
from typing import Union, List, Dict, Any
from pathlib import Path
import zipfile
import logging
_logger = logging.getLogger("newSpice.ServerSimRunner")

from ..sim.sim_runner import SimRunner
from ..editor.base_editor import BaseEditor


def zip_files(raw_filename: Path, log_filename: Path):
    zip_filename = raw_filename.with_suffix('.zip')
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.write(raw_filename)
        zip_file.write(log_filename)
    return zip_filename


class ServerSimRunner(threading.Thread):
    """This class maintains updated status of the SimRunner.
    It was decided not to make SimRunner a super class and rather make it manipulate directly the structures of
    SimRunner. The rationale for this, was to avoid confusions between the run() on the Thread class and the
    run on the SimRunner class.
    Making a class derive from two different classes needs to be handled carefully.

    In consequence of the rationale above, many of the functions that were handled by the SimRunner are overriden
    by this class.
    """

    def __init__(self, parallel_sims: int = 4, timeout: float = None, verbose=True, output_folder: str = None, simulator=None):
        super().__init__(name="SimManager")
        self.runner = SimRunner(simulator=simulator, parallel_sims=parallel_sims, timeout=timeout,
                                verbose=verbose, output_folder=output_folder)
        self.completed_tasks: List[Dict[str, Any]] = []  # This is a list of dictionaries with the information of the completed tasks
        self._stop = False

    def run(self) -> None:
        """This function makes a direct manipulation of the structures of SimRunner. This option is """
        while True:
            self.runner.update_completed()
            while len(self.runner.completed_tasks) > 0:
                task = self.runner.completed_tasks.pop(0)
                zip_filename = task.callback_return
                self.completed_tasks.append({
                    'runno': task.runno,
                    'retcode': task.retcode,
                    'circuit': task.netlist_file,
                    'raw': task.raw_file,
                    'log': task.log_file,
                    'zipfile': zip_filename,
                    'start': task.start_time,
                    'stop': task.stop_time,
                })
                _logger.debug(f"Task {task} is finished")
                _logger.debug(self.completed_tasks[-1])
                _logger.debug(len(self.completed_tasks))

            time.sleep(0.2)
            if self._stop is True:
                break
        self.runner.wait_completion()
        self.runner.file_cleanup()  # Delete things that have been left behind

    def add_simulation(self, netlist: Union[str, Path, BaseEditor], *, timeout: float = 600) -> int:
        """"""
        _logger.debug(f"starting Simulation of {netlist}")
        task = self.runner.run(netlist, wait_resource=True, timeout=timeout, callback=zip_files)
        if task is None:
            _logger.error(f"Failed to start task {netlist}")
            return -1
        else:
            _logger.info(f"Started task {netlist} with job_id{task.runno}")
            return task.runno

    def _erase_files_and_info(self, pos):
        task = self.completed_tasks[pos]
        for filename in ('circuit', 'log', 'raw', 'zipfile'):
            f = task[filename]
            if f.exists():
                _logger.info(f"deleting {f}")
                f.unlink()
        del self.completed_tasks[pos]

    def erase_files_of_runno(self, runno):
        """Will delete all files related with a completed task. Will also delete information on the completed_tasks
        attribute."""
        for i, task_info in enumerate(self.completed_tasks):
            if task_info['runno'] == runno:
                self._erase_files_and_info(i)
                break

    def cleanup_completed(self):
        while len(self.completed_tasks):
            self._erase_files_and_info(0)

    def stop(self):
        _logger.info("stopping...ServerSimRunner")
        self._stop = True

    def running(self):
        return self._stop is False
