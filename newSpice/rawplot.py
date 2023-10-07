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
# Name:        rawplot.py
# Purpose:     Make a plot of the data in the raw file
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Created:     02-09-2023
# Licence:     refer to the LICENSE file
# -------------------------------------------------------------------------------


def main():
    """Uses matplotlib to plot the data in the raw file"""
    import sys
    import matplotlib
    import matplotlib.pyplot as plt

    from numpy import abs as mag, angle as phase_np
    from numpy import angle, arange

    from newSpice import RawRead

    def what_to_units(whattype):
        """Determines the unit to display on the plot Y axis"""
        if 'voltage' in whattype:
            return 'V'
        if 'current' in whattype:
            return 'A'

    matplotlib.use('tkagg')

    if len(sys.argv) > 2:
        raw_filename = sys.argv[1]
        trace_names = sys.argv[2:]
    elif len(sys.argv) > 1:
        raw_filename = sys.argv[1]
        trace_names = '*'  # All traces
    else:
        print("Usage: rawplot.py RAW_FILE TRACE_NAME")
        print("TRACE_NAME is the traces to plot")
        sys.exit(-1)

    LTR = RawRead(raw_filename, trace_names, verbose=True)
    for param, value in LTR.raw_params.items():
        print("{}: {}{}".format(param, " " * (20 - len(param)), str(value).strip()))

    if trace_names == '*':

        print("Reading all the traces in the raw file")
        trace_names = LTR.get_trace_names()

    traces = [LTR.get_trace(trace) for trace in trace_names]
    if LTR.axis is not None:
        steps_data = LTR.get_steps()
    else:
        steps_data = [0]
    print("Steps read are :", list(steps_data))

    n_axis = len(traces)

    fig, axis_set = plt.subplots(nrows=n_axis, ncols=1, sharex='all')

    if n_axis == 1:
        axis_set = [axis_set]  # Needs to have a list of axis

    for i, trace in enumerate(traces):
        ax = axis_set[i]

        ax.grid(True)
        if 'log' in LTR.flags:
            ax.set_xscale('log')
        for step_i in steps_data:
            if LTR.axis:
                x = LTR.get_axis(step_i)
            else:
                x = arange(LTR.nPoints)
            y = traces[i].get_wave(step_i)
            label = f"{trace.name}:{steps_data[step_i]})"
            if 'complex' in LTR.flags:
                x = mag(x)
                ax.set_yscale('log')
                y = mag(y)
                ax.yaxis.label.set_color('blue')
                ax.set(ylabel=label+'(dB)')
                ax.plot(x, y)
                ax_phase = ax.twinx()
                y = phase_np(y, deg=True)
                ax_phase.plot(x, y, color='red', linestyle='-.')
                ax_phase.yaxis.label.set_color('red')
                ax_phase.set(ylabel=label+'Phase (o)')
                # title = f"{trace.name} Phase [deg]"
                # ax.set_title(title)
            else:
                ax.plot(x, y)
                ax.set(ylabel=label)
                # title = f"{trace.name} [{what_to_units(trace.whattype)}]"
                # ax.set_title(title)
    fig.tight_layout()
    plt.show()
'''
'''
# out = open("RAW_TEST_out_test1.txt", 'w')
#
# for step in LTR.get_steps():
#     for x in range(len(LTR[0].data)):
#         out.write("%s, %e, %e\n" % (step, LTR[0].data[x], LTR[2].data[x]))
# out.close()
if __name__ == "__main__":
    main()
