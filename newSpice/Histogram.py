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
# Name:        Histogram.py
# Purpose:     Make an histogram plot based on data provided by the user
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Created:     17-01-2017
# Licence:     refer to the LICENSE file
# -------------------------------------------------------------------------------
"""
This module uses matplotlib to plot a histogram of a gaussian distribution and calculates the project n-sigma interval.

The data can either be retrieved from the clipboard or from a text file. Use the following command line text to call
this module.

.. code-block:: text

    python -m newSpice.Histogram [options] [data_file] TRACE

The help can be obtained by calling the script without arguments

.. code-block:: text

    Usage: Histogram.py [options] LOG_FILE TRACE

    Options:
      --version             show program's version number and exit
      -h, --help            show this help message and exit
      -s SIGMA, --sigma=SIGMA
                            Sigma to be used in the distribution fit. Default=3
      -n NBINS, --nbins=NBINS
                            Number of bins to be used in the histogram. Default=20
      -c FILTERS, --condition=FILTERS
                            Filter condition writen in python. More than one
                            expression can be added but each expression should be
                            preceded by -c. EXAMPLE: -c V(N001)>4 -c parameter==1
                            -c  I(V1)<0.5
      -f FORMAT, --format=FORMAT
                            Format string for the X axis. Example: -f %3.4f
      -t TITLE, --title=TITLE
                            Title to appear on the top of the histogram.
      -r RANGE, --range=RANGE
                            Range of the X axis to use for the histogram in the
                            form min:max. Example: -r -1:1
      -C, --clipboard       If the data from the clipboard is to be used.
      -i IMAGEFILE, --image=IMAGEFILE
                            Name of the image File. extension 'png'


"""
__author__ = "Nuno Canto Brum <me@nunobrum.com>"
__copyright__ = "Copyright 2017, Fribourg Switzerland"

