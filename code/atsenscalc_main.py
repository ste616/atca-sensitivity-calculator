######################################################################
# The ATCA Sensitivity Calculator
# Common execution handlers.
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

import math
import sys
import simplejson as json
import numpy as np
import atsenscalc_routines as sens

def checkArguments(args):
    cargs = vars(args)
    # Check the frequency exists and is within a known band.
    if 'frequency' in cargs:
        b = sens.frequencyBand(int(args.frequency))
        if b is None:
            raise sens.CalcError("Frequency is not in an ATCA band.")

    # Check that any specified zoom band is within the frequency range.
    if ('zoomfreq' in cargs and args.zoomfreq is not None):
        if (args.zoomfreq < (args.frequency - (sens.continuumBandwidth / 2)) or
            args.zoomfreq > (args.frequency + (sens.continuumBandwidth / 2))):
            raise sens.CalcError("Zoom frequency too far from continuum central frequency.")

    # Check that the elevation limit is reasonable.
    if (args.ellimit < 12 or args.ellimit >= 90):
        raise sens.CalcError("Elevation limit out of range.")

    # Check that the hour angle limit is reasonable.
    if (args.halimit <= 0 or args.halimit > 12):
        raise sens.CalcError("Hour-angle limit out of range.")
    # And the middle hour angle.
    if (abs(args.ha_middle) > 12):
        raise sens.CalcError("Middle hour-angle out of range.")
    # And thus the derived maximum and minimum hour angles.
    hourAngle_min = args.ha_middle - abs(args.halimit)
    hourAngle_max = args.ha_middle + abs(args.halimit)
    # Or the actual specified minimum and maximum hour angles.
    if (('ha_min' in cargs and args.ha_min is not None) and
        ('ha_max' in cargs and args.ha_max is not None)):
        hourAngle_min = args.ha_min
        hourAngle_max = args.ha_max
    if (abs(hourAngle_min) > 12 or abs(hourAngle_max) > 12):
        raise sens.CalcError("Interpreted hour-angle maximum/minimum out of range.")

    # Check that the declination is reasonable.
    if (args.dec < -90 or args.dec > (90 - 30.313 - args.ellimit)):
        raise sens.CalcError("Declination not observable with specified elevation limit.")

    # Check we have a positive integration time.
    if (args.integration <= 0):
        raise sens.CalcError("Integration time must be greater than 0 minutes.")

    # Check the number of integrations per hour angle is reasonable.
    if (args.per_ha <= 0):
        raise sens.CalcError("Number of integrations per hour angle is invalid.")

    # Check for a specified rest frequency.
    if ('restfreq' in cargs and args.restfreq is not None):
        restfreq = args.restfreq * 1000.0 # Conversion from GHz to MHz.
    elif ('zoomfreq' in cargs and args.zoomfreq is not None):
        # Use the centre frequency of the specified zoom band.
        restfreq = args.zoomfreq
    else:
        # Use the centre frequency of the continuum band.
        restfreq = args.frequency

    # Check that the number of zooms requested is between 1 and 16 inclusive.
    if (args.zoom_width < 1 or args.zoom_width > 16):
        raise sens.CalcError("Specified zoom width is out of range.")

    # Check for consistency with time calculation mode.
    # First check how many target bands were specified.
    ntargetband = 0
    if (args.target_continuum):
        ntargetband += 1
    if (args.target_spectral):
        ntargetband += 1
    if (args.target_zoom):
        ntargetband += 1
    if (args.target_specific_zoom):
        ntargetband += 1
    # Check how many target modes were specified.
    ntargetmode = 0
    if (args.target_flux_density):
        ntargetmode += 1
    if (args.target_brightness_temperature):
        ntargetmode += 1
    # Check how many target conditions were specified.
    ntargetcondition = 0
    if (args.target_best):
        ntargetcondition += 1
    if (args.target_typical):
        ntargetcondition += 1
    if (args.target_worst):
        ntargetcondition += 1

    # Do we operation in sensitivity target mode?
    if (args.calculate_time):
        # Yes, so we check we have a clear picture of how to do the calculation.
        if ((ntargetband != 1) or (ntargetmode != 1) or (ntargetcondition != 1)):
            if (ntargetband != 1):
                raise sens.CalcError("Time calculation undefined: no single target band selected.")
            elif (ntargetmode != 1):
                raise sens.CalcError("Time calculation undefined: no single target mode selected.")
            elif (ntargetcondition != 1):
                raise sens.CalcError("Time calculation undefined: no single target condition selected.")
        # Check that we actually have a target value.
        if (args.target <= 0.0):
            raise sens.CalcError("Target sensitivity not specified.")

    # Return the interpreted values we made.
    return { 'hourAngle_min': hourAngle_min, 'hourAngle_max': hourAngle_max,
             'restfreq': restfreq }

def thingToString(t):
    if (type(t) is str):
        return (t)
    elif (type(t) is list):
        narr = []
        for i in xrange(0, len(t)):
            narr.append(thingToString(t[i]))
        return (', '.join(narr))
    elif (type(t) is int):
        return ("%d" % t)
    elif (type(t) is float or type(t) is np.float64):
        return ("%f" % t)

def humanOutputDict(d, description, units, l):
    for p in d:
        if (p != "description" and p != "units"):
            if (type(d[p]) is dict):
                print "%s%s:" % ((" " * l), p)
                humanOutputDict(d[p], description, units, (l + 1))
            else:
                od = p
                if (p in description):
                    od = description[p]
                ou = ""
                if (p in units):
                    ou = units[p]
                ov = thingToString(d[p])
                print "%s %s = %s %s" % ((" " * l), od, ov, ou)

