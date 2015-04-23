######################################################################
# The ATCA Sensitivity Calculator
# Command line master handler.
# Copyright 2015 Jamie Stevens, CSIRO
#
# This file is part of the ATCA Sensitivity Calculator.
#
# The ATCA Sensitivity Calculator is free software: you can
# redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# The ATCA Sensitivity Calculator is distributed in the hope
# that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License
# along with the ATCA Sensitivity Calculator.
# If not, see <http://www.gnu.org/licenses/>.

import argparse
import sys
import atsenscalc_main as sens

if __name__ == "__main__":
    # Set up the arguments.
    for i, arg in enumerate(sys.argv):
        # Deal with the possibly negative number that is declination.
        if (arg[0] == '-') and arg[1].isdigit():
            sys.argv[i] = ' ' + arg
            
    parser = argparse.ArgumentParser() 
    parser.add_argument("--ca06", action="store_true",
                        help="include CA06 for the calculations")
    parser.add_argument("-a", "--halimit", type=float, default=6,
                        help="the hour angle limit to use (decimal hours)")
    parser.add_argument("-b", "--corrconfig", default="CFB1M",
                        help="the correlator configuration",
                        choices=[ "CFB1M", "CFB64M" ])
    parser.add_argument("-B", "--birdies", action="store_true",
                        help="flag the birdies in the continuum band")
    parser.add_argument("-c", "--configuration",
                        help="the array configuration", default="6000",
                        choices=[ "6000", "6km", "3000", "3km", "1500", "1.5km",
                                  "750", "750m", "367", "EW352", "EW367", "EW352/367",
                                  "h214", "H214", "h168", "H168", "h75", "H75" ]);
    parser.add_argument("-C", "--calculate-time", action="store_true",
                        help="the calculator will determine the time required to reach the target sensitivity")
    parser.add_argument("-d", "--dec", type=float, default=-30,
                        help="the declination of the source (decimal degrees)")
    parser.add_argument("-e", "--ellimit", type=float, default=12,
                        help="the elevation limit to use (decimal degrees)")
    parser.add_argument("-E", "--edge", type=int, default=0,
                        help="the number of edge channels to flag")
    parser.add_argument("-f", "--frequency", type=int,
                        help="the central frequency of the observations (MHz)")
    parser.add_argument("-F", "--per-freq", type=float, default=50.0,
                        help="the minimum frequency spacing between atmospheric corrections (MHz)")
    parser.add_argument("-H", "--ha-min", type=float,
                        help="the lowest hour angle observed (decimal hours)")
    parser.add_argument("-K", "--ha-max", type=float,
                        help="the highest hour angle observed (decimal hours)")
    parser.add_argument("-M", "--ha-middle", type=float, default=0.0,
                        help="the middle hour angle observed (decimal hours)")
    parser.add_argument("-o", "--output", default="spectrum",
                        help="the name of the PNG file to output the RMS v frequency spectrum to (no extension)")
    parser.add_argument("-p", "--human-readable", action="store_true", default=True,
                        help="make human readable output (default for command line version)")
    parser.add_argument("-P", "--per-ha", type=float, default=5.0,
                        help="the number of calculations of atmosphere made per hour")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="do not output progress messages")
    parser.add_argument("-r", "--restfreq", type=float,
                        help="use this rest frequency to calculate the velocity parameters (GHz)")
    parser.add_argument("-R", "--rfi", action="store_true",
                        help="flag known RFI-affected regions of the continuum spectrum")
    parser.add_argument("-s", "--smoothing", type=int, default=1,
                        help="the number of continuum spectral channels to bin together in the output")
    parser.add_argument("-S", "--season", default="ANNUAL",
                        choices=[ "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
                                  "JUL", "AUG", "SEP", "OCT", "NOV", "DEC",
                                  "SUMMER", "AUTUMN", "WINTER", "SPRING",
                                  "APRS", "OCTS", "ANNUAL" ],
                        help="the conditions to assume for weather dependence")
    parser.add_argument("-t", "--integration", type=float, default=720,
                        help="the amount of on-source integration time (min)")
    parser.add_argument("-T", "--target", type=float, default=0.0,
                        help="the target sensitivity to reach")
    parser.add_argument("--target-continuum", action="store_true",
                        help="the target sensitivity is for the continuum image")
    parser.add_argument("--target-spectral", action="store_true",
                        help="the target sensitivity is for the spectral RMS in the continuum band")
    parser.add_argument("--target-zoom", action="store_true",
                        help="the target sensitivity is for the spectral RMS in a typical zoom band")
    parser.add_argument("--target-specific-zoom", action="store_true",
                        help="the target sensitivity is for the spectral RMS in the specific zoom band")
    parser.add_argument("--target-flux-density", action="store_true",
                        help="the target sensitivity is specified as a flux density in mJy")
    parser.add_argument("--target-brightness-temperature", action="store_true",
                        help="the target sensitivity is specified as a brightness temperature in mK")
    parser.add_argument("--target-best", action="store_true",
                        help="the target sensitivity is to be obtained in the best weather conditions")
    parser.add_argument("--target-typical", action="store_true",
                        help="the target sensitivity is to be obtained in typical weather conditions")
    parser.add_argument("--target-worst", action="store_true",
                        help="the target sensitivity is to be obtained in the worst weather conditions")
    parser.add_argument("-w", "--weighting", default="R2",
                        help="the image weighting scheme",
                        choices=[ "R2", "R1", "R0", "R-1", "R-2" ])
    parser.add_argument("-W", "--zoom-width", default=1, type=int,
                        help="the number of concatenated zoom bands to use for the specific zoom")
    parser.add_argument("-y", "--zoom-smoothing", type=int, default=1,
                        help="the number of zoom spectral channels to bin together in the output")
    parser.add_argument("-z", "--zoomfreq", type=int,
                        help="a specific zoom frequency to calculate parameters for")
    parser.add_argument("-Z", "--zoom-edge", type=int, default=0,
                        help="the number of edge channels to flag in the zoom band")
    args = parser.parse_args()
    sens.main(args)