def main():
    import numpy as np
    from scipy.stats import norm
    import matplotlib.pyplot as plt

    from optparse import OptionParser

    usage = "usage: %prog [options] LOG_FILE TRACE"
    opts = OptionParser(usage=usage, version="%prog 0.1")
    # opts.add_option('v', "var", action="store", type="string", dest="trace", help="The trace to be used in the histogram")
    opts.add_option('-s', "--sigma", action="store", type="int", dest="sigma", default=3,
                    help="Sigma to be used in the distribution fit. Default=3")
    opts.add_option('-n', "--nbins", action="store",  type="int", dest="nbins", default=20,
                    help="Number of bins to be used in the histogram. Default=20")
    opts.add_option('-c', "--condition", action="append", type="string", dest="filters",
                    help="Filter condition writen in python. More than one expression can be added but each expression "
                         "should be preceded by -c.\n" +
                         "EXAMPLE: -c V(N001)>4 -c parameter==1 -c  I(V1)<0.5" )
    opts.add_option('-f', "--format", action="store", type="string", dest="format",
                    help="Format string for the X axis. Example: -f %3.4f")
    # opts.add_option('-p', "--scaling",action="store", type="string", dest="prescaling",
    # help="Prescaling function to be applied to the input value.")
    opts.add_option('-t', "--title", action="store", type="string", dest="title",
                    help="Title to appear on the top of the histogram.")
    opts.add_option('-r', "--range", action="store", type="string", dest="range",
                    help="Range of the X axis to use for the histogram in the form min:max. Example: -r -1:1")
    opts.add_option('-C', "--clipboard", action="store_true", dest="clipboard",
                    help="If the data from the clipboard is to be used.")
    # opts.add_option('-x', "--xname", action="store", dest="xname", help="Name for the variable displayed")
    opts.add_option('-o', "--output", action="store", type="string", dest="imagefile",
                    help="Output the image to a file. Argument is the name of the image File with png extension.\n"
                         "Example: -o image.png")
    opts.add_option('-1', "--nonorm", action="store_false", dest="normalized", default=True,
                    help="Doesn't normalize the histogram so that area of the bell curve is 1.")
    (options, args) = opts.parse_args()

    values = []


    if options.clipboard:
        try:
            import clipboard
        except ImportError:
            print("Failed to load clipboard package. Use PiP to install it.")
            exit(1)
        if len(args) > 0:
            TRACE = args[-1]
        else:
            TRACE = "var"
        text = clipboard.paste()
        for line in text.split('\n'):
            try:
                values.append(float(line))
            except ValueError:
                print("Failed to convert line: '", line, "'")
    elif len(args) == 0:
        opts.print_help()
        exit(-1)
    else:
        if len(args) < 2:
            opts.error("Wrong number of parameters. Need to give the filename and the trace.")
            opts.print_help()
            exit(-1)
        TRACE = args[1]
        logfile = args[0]

        if not options.filters is None:
            print("Filters Applied:", options.filters)
        else:
            print("No filters defined")

        log = open(logfile,'r')
        header = log.readline().rstrip('\r\n')
        vars = header.split('\t')
        try:
            sav_col = vars.index(TRACE)
        except ValueError:
            log.close()
            print("File '%s' doesn't have trace '%s'" % (logfile, TRACE))
            print("LOG FILE contains %s" % vars)
            exit(-1)

        if (options.filters is None) or (len(options.filters) == 0):
            for line in log:
                #print(line)
                vs = line.split('\t')
                values.append(float(vs[sav_col]))
        else:
            for line in log:
                vs = map(float,line.split('\t'))
                env = dict(zip(vars,vs))

                for expression in options.filters:
                    test = eval(expression, None, env)
                    if test == False:
                        break
                else:
                    values.append(float(env[TRACE]))
        log.close()

    if len(values) == 0:
        print("No elements found")
    elif len(values) < options.nbins:
        print("Not enough elements for an histogram")
    else:
        x = np.array(values, dtype=float)
        mu = x.mean()
        mn = x.min()
        mx = x.max()
        sd = np.std(x)
        sigmin = mu - options.sigma*sd
        sigmax = mu + options.sigma*sd

        if options.range is None:
            # Automatic calculation of the range
            axisXmin = mu - (options.sigma + 1) * sd
            axisXmax = mu + (options.sigma + 1) * sd

            if mn < axisXmin:
                axisXmin = mn

            if mx > axisXmax:
                axisXmax = mx
        else:
            try:
                smin, smax = options.range.split(":")
                axisXmin = float(smin)
                axisXmax = float(smax)
            except:
                opts.error("Invalid range setting")
                exit(-1)
        if options.format:
            fmt = options.format
        else:
            fmt = "%f"

        print("Collected %d elements" % len(values))
        print("Distributing in %d bins" % options.nbins)
        print("Minimum is " + fmt % mn)
        print("Maximum is " + fmt % mx)
        print("Mean is " + fmt % mu)
        print("Standard Deviation is " + fmt % sd)
        print(("Sigma %d boundaries are " + fmt + " and " + fmt) % (options.sigma, sigmin, sigmax))
        n, bins, patches = plt.hist(x, options.nbins, density=options.normalized, facecolor='green', alpha=0.75,
                                    range=(axisXmin, axisXmax))
        axisYmax = n.max() * 1.1

        if options.normalized:
            # add a 'best fit' line
            y = norm.pdf(bins, mu, sd)
            l = plt.plot(bins, y, 'r--', linewidth=1)
            plt.axvspan(mu - options.sigma*sd, mu + options.sigma*sd, alpha=0.2, color="cyan")
            plt.ylabel('Distribution [Normalised]')
        else:
            plt.ylabel('Distribution')
        plt.xlabel(TRACE)

        if options.title is None:
            title = (r'$\mathrm{Histogram\ of\ %s:}\ \mu='+fmt+r',\ stdev='+fmt+r',\ \sigma=%d$') % (TRACE, mu, sd, options.sigma)
        else:
            title = options.title
        plt.title(title)

        plt.axis([axisXmin, axisXmax, 0, axisYmax ])
        plt.grid(True)
        if options.imagefile is not None:
            plt.savefig(options.imagefile)
        else:
            plt.show()
main()
