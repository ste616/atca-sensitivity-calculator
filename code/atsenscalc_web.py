#!/usr/bin/env python
#
######################################################################
# The ATCA Sensitivity Calculator
# Web service master handler.
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

import cgi
import random
import os
import socket
if (socket.gethostname() == 'namoi'):
    # Need to setup the matplotlib area.
    os.environ['HOME'] = '/var/www/vhosts/www.narrabri.atnf.csiro.au/cgi-bin/obstools'
import matplotlib
# This line is needed since we run matplotlib without an X-server.
matplotlib.use('Agg')
import atsenscalc_main as sens

# Set up a structure that can be used like the args in the argparse library.
class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)
    def __iter__(self):
        return iter(self.__dict__.items())

if __name__ == "__main__":
    # Get the form values.
    form = cgi.FieldStorage()

    # Set up the temporary argument dictionary. This is done in the same
    # order as in the command line version of the calculator.
    fargs = {}
    
    # Include CA06 for the calculations.
    fargs['ca06'] = ("ca06" in form)

    # The hour angle limit to use (decimal hours).
    # Default 6.
    if ("halimit" in form):
        fargs['halimit'] = float(form['halimit'].value)
    else:
        fargs['halimit'] = 6.0

    # The correlator configuration [ "CFB1M" or "CFB64M" ].
    # Default "CFB1M".
    if ("corrconfig" in form):
        fargs['corrconfig'] = form['corrconfig'].value
    else:
        fargs['corrconfig'] = "CFB1M"

    # Flag the birdies in the continuum band.
    fargs['birdies'] = ("birdies" in form)

    # The array configuration [ "6000", "6km", "3000", "3km", "1500", "1.5km",
    #                           "750", "750m", "367", "EW352", "EW367", "EW352/367",
    #                           "h214", "H214", "h168", "H168", "h75", "H75" ]
    # Default "6000".
    if ("configuration" in form):
        fargs['configuration'] = form['configuration'].value
    else:
        fargs['configuration'] = "6000"

    # The calculator will determine the time required to reach the
    # target sensitivity.
    fargs['calculate_time'] = ("calculate_time" in form)
    
    # The declination of the source (decimal degrees).
    # Default -30.
    if ("dec" in form):
        fargs['dec'] = float(form['dec'].value)
    else:
        fargs['dec'] = -30.0

    # The elevation limit to use (decimal degrees).
    # Default 12.
    if ("ellimit" in form):
        fargs['ellimit'] = float(form['ellimit'].value)
    else:
        fargs['ellimit'] = 12.0

    # The number of edge channels to flag.
    # Default 0.
    if ("edge" in form):
        fargs['edge'] = int(form['edge'].value)
    else:
        fargs['edge'] = 0

    # The central frequency of the observations (MHz).
    if ("frequency" in form):
        fargs['frequency'] = float(form['frequency'].value)

    # The minimum frequency spacing between atmospheric corrections (MHz).
    # Default 50.
    if ("per_freq" in form):
        fargs['per_freq'] = float(form['per_freq'].value)
    else:
        fargs['per_freq'] = 50.0

    # The lowest hour angle observed (decimal hours).
    if ("ha_min" in form):
        fargs['ha_min'] = float(form['ha_min'].value)

    # The highest hour angle observed (decimal hours).
    if ("ha_max" in form):
        fargs['ha_max'] = float(form['ha_max'].value)

    # The middle hour angle observed (decimal hours).
    # Default 0.
    if ("ha_middle" in form):
        fargs['ha_middle'] = float(form['ha_middle'].value)
    else:
        fargs['ha_middle'] = 0.0

    # The name of the PNG file to output the RMS v frequency spectrum to
    # (no extension).
    # Default is a random string appended to "rms_spectrum_".
    fargs['output'] = "rms_plots/rms_spectrum"
    for i in xrange(0, 7):
        fargs['output'] += ("_%d" % random.randint(0, 99))
    fargs['output'] += ".png"

    # The number of calculations of atmosphere made per hour.
    # Default 5.
    if ("per_ha" in form):
        fargs['per_ha'] = float(form['per_ha'].value)
    else:
        fargs['per_ha'] = 5.0

    # Do not output progress messages.
    # Default true (because we run on the server).
    fargs['quiet'] = True

    # Use this rest frequency to calculate the velocity parameters (GHz).
    if ("restfreq" in form):
        fargs['restfreq'] = float(form['restfreq'].value)

    # Flag known RFI-affected regions of the continuum spectrum.
    fargs['rfi'] = ("rfi" in form)

    # The number of continuum spectral channels to bin together in the
    # output.
    # Default 1.
    if ("smoothing" in form):
        fargs['smoothing'] = int(form['smoothing'].value)
    else:
        fargs['smoothing'] = 1

    # The conditions to assume for weather dependence
    # [ "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
    #   "JUL", "AUG", "SEP", "OCT", "NOV", "DEC",
    #   "SUMMER", "AUTUMN", "WINTER", "SPRING",
    #   "APRS", "OCTS", "ANNUAL" ]
    # Default "ANNUAL".
    if ("season" in form):
        fargs['season'] = form['season'].value
    else:
        fargs['season'] = "ANNUAL"

    # The amount of on-source integration time (min).
    # Default 720.
    if ("integration" in form):
        fargs['integration'] = float(form['integration'].value)
    else:
        fargs['integration'] = 720.0

    # The target sensitivity to reach.
    # Default 0.
    if ("target" in form):
        fargs['target'] = float(form['target'].value)
    else:
        fargs['target'] = 0.0

    # The target sensitivity is for the continuum image.
    fargs['target_continuum'] = ("target_continuum" in form)

    # The target sensitivity is for the spectral RMS in the continuum band.
    fargs['target_spectral'] = ("target_spectral" in form)

    # The target sensitivity is for the spectral RMS in a typical zoom band.
    fargs['target_zoom'] = ("target_zoom" in form)

    # The target sensitivity is for the spectral RMS in the specific zoom band.
    fargs['target_specific_zoom'] = ("target_specific_zoom" in form)

    # The target sensitivity is specified as a flux density in mJy.
    fargs['target_flux_density'] = ("target_flux_density" in form)

    # The target sensitivity is specified as a brightness temperature in mK.
    fargs['target_brightness_temperature'] = ("target_brightness_temperature" in form)

    # The target sensitivity is to be obtained in the best weather conditions.
    fargs['target_best'] = ("target_best" in form)
    
    # The target sensitivity is to be obtained in typical weather conditions.
    fargs['target_typical'] = ("target_typical" in form)

    # The target sensitivity is to be obtained in the worst weather conditions.
    fargs['target_worst'] = ("target_worst" in form)

    # The image weighting scheme [ "R2", "R1", "R0", "R-1", "R-2" ].
    # Default "R2".
    if ("weighting" in form):
        fargs['weighting'] = form['weighting'].value
    else:
        fargs['weighting'] = "R2"

    # The number of concatenated zoom bands to use for the specific zoom.
    # Default 1.
    if ("zoom_width" in form):
        fargs['zoom_width'] = int(form['zoom_width'].value)
    else:
        fargs['zoom_width'] = 1

    # The number of zoom spectral channels to bin together in the output.
    # Default 1.
    if ("zoom_smoothing" in form):
        fargs['zoom_smoothing'] = int(form['zoom_smoothing'].value)
    else:
        fargs['zoom_smoothing'] = 1

    # A specific zoom frequency to calculate parameters for.
    if ("zoomfreq" in form):
        fargs['zoomfreq'] = float(form['zoomfreq'].value)

    # The number of edge channels to flag in the zoom band.
    # Default 0.
    if ("zoom_edge" in form):
        fargs['zoom_edge'] = int(form['zoom_edge'].value)
    else:
        fargs['zoom_edge'] = 0

    fargs['human_readable'] = False

    # Start the JSON output.
    print "Content-type: text/json"
    print

    # Make the args object.
    args = Struct(**fargs)
    
    # Call the main routine.
    sens.main(args)