def main(args):
    ####################################################################################################
    # Do some argument checking first.
    try:
        argsInterpreted = checkArguments(args)
    except sens.CalcError:
        _, c, _ = sys.exc_info()
        if (args.human_readable):
            print "FATAL: ", c.value
        else:
            print '{ "error": "%s" }' % c.value
        sys.exit(-1)

    # The number of antenna and baselines.
    nant = 5
    if (args.ca06):
        nant = 6
    nbaselines = nant * (nant - 1) / 2

    cargs = vars(args)
    # Are we making calculations for a specific zoom band?
    specificZoomCalc = False
    if ('zoomfreq' in cargs and args.zoomfreq is not None):
        specificZoomCalc = True

    # Identify the constraints on the observed hour angles, by comparing them to the
    # specified elevation limit.
    sinel = math.sin(math.radians(args.ellimit))
    sind = math.sin(math.radians(args.dec))
    cosd = math.cos(math.radians(args.dec))

    hourAngle_min = argsInterpreted['hourAngle_min']
    hourAngle_max = argsInterpreted['hourAngle_max']

    coshaAtElLimit = sinel / (cosd * sens.cosl) - (sind * sens.sinl) / (cosd * sens.cosl)
    if (abs(coshaAtElLimit) <= 1):
        haAtElLimit = math.degrees(math.acos(coshaAtElLimit)) # in degrees
        hahAtElLimit = haAtElLimit / 15.0 # in hours
        if (hahAtElLimit < abs(hourAngle_min)):
            hourAngle_min = -1 * hahAtElLimit
        if (hahAtElLimit < abs(hourAngle_max)):
            hourAngle_max = hahAtElLimit

    # Get the image weighting factors.
    try:
        imageWeights = sens.weightingFactor(args.weighting, args.configuration, args.ca06)
    except sens.CalcError:
        _, c, _ = sys.exc_info()
        if (args.human_readable):
            print "FATAL: ", c.value
        else:
            print '{ "error": "%s" }' % c.value
        sys.exit(-1)

    # Get the lengths of the baselines and determine the maximum baseline length.
    try:
        baselineLengths = sens.maximumBaseline(args.configuration)
    except sens.CalcError:
        _, c, _ = sys.exc_info()
        if (args.human_readable):
            print "FATAL: ", c.value
        else:
            print '{ "error": "%s" }' % c.value
        sys.exit(-1)
    maxBaselineLength = baselineLengths['track']
    if (args.ca06):
        maxBaselineLength = baselineLengths['ca06']

    # All parameters are valid.
    if (not args.quiet):
        print "MESSAGE: Starting calculator."
    workArea = {}
    #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\



    ####################################################################################################
    # Prepare the output, and begin by listing the parameters we were given.
    output = {
        'parameters': {},
        'continuum': {},
        'zoom': {},
        'specific_zoom': {},
        'sensitivities': {},
        'description': {},
        'source_imaging': {},
        'units': {} }
    # The array configuration.
    sens.addToOutput(output, 'parameters', 'configuration', args.configuration, "Configuration", None)
    # The central frequency of the continuum band.
    sens.addToOutput(output, 'parameters', 'central_frequency', args.frequency, "Central Frequency", "MHz")
    # The number of antenna in the array.
    sens.addToOutput(output, 'parameters', 'n_antenna', nant, "Antenna Included", None)
    # The number of baselines formed by those antenna.
    sens.addToOutput(output, 'parameters', 'n_baselines', nbaselines, "Baselines formed", None)
    # Whether the array is hybrid, or entirely East-West.
    sens.addToOutput(output, 'parameters', 'hybrid', False, "Hybrid Array", None)
    if (args.configuration in [ 'h214', 'H214', 'h168', 'H168', 'h75', 'H75' ]):
        output['parameters']['hybrid'] = True
    # The rest frequency of the spectral line of interest.
    orf = "%.3f" % argsInterpreted['restfreq']
    sens.addToOutput(output, 'parameters', 'reference_rest_frequency', orf,
                     "Reference Rest Frequency", "MHz")

    # Source imaging parameters.
    # The declination of the source of interest.
    sens.addToOutput(output, 'source_imaging', 'source_declination', args.dec, "Source Declination", "degrees")
    # The uv weighting scheme to use during imaging.
    sens.addToOutput(output, 'source_imaging', 'weighting_scheme', args.weighting,
                     "Weighting Scheme", None)
    # And the weighting factors associated with that weighting scheme.
    # The RMS noise level weighting factor, where the factor = 1 for natural weighting.
    sens.addToOutput(output, 'source_imaging', 'weighting_factor', imageWeights['avg'],
                     "RMS noise weighting factor", None)
    # The synthesised beam size weighting factor.
    sens.addToOutput(output, 'source_imaging', 'beam_weighting_factor', imageWeights['beam'],
                     "Synthesised beam weighting factor", None)
    # The maximum baseline length for imaging.
    mbl = "%.0f" % (math.sqrt(maxBaselineLength['dX'] ** 2 + maxBaselineLength['dY'] ** 2 +
                              maxBaselineLength['dZ'] ** 2))
    sens.addToOutput(output, 'source_imaging', 'maximum_baseline_length', mbl,
                     "Maximum Baseline Length", "m")
    #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\



    ####################################################################################################
    # Calculate the frequency resolutions and put that in the output.
    workArea['resolutions'] = sens.channelResolution(args.corrconfig)
    # These resolutions are the native resolutions made by the correlator, unsmoothed.
    # In the continuum band.
    sens.addToOutput(output, 'continuum', 'correlator_channel_bandwidth', workArea['resolutions']['continuum'],
                     "Correlator Channel Bandwidth", "MHz")
    # For a general zoom.
    sens.addToOutput(output, 'zoom', 'correlator_channel_bandwidth', workArea['resolutions']['zoom'],
                     "Correlator Channel Bandwidth", "MHz")
    if (specificZoomCalc):
        # For the specific zoom (which will be the same as the general zoom).
        sens.addToOutput(output, 'specific_zoom', 'correlator_channel_bandwidth', workArea['resolutions']['zoom'],
                         "Correlator Channel Bandwidth", "MHz")
    #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\



    ####################################################################################################
    # Make the continuum spectrum templates.
    if (not args.quiet):
        print "MESSAGE: Generating template spectra..."
    workArea['continuum'] = sens.makeTemplate(args.frequency, sens.continuumBandwidth,
                                              workArea['resolutions']['continuum'])
    workArea['alternate'] = sens.makeTemplate((args.frequency - workArea['resolutions']['continuum'] / 2),
                                              sens.continuumBandwidth, workArea['resolutions']['continuum'])
    # Get the lowest and highest frequencies that we will need to read from the files.
    lowGlobalFreq = (workArea['alternate']['centreFrequency'][0] -
                     (workArea['resolutions']['continuum'] / 2.0))
    highGlobalFreq = (workArea['continuum']['centreFrequency'][-1] +
                      (workArea['resolutions']['continuum'] / 2.0))
    # Read the Tsys between those frequencies into memory if required.
    b = sens.frequencyBand(args.frequency)
    try:
        cacheTsys = sens.readTsys(sens.frequencyBands[b]['tsys'], lowGlobalFreq, highGlobalFreq)
    except sens.CalcError:
        _, c, _ = sys.exc_info()
        if (args.human_readable):
            print "FATAL: ", c.value
        else:
            print '{ "error": "%s" }' % c.value
        sys.exit(-1)
    # Use the raw Tsys to fill in the required templates.
    sens.templateFill(cacheTsys, workArea['continuum'])
    sens.templateFill(cacheTsys, workArea['alternate'])
    # Make the specific zoom template here too.
    if (specificZoomCalc):
        # Determine which channel is closest in centre frequency to the nominated
        # specific zoom frequency.
        closestCentreFreq = 0.0
        closestCentreOffs = 3000.0
        for i in xrange(0, len(workArea['continuum']['centreFrequency'])):
            offs = abs(workArea['continuum']['centreFrequency'][i] - args.zoomfreq)
            if (offs < closestCentreOffs):
                closestCentreFreq = workArea['continuum']['centreFrequency'][i]
                closestCentreOffs = offs
        for i in xrange(0, len(workArea['alternate']['centreFrequency'])):
            offs = abs(workArea['alternate']['centreFrequency'][i] - args.zoomfreq)
            if (offs < closestCentreOffs):
                closestCentreFreq = workArea['alternate']['centreFrequency'][i]
                closestCentreOffs = offs
        # Compute how the bandwidth is distributed around the centre frequency.
        bandwidthAbove = (0.125 * (2.0 * float(args.zoom_width) + (-1.0) ** float(args.zoom_width) + 3.0) *
                          workArea['resolutions']['continuum'])
        bandwidthBelow = (0.125 * (2.0 * float(args.zoom_width) - (-1.0) ** float(args.zoom_width) + 1.0) *
                          workArea['resolutions']['continuum'])
        szBandwidths = [ bandwidthBelow, bandwidthAbove ]
        workArea['specificZoom'] = sens.makeTemplate(closestCentreFreq, szBandwidths,
                                                workArea['resolutions']['zoom'])
        # Fill in the template from the continuum template.
        sens.templateFill(workArea['continuum'], workArea['specificZoom'])
        
    # Put the frequency ranges of the templates in the output.
    # The continuum ranges.
    lowestFreq = (workArea['continuum']['centreFrequency'][args.edge] - 
                  (workArea['resolutions']['continuum'] / 2))
    highestFreq = (workArea['continuum']['centreFrequency'][-(args.edge + 1)] +
                   (workArea['resolutions']['continuum'] / 2))
    sens.addToOutput(output, 'continuum', 'frequency_range', [ lowestFreq, highestFreq ],
                     "Continuum Band Frequency Range", "MHz")
    sens.addToOutput(output, 'zoom', 'n_zooms', args.zoom_width,
                     "Number of concatenated zoom channels", "channels")
    sens.addToOutput(output, 'parameters', 'zoom_frequency', args.frequency, "Zoom Frequency", "MHz")
    if (specificZoomCalc):
        sens.addToOutput(output, 'parameters', 'zoom_frequency', closestCentreFreq, "Specific Zoom Frequency", "MHz")
        # Get the lowest and highest frequencies.
        szoomLowestFreq = (workArea['specificZoom']['centreFrequency'][args.zoom_edge] -
                           (workArea['resolutions']['zoom'] / 2))
        szoomHighestFreq = (workArea['specificZoom']['centreFrequency'][-(args.zoom_edge + 1)] +
                            (workArea['resolutions']['zoom'] / 2))
        sens.addToOutput(output, 'specific_zoom', 'frequency_range', [ szoomLowestFreq, szoomHighestFreq ],
                         "Specific Zoom Frequency Range", "MHz")
        # The number of zooms used.
        sens.addToOutput(output, 'specific_zoom', 'n_zooms', args.zoom_width,
                         "Number of concatenated zoom channels", "channels")
    #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\



    ####################################################################################################
    # Make antenna efficiency templates.
    # For the continuum bands.
    efficiencyMasterTemplate = sens.templateEfficiency()
    workArea['continuum-efficiency'] = sens.makeTemplate(args.frequency, sens.continuumBandwidth,
                                                         workArea['resolutions']['continuum'])
    workArea['alternate-efficiency'] = sens.makeTemplate((args.frequency - workArea['resolutions']['continuum'] / 2),
                                                         sens.continuumBandwidth, workArea['resolutions']['continuum'])
    sens.templateFill(efficiencyMasterTemplate, workArea['continuum-efficiency'])
    sens.templateFill(efficiencyMasterTemplate, workArea['alternate-efficiency'])
    if (specificZoomCalc):
        # For the specific zoom band.
        workArea['specificZoom-efficiency'] = sens.makeTemplate(closestCentreFreq, szBandwidths,
                                                                workArea['resolutions']['zoom'])
        sens.templateFill(workArea['continuum-efficiency'], workArea['specificZoom-efficiency'])

    # Put the average computed efficiencies in the output.
    averageEfficiency = "%.1f" % (sens.averageTemplate(workArea['continuum-efficiency']) * 100.0)
    sens.addToOutput(output, 'parameters', 'antenna_efficiency', float(averageEfficiency),
                     "Antenna Efficiency", "%")
    #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\



    ####################################################################################################
    # Do template flagging.
    if (not args.quiet):
        print "MESSAGE: Flagging..."
    sens.flagTemplate(workArea['continuum'], 'continuum', args.corrconfig, 0)
    sens.flagTemplate(workArea['continuum'], 'edge', args.corrconfig, args.edge)
    if (specificZoomCalc):
        sens.flagTemplate(workArea['specificZoom'], 'edge', args.corrconfig, args.zoom_edge)
    if (args.birdies):
        sens.flagTemplate(workArea['continuum'], 'birdies', args.corrconfig, 0)
    if (args.rfi):
        sens.flagTemplate(workArea['continuum'], 'rfi', args.corrconfig, 0)
    #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\



    ####################################################################################################
    # Do any bin smoothing now. We need to smooth the system temperature and efficiency templates.
    # The continuum frequency resolution after smoothing.
    contSmoothRes = workArea['resolutions']['continuum'] * float(args.smoothing)
    sens.addToOutput(output, 'source_imaging', 'smoothing_window', args.smoothing,
                     "Smoothing Window", "channels")
    # Check that we will end up with at least 2 channels, otherwise we die.
    if ((sens.continuumBandwidth / contSmoothRes) < 2):
        if (args.human_readable):
            print "FATAL: Smoothing factor too large."
        else:
            print '{ "error": "Smoothing factor too large." }'
        sys.exit(-1)
    # Make the smoothed templates and fill them from the unsmoothed templates.
    workArea['continuum-smooth'] = sens.makeTemplate(args.frequency, sens.continuumBandwidth, contSmoothRes)
    sens.templateFill(workArea['continuum'], workArea['continuum-smooth'])
    workArea['continuum-efficiency-smooth'] = sens.makeTemplate(args.frequency, sens.continuumBandwidth, contSmoothRes)
    sens.templateFill(workArea['continuum-efficiency'], workArea['continuum-efficiency-smooth'])
    sens.addToOutput(output, 'continuum', 'channel_bandwidth', contSmoothRes,
                     "Channel Bandwidth", "MHz")

    # The zooms are smoothed by a different argument.
    # The "general" zoom frequency resolution after smoothing.
    zoomSmoothRes = workArea['resolutions']['zoom'] * float(args.zoom_smoothing)
    sens.addToOutput(output, 'source_imaging', 'zoom_smoothing_window', args.zoom_smoothing,
                     "Zoom Smoothing Window", "channels")
    # The channel bandwidth goes to integer Hz.
    chbw = "%.6f" % zoomSmoothRes
    sens.addToOutput(output, 'zoom', 'channel_bandwidth', chbw,
                     "Channel Bandwidth", "MHz")
    if (specificZoomCalc):
        # The specific zoom will have the exact same frequency resolution.
        sens.addToOutput(output, 'specific_zoom', 'channel_bandwidth', chbw,
                         "Channel Bandwidth", "MHz")
    # We don't want to smooth too much in the zooms either, so we check for that now.
    if ((workArea['resolutions']['continuum'] / zoomSmoothRes) < 2):
        if (args.human_readable):
            print "FATAL: Zoom smoothing factor too large."
        else:
            print '{ "error": "Zoom smoothing factor too large." }'
        sys.exit(-1)

    if (specificZoomCalc):
        # Make the specific zoom smoothed template.
        workArea['specificZoom-smooth'] = sens.makeTemplate(closestCentreFreq, szBandwidths,
                                                            zoomSmoothRes)
        sens.templateFill(workArea['specificZoom'], workArea['specificZoom-smooth'])
        workArea['specificZoom-efficiency-smooth'] = sens.makeTemplate(closestCentreFreq, szBandwidths,
                                                                       zoomSmoothRes)
        sens.templateFill(workArea['specificZoom-efficiency'], workArea['specificZoom-efficiency-smooth'])
    #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    


    ####################################################################################################
    # Calculate the properties of the primary beam.
    # Primary beam field of view, in arcminutes, for the continuum central frequency.
    pbfwhm = sens.primaryBeamSize(args.frequency, sens.antennaDiameter)
    sens.addToOutput(output, 'source_imaging', 'field_of_view', pbfwhm,
                "Field of View (primary beam FWHM)", "arcmin")
    # And the low/high frequencies of the continuum band.
    pbfwhml = sens.primaryBeamSize(workArea['continuum']['centreFrequency'][0], sens.antennaDiameter)
    pbfwhmh = sens.primaryBeamSize(workArea['continuum']['centreFrequency'][-1], sens.antennaDiameter)
    sens.addToOutput(output, 'source_imaging', 'field_of_view_range', [ pbfwhml, pbfwhmh ],
                "Field of View Range (primary beam FWHM)", "arcmin")
    if (specificZoomCalc):
        # And at the specific zoom frequency.
        zpbfwhm = sens.primaryBeamSize(args.zoomfreq, sens.antennaDiameter)
        sens.addToOutput(output, 'source_imaging', 'field_of_view_zoom', zpbfwhm,
                    "Specific Zoom Band Field of View (primary beam FWHM)", "arcmin")
    #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\



    ####################################################################################################
    # Calculate the properties of the synthesised beam.
    # Synthesised beam for the continuum central frequency.
    try:
        synthBeamContinuum = sens.synthesisedBeamSize(args.frequency, maxBaselineLength, args.dec, hourAngle_min,
                                                      hourAngle_max, imageWeights['beam'])
    except ZeroDivisionError:
        if (args.human_readable):
            print "FATAL: Cannot observe a declination 0 source with an EW array."
        else:
            print '{ "error": "Cannot observe a declination 0 source with an EW array." }'
        sys.exit(-1)
    sens.addToOutput(output, 'source_imaging', 'synthesised_beam_size', synthBeamContinuum,
                "Synthesised Beam Size (FWHM)", "arcsec")

    # The sizes at the high and low frequencies of the continuum band. We no longer check for
    # the returning ZeroDivisionError because if it was going to happen, it would have already happened.
    synthBeamLowFreq = sens.synthesisedBeamSize(lowestFreq, maxBaselineLength, args.dec, hourAngle_min,
                                           hourAngle_max, imageWeights['beam'])
    synthBeamHighFreq = sens.synthesisedBeamSize(highestFreq, maxBaselineLength, args.dec, hourAngle_min,
                                            hourAngle_max, imageWeights['beam'])
    sens.addToOutput(output, 'source_imaging', 'synthesised_beam_size_range', 
                [ synthBeamLowFreq, synthBeamHighFreq ],
                "Synthesised Beam Size Range (FWHM)", "arcsec")
    if (specificZoomCalc):
        # The synthesised beam for the frequency the user wanted in the specific zoom band.
        synthBeamZoom = sens.synthesisedBeamSize(args.zoomfreq, maxBaselineLength, args.dec, hourAngle_min,
                                            hourAngle_max, imageWeights['beam'])
        sens.addToOutput(output, 'source_imaging', 'synthesised_beam_size_zoom', synthBeamZoom,
                    "Specific Zoom Band Synthesised Beam Size (FWHM)", "arcsec")
    #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\



    ####################################################################################################
    # Work out the velocity resolutions and ranges. Because the channels flagged at the
    # edge shouldn't be considered as usable bandwidth, we don't consider them as usable
    # for velocity range.
    # The usable frequency bandwidth over the continuum band.
    contVelBandwidth = highestFreq - lowestFreq
    # We calculate the velocity span corresponding to that amount of bandwidth with the
    # actual lower frequency.
    sens.addToOutput(output, 'continuum', 'spectral_bandwidth',
                     sens.bandwidthToVelocity(workArea['continuum']['centreFrequency'][args.edge],
                                              contVelBandwidth, argsInterpreted['restfreq']),
                     "Spectral Bandwidth", "km/s")
    # The velocity width of a channel is dependant on its frequency, so we can't give
    # an exact figure for every channel here; we just divide the continuum range by the
    # number of channels here, excluding the edge channels.
    contRes = (output['continuum']['spectral_bandwidth'] / 
               float(len(workArea['continuum']['centreFrequency']) - 2 * args.edge))
    # We now compensate for continuum band smoothing.
    chanRes = float("%.3f" % (contRes * float(args.smoothing)))
    sens.addToOutput(output, 'continuum', 'spectral_channel_resolution', chanRes,
                     "Spectral Channel Resolution", "km/s")

    # The velocity width of a "general" zoom band needs to be calculated in the same way
    # since the user may not want the edge channels there.
    # The usable frequency bandwidth over a "general" zoom band.
    nZoomFactor = (float(args.zoom_width) + 1.0) / 2.0
    zoomVelBandwidth = (nZoomFactor * workArea['resolutions']['continuum'] - 
                        (2.0 * float(args.zoom_edge) * workArea['resolutions']['zoom']))
    sens.addToOutput(output, 'zoom', 'effective_bandwidth', zoomVelBandwidth, 
                     "Effective Bandwidth", "MHz")
    # But we can't actually calculate a "general" velocity width that way since it is again
    # frequency dependant. So we just divide up the continuum velocity resolution.
    zoomRes = contRes / float(sens.nZoomChannels)
    # And compensate for zoom band smoothing.
    zoomChanRes = float("%.3f" % (zoomRes * float(args.zoom_smoothing)))
    sens.addToOutput(output, 'zoom', 'spectral_channel_resolution', zoomChanRes, "Spectral Channel Resolution",
                     "km/s")
    # The number of channels in the zoom, excluding the edge flagged channels.
    nZoomVelChans = int(zoomVelBandwidth / workArea['resolutions']['zoom'])
    # But we output only the number of smoothed channels.
    sens.addToOutput(output, 'zoom', 'n_channels', (nZoomVelChans / args.zoom_smoothing),
                     "# Channels", None)
    # The zoom velocity width is then just the velocity resolution of each channel multiplied
    # by the number of non-edge channels.
    zoomSpecBandwidth = zoomRes * float(nZoomVelChans)
    zsb = "%.3f" % zoomSpecBandwidth
    sens.addToOutput(output, 'zoom', 'spectral_bandwidth', zsb, "Spectral Bandwidth", "km/s")

    if (specificZoomCalc):
        # We can actually calculate real velocity values for the specific zoom band, so we
        # do it basically the same as for the continuum band.
        # The frequency bandwidth of the specific zoom takes into account how many zoom
        # channels that the user will consolidate, and the number of channels flagged at the
        # edge.
        szoomVelBandwidth = szoomHighestFreq - szoomLowestFreq
        szvb = ".3f" % szoomVelBandwidth
        sens.addToOutput(output, 'specific_zoom', 'effective_bandwidth', szoomVelBandwidth, 
                         "Effective Bandwidth", "MHz")
        # The velocity span corresponding to that amount of bandwidth is calculated with
        # respect to the lower frequency of the zoom.
        sens.addToOutput(output, 'specific_zoom', 'spectral_bandwidth',
                         sens.bandwidthToVelocity(szoomLowestFreq, szoomVelBandwidth,
                                                  argsInterpreted['restfreq']),
                         "Spectral Bandwidth", "km/s")
        # We calculate the number of channels across the consolidated zoom.
        nszoomChans = int(szoomVelBandwidth / workArea['resolutions']['zoom'])
        # But we output only the number of smoothed channels.
        sens.addToOutput(output, 'specific_zoom', 'n_channels', (nszoomChans / args.zoom_smoothing),
                         "# Channels", None)

        # The velocity resolution is just the velocity span divided by the number of channels,
        # excluding those flagged at the edge.
        szoomRes = (output['specific_zoom']['spectral_bandwidth'] / float(nszoomChans))
        # We compensate for zoom smoothing.
        szoomChanRes = float("%.3f" % (szoomRes * float(args.zoom_smoothing)))
        sens.addToOutput(output, 'specific_zoom', 'spectral_channel_resolution', szoomChanRes,
                         "Spectral Channel Resolution", "km/s")
    #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\



    ####################################################################################################
    # Get the atmospheric parameters for the zenith and store that in a template.
    if (not args.quiet):
        print "MESSAGE: Calculating weather effects..."

    # The weather conditions that we will use for computing the atmosphere later.
    weatherConditions = {
        'JAN': { 'best': { 'temperature': 32.7, 'pressure': 986.8, 'humidity': 27.5 },
                 'typical': { 'temperature': 30.6, 'pressure': 989.8, 'humidity': 50.5 },
                 'worst': { 'temperature': 26.3, 'pressure': 1001.9, 'humidity': 91.0 } }, 
        'FEB': { 'best': { 'temperature': 29.6, 'pressure': 987.2, 'humidity': 36.0 },
                 'typical': { 'temperature': 24.2, 'pressure': 989.6, 'humidity': 65.0 },
                 'worst': { 'temperature': 23.7, 'pressure': 990.4, 'humidity': 86.0 } },
        'MAR': { 'best': { 'temperature': 27.4, 'pressure': 989.7, 'humidity': 33.0 },
                 'typical': { 'temperature': 18.9, 'pressure': 995.5, 'humidity': 82.0 },
                 'worst': { 'temperature': 28.2, 'pressure': 988.0, 'humidity': 69.7 } },
        'APR': { 'best': { 'temperature': 9.5, 'pressure': 1011.7, 'humidity': 76.0 },
                 'typical': { 'temperature': 16.8, 'pressure': 1013.4, 'humidity': 73.0 },
                 'worst': { 'temperature': 19.7, 'pressure': 1001.6, 'humidity': 85.0 } },
        'MAY': { 'best': { 'temperature': 19.6, 'pressure': 1008.0, 'humidity': 31.0 },
                 'typical': { 'temperature': 9.7, 'pressure': 1009.7, 'humidity': 86.0 },
                 'worst': { 'temperature': 18.7, 'pressure': 1012.3, 'humidity': 78.0 } },
        'JUN': { 'best': { 'temperature': -1.6, 'pressure': 1016.9, 'humidity': 95.0 },
                 'typical': { 'temperature': 8.1, 'pressure': 1002.7, 'humidity': 95.0 },
                 'worst': { 'temperature': 15.0, 'pressure': 997.7, 'humidity': 101.1 } },
        'JUL': { 'best': { 'temperature': 1.9, 'pressure': 1019.0, 'humidity': 91.0 },
                 'typical': { 'temperature': 18.8, 'pressure': 999.4, 'humidity': 50.5 },
                 'worst': { 'temperature': 15.6, 'pressure': 1004.2, 'humidity': 100.0 } },
        'AUG': { 'best': { 'temperature': 3.6, 'pressure': 1017.2, 'humidity': 73.0 },
                 'typical': { 'temperature': 8.2, 'pressure': 1010.5, 'humidity': 87.0 },
                 'worst': { 'temperature': 16.6, 'pressure': 1012.4, 'humidity': 93.0 } },
        'SEP': { 'best': { 'temperature': 19.9, 'pressure': 989.9, 'humidity': 27.0 },
                 'typical': { 'temperature': 15.4, 'pressure': 993.5, 'humidity': 61.0 },
                 'worst': { 'temperature': 20.3, 'pressure': 993.6, 'humidity': 66.0 } },
        'OCT': { 'best': { 'temperature': 26.6, 'pressure': 986.6, 'humidity': 22.0 },
                 'typical': { 'temperature': 28.6, 'pressure': 986.5, 'humidity': 33.0 },
                 'worst': { 'temperature': 25.8, 'pressure': 996.6, 'humidity': 57.0 } },
        'NOV': { 'best': { 'temperature': 32.5, 'pressure': 986.7, 'humidity': 19.7 },
                 'typical': { 'temperature': 22.1, 'pressure': 990.2, 'humidity': 58.0 },
                 'worst': { 'temperature': 24.7, 'pressure': 989.5, 'humidity': 71.9 } },
        'DEC': { 'best': { 'temperature': 29.5, 'pressure': 986.8, 'humidity': 30.0 },
                 'typical': { 'temperature': 21.8, 'pressure': 987.0, 'humidity': 70.0 },
                 'worst': { 'temperature': 27.9, 'pressure': 984.5, 'humidity': 71.0 } },
        'SUMMER': { 'best': { 'temperature': 29.5, 'pressure': 986.8, 'humidity': 30.0 },
                    'typical': { 'temperature': 29.9, 'pressure': 989.1, 'humidity': 49.0 },
                    'worst': { 'temperature': 26.3, 'pressure': 1001.9, 'humidity': 91.0 } },
        'AUTUMN': { 'best': { 'temperature': 19.5, 'pressure': 1008.0, 'humidity': 31.0 },
                    'typical': { 'temperature': 23.6, 'pressure': 1016.5, 'humidity': 51.0 },
                    'worst': { 'temperature': 28.2, 'pressure': 988.0, 'humidity': 69.7 } },
        'WINTER': { 'best': { 'temperature': -1.6, 'pressure': 1016.9, 'humidity': 95.0 },
                    'typical': { 'temperature': 9.7, 'pressure': 1004.6, 'humidity': 83.0 },
                    'worst': { 'temperature': 15.6, 'pressure': 1004.2, 'humidity': 100.0 } },
        'SPRING': { 'best': { 'temperature': 19.9, 'pressure': 989.9, 'humidity': 27.0 },
                    'typical': { 'temperature': 14.9, 'pressure': 997.5, 'humidity': 68.7 },
                    'worst': { 'temperature': 24.7, 'pressure': 989.5, 'humidity': 71.9 } },
        'APRS': { 'best': { 'temperature': 19.9, 'pressure': 989.9, 'humidity': 27.0 },
                  'typical': { 'temperature': 12.7, 'pressure': 1011.1, 'humidity': 72.0 },
                  'worst': { 'temperature': 19.7, 'pressure': 1001.6, 'humidity': 85.0 } },
        'OCTS': { 'best': { 'temperature': 26.6, 'pressure': 986.6, 'humidity': 22.0 },
                  'typical': { 'temperature': 22.1, 'pressure': 988.7, 'humidity': 66.7 },
                  'worst': { 'temperature': 26.3, 'pressure': 1001.9, 'humidity': 91.0 } },
        'ANNUAL': { 'best': { 'temperature': 19.9, 'pressure': 989.9, 'humidity': 27.0 },
                    'typical': { 'temperature': 16.6, 'pressure': 1010.3, 'humidity': 57.5 },
                    'worst': { 'temperature': 26.3, 'pressure': 1001.9, 'humidity': 91.0 } }
        }

    # This is the frequency resolution of the atmospheric corrections.
    atmosRes = max(workArea['resolutions']['continuum'], args.per_freq)
    sens.addToOutput(output, 'parameters', 'atmosphere_frequency_resolution', atmosRes,
                     "Frequency resolution of atmospheric parameters", "MHz")
    # Include the weather parameters we use in the output.
    sens.addToOutput(output, 'parameters', 'atmospheric_season', args.season,
                     'Season for atmospheric calculations', None)
    sens.addToOutput(output, 'parameters', 'atmospheric_conditions', weatherConditions[args.season],
                     "Atmospheric conditions", None)
    # Add the units for temperature, pressure and humidity manually to the output.
    output['units']['temperature'] = "C"
    output['units']['humidity'] = "%"
    output['units']['pressure'] = "hPa"

    # Form the opacity and temperature templates for each of the weather conditions
    # (best, typical, worst).
    workArea['opacity'] = {}
    workArea['temperature'] = {}
    workArea['sz-opacity'] = {}
    workArea['sz-temperature'] = {}
    for condition in weatherConditions[args.season]:
        # Make the continuum templates first.
        tempOpacity = sens.makeTemplate(args.frequency, sens.continuumBandwidth, atmosRes)
        tempTemperature = sens.makeTemplate(args.frequency, sens.continuumBandwidth, atmosRes)
        workArea['opacity'][condition] = sens.makeTemplate(args.frequency, sens.continuumBandwidth,
                                                      workArea['resolutions']['continuum'])
        workArea['temperature'][condition] = sens.makeTemplate(args.frequency, sens.continuumBandwidth,
                                                          workArea['resolutions']['continuum'])
        sens.fillAtmosphereTemplate(tempOpacity, tempTemperature, 
                               (weatherConditions[args.season][condition]['temperature'] + 273.15),
                               (weatherConditions[args.season][condition]['pressure'] * 100.0),
                               (weatherConditions[args.season][condition]['humidity'] / 100.0))
        sens.templateFill(tempOpacity, workArea['opacity'][condition])
        sens.templateFill(tempTemperature, workArea['temperature'][condition])
        if (specificZoomCalc):
            # Make the specific zoom templates if we need to, and fill them from the already
            # computed templates for the continuum band.
            workArea['sz-opacity'][condition] = sens.makeTemplate(closestCentreFreq, szBandwidths,
                                                             workArea['resolutions']['zoom'])
            workArea['sz-temperature'][condition] = sens.makeTemplate(closestCentreFreq, szBandwidths,
                                                                 workArea['resolutions']['zoom'])
            sens.templateFill(workArea['opacity'][condition], workArea['sz-opacity'][condition])
            sens.templateFill(workArea['temperature'][condition], workArea['sz-temperature'][condition])
    #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\



    ####################################################################################################
    # Compute the sensitivites with all the information we just collected.
    if (not args.quiet):
        print "MESSAGE: Calculating sensitivities..."
    workArea['continuum-rms'] = {}
    workArea['continuum-smooth-rms'] = {}
    workArea['specificZoom-rms'] = {}
    computeBands = { 'continuum': 0, 'spectral': 0, 'zoom': 0 }
    workArea['rms'] = {
        'continuum': {},
        'spectral': {},
        'zoom': {},
        'specificZoom': {}
    }
    workArea['btrms'] = {
        'continuum': {},
        'spectral': {},
        'zoom': {},
        'specificZoom': {}
    }
    workArea['SEFD'] = {}

    # Sensitivities are computed for each of the different weather conditions we expect.
    sensitivityReached = False
    while (sensitivityReached == False):
        for condition in weatherConditions[args.season]:
            # The RMS noise in the smoothed continuum band, for each channel.
            workArea['continuum-smooth-rms'][condition] = sens.calculateRms(workArea['continuum-smooth'],
                                                                       workArea['continuum-efficiency-smooth'],
                                                                       workArea['opacity'][condition],
                                                                       workArea['temperature'][condition],
                                                                       hourAngle_min, hourAngle_max, args.per_ha,
                                                                       nant, args.integration, imageWeights, sind, cosd)
            # Then derive the global average values in the continuum band.
            sensResSmooth = sens.calculateSensitivity(workArea['continuum-smooth-rms'][condition], nant)
            # Check whether we have any unflagged continuum channels.
            if (sensResSmooth['bandwidth']['unflagged'] < 1.0):
                if (args.human_readable):
                    print "FATAL: No continuum bandwidth remains unflagged."
                else:
                    print '{ "error": "No continuum bandwidth remains unflagged." }'
                sys.exit(-1)

            # We get the "general" zoom sensitivity from the unsmoothed continuum data, since smoothing
            # the continuum won't help improve the zoom sensitivity.
            workArea['continuum-rms'][condition] = sens.calculateRms(workArea['continuum'],
                                                                workArea['continuum-efficiency'],
                                                                workArea['opacity'][condition],
                                                                workArea['temperature'][condition],
                                                                hourAngle_min, hourAngle_max, args.per_ha,
                                                                nant, args.integration, imageWeights, sind, cosd)
            # Then derive the global average values in the "general" zoom band.
            sensRes = sens.calculateSensitivity(workArea['continuum-rms'][condition], nant)

            if (specificZoomCalc):
                # The RMS noise in the smoothed specific zoom band, for each channel.
                workArea['specificZoom-rms'][condition] = sens.calculateRms(workArea['specificZoom-smooth'],
                                                                       workArea['specificZoom-efficiency-smooth'],
                                                                       workArea['sz-opacity'][condition],
                                                                       workArea['sz-temperature'][condition],
                                                                       hourAngle_min, hourAngle_max, args.per_ha,
                                                                       nant, args.integration, imageWeights, sind, cosd)
                # Then derive the global average values in the specific zoom band.
                szSensRes = sens.calculateSensitivity(workArea['specificZoom-rms'][condition], nant)

            for t in computeBands:
                if (t == 'zoom'):
                    # Since we don't make a template for the "general" zoom, we have to manually
                    # adjust for the zoom smoothing factor now.
                    # The RMS noise goes down with the square-root of the smoothed bandwidth over the
                    # normal bandwidth.
                    sensRes['rms'][t] /= math.sqrt(float(args.zoom_smoothing))
                    workArea['rms'][t][condition] = float("%.3f" % sensRes['rms'][t])
                    # Calculate the brightness temperature sensitivity using the synthesised beam at
                    # the centre of the continuum band.
                    bts = sens.brightnessTemperatureSensitivity(sensRes['rms'][t], synthBeamContinuum,
                                                           args.frequency)
                else:
                    # We calculate the continuum and continuum-spectral sensitivities in the
                    # same way.
                    workArea['rms'][t][condition] = float("%.3f" % sensResSmooth['rms'][t])
                    # Calculate the brightness temperature sensitivity using the synthesised beam at
                    # the centre of the continuum band.
                    bts = sens.brightnessTemperatureSensitivity(sensResSmooth['rms'][t], synthBeamContinuum,
                                                           args.frequency)
                # We put the brightness sensitivity in mK for readability.
                workArea['btrms'][t][condition] = float("%.2f" % (bts * 1000.0))
                # We keep the SEFDs in Jy.
                workArea['SEFD'][condition] = {
                    'antenna': float( "%.1f" % (sensRes['sefd']['antenna']) ),
                    'array': float( "%.1f" % (sensRes['sefd']['array'])) }

            if (specificZoomCalc):
                # The spectral RMS of the specific zoom band.
                workArea['rms']['specificZoom'][condition] = float("%.3f" % szSensRes['rms']['spectral'])
                # Calculate the brightness temperature sensitivity using the synthesised beam at the
                # nominated specific zoom band frequency.
                bts = sens.brightnessTemperatureSensitivity(szSensRes['rms']['spectral'], synthBeamZoom,
                                                       args.zoomfreq)
                # The brightness sensitivity is again in mK.
                workArea['btrms']['specificZoom'][condition] = float("%.2f" % (bts * 1000.0))

        # Check if we need to adjust the integration time.
        if (args.calculate_time == False):
            # We operate from time to sensitivity, so we exit now.
            sensitivityReached = True
        else:
            # We compare the sensitivity we obtained with the target.
            if (args.target_best):
                conditionTarget = 'best'
            elif (args.target_typical):
                conditionTarget = 'typical'
            elif (args.target_worst):
                conditionTarget = 'worst'

            if (args.target_continuum):
                bandTarget = 'continuum'
            elif (args.target_spectral):
                bandTarget = 'spectral'
            elif (args.target_zoom):
                bandTarget = 'zoom'
            elif (args.target_specific_zoom):
                bandTarget = 'specificZoom'

            if (args.target_flux_density):
                modeTarget = 'rms'
            elif (args.target_brightness_temperature):
                modeTarget = 'btrms'

            compareSensitivity = workArea[modeTarget][bandTarget][conditionTarget]
            # Calculate the ratio of the obtained sensitivity to that desired.
            sensRatio = compareSensitivity / args.target
            # We stop if we're within 1% of the target sensitivity.
            if (abs(sensRatio - 1.0) < 0.01):
                sensitivityReached = True
            else:
                # Change the integration time appropriately.
                args.integration *= sensRatio * sensRatio
            

    # We now stick all this information into the output.
    # The effective bandwidth of the continuum band depends on what the user chose to flag.
    sens.addToOutput(output, 'continuum', 'effective_bandwidth', sensResSmooth['bandwidth']['unflagged'],
                "Effective Bandwidth", "MHz")
    # The effective number of channels in the continuum band depends on the flagging and the
    # smoothing factor.
    sens.addToOutput(output, 'continuum', 'n_channels',
                (int(sensResSmooth['bandwidth']['unflagged'] / contSmoothRes)),
                "# Channels", None)
    # The computed system temperatures over the continuum band, for each weather condition, in K.
    sens.addToOutput(output, 'sensitivities', 'system_temperature',
                [ workArea['continuum-rms']['best']['systemTemperature'],
                  workArea['continuum-rms']['typical']['systemTemperature'],
                  workArea['continuum-rms']['worst']['systemTemperature'] ],
                "System Temperature", "K")

    # The continuum sensitivities, for each weather condition, in mJy/beam.
    sens.addToOutput(output, 'sensitivities', [ 'rms_noise_level', 'continuum' ],
                [ workArea['rms']['continuum']['best'], workArea['rms']['continuum']['typical'],
                  workArea['rms']['continuum']['worst'] ],
                "RMS noise level", "mJy/beam")
    # The continuum brightness temperature sensitivity, for each weather condition, in mK.
    sens.addToOutput(output, 'sensitivities', [ 'brightness_temperature_sensitivity', 'continuum' ],
                [ workArea['btrms']['continuum']['best'], workArea['btrms']['continuum']['typical'],
                  workArea['btrms']['continuum']['worst'] ],
                "Brightness Temperature Sensitivity", "mK")

    # The RMS spectral noise in the continuum band, for each weather condition, in mJy/beam.
    sens.addToOutput(output, 'sensitivities', [ 'rms_noise_level', 'spectral' ],
                [ workArea['rms']['spectral']['best'], workArea['rms']['spectral']['typical'],
                  workArea['rms']['spectral']['worst'] ],
                "RMS noise level", "mJy/beam")
    # The RMS spectral brightness noise in the continuum band, for each weather condition, in mK.
    sens.addToOutput(output, 'sensitivities', [ 'brightness_temperature_sensitivity', 'spectral' ],
                [ workArea['btrms']['spectral']['best'], workArea['btrms']['spectral']['typical'],
                  workArea['btrms']['spectral']['worst'] ],
                "Brightness Temperature Sensitivity", "mK")

    # The RMS spectral noise in a "general" zoom band, for each weather condition, in mJy/beam.
    sens.addToOutput(output, 'sensitivities', [ 'rms_noise_level', 'zoom' ],
                [ workArea['rms']['zoom']['best'], workArea['rms']['zoom']['typical'],
                  workArea['rms']['zoom']['worst'] ],
                "RMS noise level", "mJy/beam")
    # The RMS spectral brightness noise in a "general" zoom band, for each weather condition, in mK.
    sens.addToOutput(output, 'sensitivities', [ 'brightness_temperature_sensitivity', 'zoom' ],
                [ workArea['btrms']['zoom']['best'], workArea['btrms']['zoom']['typical'],
                  workArea['btrms']['zoom']['worst'] ],
                "Brightness Temperature Sensitivity", "mK")

    # The SEFD of a single antenna, for each weather condition, in Jy.
    sens.addToOutput(output, 'sensitivities', 'antenna_sensitivity',
                [ workArea['SEFD']['best']['antenna'], workArea['SEFD']['typical']['antenna'],
                  workArea['SEFD']['worst']['antenna']],
                "Antenna SEFD", "Jy")
    # The SEFD of the entire array combined, for each weather condition, in Jy.
    sens.addToOutput(output, 'sensitivities', 'array_sensitivity',
                [ workArea['SEFD']['best']['array'], workArea['SEFD']['typical']['array'],
                  workArea['SEFD']['worst']['array']],
                "Array SEFD", "Jy")

    if (specificZoomCalc):
        # The computed system temperatures over the specific zoom band, for each weather condition, in K.
        sens.addToOutput(output, 'sensitivities', 'specific_zoom_system_temperature',
                    [ workArea['specificZoom-rms']['best']['systemTemperature'],
                      workArea['specificZoom-rms']['typical']['systemTemperature'],
                      workArea['specificZoom-rms']['worst']['systemTemperature'] ],
                    "System Temperature", "K")
        
        # The RMS spectral noise in the specific zoom band, for each weather condition, in mJy/beam.
        sens.addToOutput(output, 'sensitivities', [ 'rms_noise_level', 'specific_zoom' ],
                    [ workArea['rms']['specificZoom']['best'], workArea['rms']['specificZoom']['typical'],
                      workArea['rms']['specificZoom']['worst'] ],
                    "RMS noise level", "mJy/beam")
        # The RMS spectral brightness noise in the specific zoom band, for each weather condition, in mK.
        sens.addToOutput(output, 'sensitivities', [ 'brightness_temperature_sensitivity', 'specific_zoom' ],
                    [ workArea['btrms']['specificZoom']['best'], workArea['btrms']['specificZoom']['typical'],
                      workArea['btrms']['specificZoom']['worst'] ],
                    "Brightness Temperature Sensitivity", "mK")
    # The integration time is added now, since it may have changed if the user asked for a
    # particular sensitivity target.
    inttime = "%.0f" % args.integration
    sens.addToOutput(output, 'source_imaging', 'integration_time', inttime,
                "Time on Source", "minutes")

    #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\



    ####################################################################################################
    # Plot the RMS spectral noise templates into output files.
    # The name of the output file; we make sure it doesn't end with ".png.png" first.
    outfile = args.output.replace('.png', '') + '.png'
    sens.plotSpectrum(workArea['continuum-smooth-rms'], [ 'typical', 'best', 'worst' ], outfile)
    # Put the name of the output file in the output dictionary.
    output['output_plot'] = outfile

    if (specificZoomCalc):
        # We make an output plot of the RMS spectral noise of the specific zoom as well.
        szoutfile = args.output.replace('.png', '') + '.sz.png'
        sens.plotSpectrum(workArea['specificZoom-rms'], [ 'typical', 'best', 'worst'], szoutfile)
        # Put the name of this output file in the output dictionary.
        output['output_zoom_plot'] = szoutfile
    #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\



    ####################################################################################################
    # Output all the quantities we have computed and stored.
    if (args.human_readable):
        # Output the object in a human readable format.
        humanOutputDict(output, output['description'], output['units'], 0)
    else:
        # Output the JSON.
        print json.dumps(output)
    #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    # SENSITIVITY CALCULATOR ENDS
