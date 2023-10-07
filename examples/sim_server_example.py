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
# Name:        run_server.py
# Purpose:     A Command Line Interface to run the LTSpice Server
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Created:     10-08-2023
# Licence:     refer to the LICENSE file
# -------------------------------------------------------------------------------
import sys

import time
import keyboard
import logging

from newSpice.client_server.sim_server import SimServer
from newSpice.simulators.ltspice_simulator import LTspice
simulator = LTspice

_logger = logging.getLogger("newSpice.SimServer")
_logger.setLevel(logging.DEBUG)
_logger.addHandler(logging.StreamHandler(sys.stdout))

print("Starting Server")
server = SimServer(simulator, parallel_sims=4, output_folder='./temp_server', port=9000)
print("Server Started. Press and hold 'q' to stop")

while server.running():
    time.sleep(0.2)
    # Check whether a key was pressed
    if keyboard.is_pressed('q'):
        server.stop_server()
        break
