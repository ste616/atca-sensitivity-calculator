######################################################################
# The ATCA Sensitivity Calculator
# Calculation subroutines.
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

import os
import math
import sys
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import refract as refract

# Define some global parameters.
frequencyBands = {
    # Low and high frequencies for each of the ATCA receivers, and the file to
    # read to get Tsys information.
    '16cm': { 'low': 1730, 'high': 2999,
              'tsys': "systemps/ca02_21cm_x_polarisation.avg" },
    '4cm': { 'low': 4928, 'high': 10928,
             'tsys': "systemps/ca02_4cm_y_polarisation.avg" },
    '15mm': { 'low': 16000, 'high': 25000,
              'tsys': "systemps/12mm_recvtemps.avg" },
    '7mm': { 'low': 30000, 'high': 50000,
             'tsys': "systemps/ca02_7mm.avg" },
    '3mm': { 'low': 83857, 'high': 104785,
             'tsys': "systemps/nominal_3mm.avg" }
}
sideBands = {
    # Which sideband is used per frequency range.
    'USB': [ [ 4928, 10928 ], [ 41000, 50000 ], [ 97800, 104785 ] ],
    'LSB': [ [ 1730, 2999 ], [ 16000, 25000 ], [ 30000, 40999 ],
             [ 83857, 97799 ] ]
}
continuumBandwidth = 2049.0 # MHz bandwidth of the continuum bands.
nZoomChannels = 2048 # the number of channels each zoom has
antennaDiameter = 22.0 # metres
speedoflight = 299792458.0 # Speed of light, m/s
boltzmann = 1.3806488e-23 # J / K
latitudeATCA = -30.31288472 # degrees, latitude of the ATCA.
longitudeATCA = 149.5501388 # degrees, longitude of the ATCA.
eastAngle = longitudeATCA - 90.0
cangle = math.radians(eastAngle)
cosl = math.cos(math.radians(latitudeATCA))
sinl = math.sin(math.radians(latitudeATCA))
channelFlagging = {
    # The channels always flagged in the continuum band.
    'continuum': { 'CFB1M': [ 513, 1025, 1537 ],
                   'CFB64M': [ 9, 17, 25 ] },
    # The sampling clock birdies.
    'birdies': { 'CFB1M': [ 129, 157, 257, 641, 769, 1153, 1177, 1281, 1409, 1793, 1921 ] }
}
frequencyFlagging = {
    # Known RFI ranges.
    'rfi': [ [ 1059.0, 1075.0 ], [ 1103.0, 1117.0 ], [ 1145.0, 1159.0 ], [ 1165.0, 1191.0 ],
             [ 1217.0, 1239.0 ], [ 1240.0, 1252.0 ], [ 1380.0, 1382.0 ], [ 1428.0, 1432.0 ],
             [ 1436.0, 1450.0 ], [ 1456.0, 1460.0 ], [ 1493.0, 1495.0 ], [ 1499.0, 1511.0 ],
             [ 1525.0, 1628.0 ], [ 2489.0, 2496.0 ], [ 2879.0, 2881.0 ], [ 5622.0, 5628.0 ],
             [ 5930.0, 5960.0 ], [ 6440.0, 6480.0 ], [ 7747.0, 7777.0 ], [ 7866.0, 7896.0 ],
             [ 8058.0, 8088.0 ], [ 8177.0, 8207.0 ] ]
}
# Some conversion factors.
mhzToHz = 1.0e6 # Convert MHz to Hz
degreesToArcmin = 60.0 # Convert degrees to arcminutes
degreesToArcsec = 3600.0 # Convert degrees to arcseconds
jyToSI = 1e-26 # Convert Jy to W.m^-2.s^-1
mToKm = 1e-3 # Convert m to km

# Our error handling class.
class CalcError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def frequencyOverlap(inf1, inf2, ing1, ing2):
    # Given two frequency ranges f1 - f2, g1 - g2, returns the amount
    # of frequency overlap.
    overlap = 0.0
    
    # Check for correct frequency order.
    f1 = inf1
    f2 = inf2
    g1 = ing1
    g2 = ing2
    if (f2 < f1):
        f1 = inf2
        f2 = inf1
    if (g2 < g1):
        g1 = ing2
        g2 = ing1

    # Assess overlap.
    if ((g1 >= f1) and (g1 <= f2)):
        a1 = g2 - g1
        a2 = f2 - g1
        overlap += min(a1, a2)
    elif ((g2 >= f1) and (g2 <= f2)):
        a1 = g2 - g1
        a2 = g2 - f1
        overlap += min(a1, a2)
    elif ((f1 >= g1) and (f1 <= g2)):
        a1 = f2 - f1
        a2 = g2 - f1
        overlap += min(a1, a2)
    elif ((f2 >= g1) and (f2 <= g2)):
        a1 = f2 - f1
        a2 = f2 - g1
        overlap += min(a1, a2)

    return overlap

def frequencyBand(freq):
    # Which band does the frequency belong to?
    for b in frequencyBands:
        if (freq >= frequencyBands[b]['low'] and
            freq <= frequencyBands[b]['high']):
            return b
    return None

def channelResolution(corrMode):
    # Return the width of each type of channel for a given correlator mode.
    if (corrMode == 'CFB1M'):
        return { 'continuum': 1.0, 'zoom': (1.0 / 2048.0) }
    elif (corrMode == 'CFB64M'):
        return { 'continuum': 64.0, 'zoom': (64.0 / 2048.0) }
    else:
        return None

def makeTemplate(centreFreq, bandwidth, channelWidth):
    # Make a blank spectrum that covers the specified frequency range with
    # the correct channel resolution.
    c = []
    v = []
    f = []
    n = []
    x = []
    p = []
    if (type(bandwidth) is float):
        lowFreq = centreFreq - (bandwidth - channelWidth) / 2 
        highFreq = centreFreq + (bandwidth - channelWidth) / 2
    elif (type(bandwidth) is list):
        lowFreq = centreFreq - bandwidth[0]
        highFreq = centreFreq + bandwidth[1]
    cFreq = lowFreq
    chanNum = 1
    while (cFreq <= highFreq):
        c.append(cFreq)
        v.append(0.0)
        n.append(0)
        f.append(False)
        p.append(0.0)
        x.append(chanNum)
        cFreq += channelWidth
        chanNum += 1
    nx = np.array(x)
    for i in xrange(0, len(sideBands['LSB'])):
        if ((centreFreq >= sideBands['LSB'][i][0]) and
            (centreFreq <= sideBands['LSB'][i][1])):
            # This band is LSB, so we flip the channel numbers.
            nx = nx[::-1]
            break

    return { 'centreFrequency': np.array(c), 'value': np.array(v),
             'count': np.array(n), 'flags': f,
             'flaggedBandwidth': p,
             'channelWidth': channelWidth, 'channelNumber': nx }

def averageTemplate(template):
    # Return the average unflagged value of a template.
    varr = np.array([])
    for i in xrange(0, len(template['value'])):
        if (template['flags'][i] == False):
            varr = np.append(varr, template['value'][i])
    return np.mean(varr)

def getFreq(item):
    return item[0]

def frequencyToWavelength(freq):
    # Convert a frequency in MHz to a wavelength in metres.
    wl = speedoflight / (freq * mhzToHz)
    return (wl)

def baselineToLambda(freq, baselineLength):
    # Convert a basline length in metre to lambda for a specified frequency.
    wl = frequencyToWavelength(freq)
    bl = baselineLength / wl
    return (bl)

def primaryBeamSize(freq, diam):
    # Calculate the size of the primary beam for an antenna with a specified diameter (m),
    # at the specified frequency (MHz), in arcmin.
    pbfwhm = math.degrees((speedoflight / diam) / (freq * mhzToHz)) * degreesToArcmin
    tpbfwhm = "%.1f" % pbfwhm
    return (float(tpbfwhm))

def synthesisedBeamSize(freq, baselineLength, dec, minHa, maxHa, weightFactor):
    # Calculate the synthesised beam size given a frequency, baseline length,
    # declination and the minimum and maximum hour angles observed.
    # Returns an array where minor axis is the first element, and major
    # FWHM is the second.
    blX = baselineToLambda(freq, baselineLength['dX'])
    blY = baselineToLambda(freq, baselineLength['dY'])
    blZ = baselineToLambda(freq, baselineLength['dZ'])

    # We need the hour angles in radians.
    minHaRad = math.radians(minHa * 15.0)
    maxHaRad = math.radians(maxHa * 15.0)

    # We use the full TMS equation 4.1 here.
    # Find the hour angle for maximum u.
    umaxHa = math.degrees(math.atan2(blX, blY)) / 15.0
    if (umaxHa < minHa):
        umaxHa = minHa
    if (umaxHa > maxHa):
        umaxHa = maxHa
    umaxHaRad = math.radians(umaxHa * 15.0)
    umax = abs(math.sin(umaxHaRad) * blX + math.cos(umaxHaRad) * blY)
    # Find the hour angle for maximum v.
    vmaxHa = math.degrees(math.atan2(-1 * blY, blX)) / 15.0
    if (vmaxHa < minHa):
        vmaxHa = minHa
    if (vmaxHa > maxHa):
        vmaxHa = maxHa
    vmaxHaRad = math.radians(vmaxHa * 15.0)
    vmax = abs(-1 * math.sin(math.radians(dec)) * math.cos(vmaxHaRad) * blX +
               math.sin(math.radians(dec)) * math.sin(vmaxHaRad) * blY +
               math.cos(math.radians(dec)) * blZ)

    # The resolution is simply the inverse of umax or vmax, but we also
    # convert to arcseconds and multiply by the image weighting factor.
    ures = math.degrees(1.0 / umax) * degreesToArcsec * weightFactor
    # This next line will trigger a ZeroDivisionError if the source is
    # on the celestial equator and we're in an EW array.
    vres = math.degrees(1.0 / vmax) * degreesToArcsec * weightFactor

    # We now take care of significant figures.
    utmp = "%.2f" % ures
    vtmp = "%.2f" % vres
    ures = float(utmp)
    vres = float(vtmp)

    # Make the output with the minor axis first.
    res = [ ures, vres ]
    if (ures > vres):
        res = [ vres, ures ]
    return (res)

def ellipseArea(minor, major):
    # Returns the area of an ellipse with specified minor and major
    # axis lengths (in arcseconds), in sr.
    mn = (minor / 2.0) / degreesToArcsec
    mj = (major / 2.0) / degreesToArcsec
    a = math.pi * mn * mj # in square degrees
    asr = a / (180.0 / math.pi)**2 # in steradians
    return (asr)

def brightnessTemperatureSensitivity(rms, synthBeam, freq):
    # Calculate the brightness temperature sensitivity (K) of an observation
    # with an RMS noise level (mJy/beam), a synthesised beam size (arcsec),
    # and a frequency in MHz. This comes from TMS equation 1.2.
    A = ellipseArea(synthBeam[0], synthBeam[1])
    I = (rms / 1000.0) * jyToSI / A
    wl = frequencyToWavelength(freq)
    bt = wl * wl * I / (2.0 * boltzmann)
    return (bt)

def readTsys(filename, lf, hf):
    # Open the filename.
    if (os.path.isfile(filename)):
        # Read it.
        d = np.loadtxt(filename)
        # Sort it.
        ds = sorted(d, key=getFreq)
        # Split it.
        startIndex = 0
        endIndex = len(ds) - 1
        llf = lf / 1000.0
        hhf = hf / 1000.0
        while ((ds[startIndex][0] < llf) and
               (startIndex < (len(ds) - 1)) and
               (ds[startIndex + 1][0] < llf)):
            startIndex += 1
        while ((ds[endIndex][0] > hhf) and
               (endIndex > 0) and
               (ds[endIndex - 1][0] > hhf)):
            endIndex -= 1
        if (startIndex == endIndex):
            if (startIndex > 0):
                startIndex -= 1
            if (endIndex < (len(ds) - 1)):
                endIndex += 1
        dds = ds[startIndex:(endIndex + 1)]
        c = [np.around(row[0] * 1000.0) for row in dds]
        v = [(10 ** row[1]) for row in dds]
        n = []
        f = []
        for i in xrange(0, len(v)):
            n.append(1)
            f.append(False)
        return { 'centreFrequency': c, 'value': v, 'count': np.array(n),
                 'flags': f,
                 'channelWidth': 1.0 }
    else:
        raise CalcError("Can't find Tsys file %s." % filename)

def lowHigh(c, w):
    return { 'low': c - (w / 2.0), 'high': c + (w / 2.0) }

def overlaps(a, b):
    if (b['low'] >= a['high']):
        return False
    if (b['high'] <= a['low']):
        return False
    return True

def templateAverage(t):
    # Divide the values by the counts.
    for i in xrange(0, len(t['centreFrequency'])):
        if (t['count'][i] > 0):
            t['value'][i] /= float(t['count'][i])
            if (isinstance(t['flags'][i], list) == True):
                # Multiple input flags, we choose the most common.
                ft = 0
                ff = 0
                for j in xrange(0, len(t['flags'][i])):
                    if (t['flags'][i][j]):
                        ft += 1
                    else:
                        ff += 1
                if (ft > ff):
                    t['flags'][i] = True
                else:
                    t['flags'][i] = False

def linearInterpolate(p1, p2, pi):
    # Using information from p1 and p2, determine the value at pi.
    run = p2['frequency'] - p1['frequency']
    if (run != 0):
        slope = (p2['value'] - p1['value']) / run
    else:
        slope = 0
    nrun = pi['frequency'] - p1['frequency']
    return p1['value'] + nrun * slope

def templateInterpolate(t):
    # Interpolate values for channels with no counts.
    # Get the array for where counts is 0 and not.
    zeroes = np.where(t['count'] == 0)
    good = np.where(t['count'] > 0)
    # Get the arrays without zero counts.
    cf = t['centreFrequency'][good]
    vs = t['value'][good]
    # And the values we need to interpolate for.
    rf = t['centreFrequency'][zeroes]
    # And then interpolate.
    iv = np.interp(rf, cf, vs)
    t['value'][zeroes] = iv
    
def templateFill(srcTemplate, destTemplate):
    # Fill in a template spectrum with values from another template, and do it with
    # a single pass of each array (no looping).
    i = 0 # The index of the destination template bin
    j = 0 # The index of the source template bin
    sfs = lowHigh(srcTemplate['centreFrequency'][j], srcTemplate['channelWidth'])
    dfs = lowHigh(destTemplate['centreFrequency'][i], destTemplate['channelWidth'])
    while (i < len(destTemplate['centreFrequency']) and
           j < len(srcTemplate['centreFrequency'])):
        if (overlaps(dfs, sfs)):
            destTemplate['value'][i] += srcTemplate['value'][j]
            destTemplate['count'][i] += 1
            if (destTemplate['count'][i] > 1):
                if (destTemplate['count'][i] == 2):
                    t = [ destTemplate['flags'][i], srcTemplate['flags'][j] ]
                    destTemplate['flags'][i] = t
                else:
                    destTemplate['flags'][i].append(srcTemplate['flags'][j])
            else:
                destTemplate['flags'][i] = srcTemplate['flags'][j]
            j += 1
            if (j < len(srcTemplate['centreFrequency'])):
                sfs = lowHigh(srcTemplate['centreFrequency'][j], srcTemplate['channelWidth'])
        elif (srcTemplate['centreFrequency'][j] < destTemplate['centreFrequency'][i]):
            j += 1
            if (j < len(srcTemplate['centreFrequency'])):
                sfs = lowHigh(srcTemplate['centreFrequency'][j], srcTemplate['channelWidth'])
        else:
            i += 1
            if (i < len(destTemplate['centreFrequency'])):
                dfs = lowHigh(destTemplate['centreFrequency'][i], destTemplate['channelWidth'])

    templateAverage(destTemplate)

    # Check that the edges aren't empty
    # Bottom edge.
    if (destTemplate['count'][0] == 0):
        # Have to interpolate from the source template.
        dfs = lowHigh(destTemplate['centreFrequency'][0], destTemplate['channelWidth'])
        j = 0
        sfs = lowHigh(srcTemplate['centreFrequency'][j], srcTemplate['channelWidth'])
        while (sfs['high'] < dfs['low']):
            j += 1
            sfs = lowHigh(srcTemplate['centreFrequency'][j], srcTemplate['channelWidth'])
        j -= 1 # Because the breaking point is when the frequency goes too high.
        i = 1
        while (i < (len(destTemplate['count']) - 1) and destTemplate['count'][i] == 0):
            i += 1
        destTemplate['value'][0] = linearInterpolate({ 'value': srcTemplate['value'][j],
                                                       'frequency': srcTemplate['centreFrequency'][j] },
                                                     { 'value': destTemplate['value'][i],
                                                       'frequency': destTemplate['centreFrequency'][i] },
                                                     { 'frequency': destTemplate['centreFrequency'][0] } )
        destTemplate['count'][0] = 1
    # Top edge.
    if (destTemplate['count'][-1] == 0):
        dfs = lowHigh(destTemplate['centreFrequency'][-1], destTemplate['channelWidth'])
        j = 0
        sfs = lowHigh(srcTemplate['centreFrequency'][j], srcTemplate['channelWidth'])
        while (sfs['high'] <= dfs['low']):
            j += 1
            if (j < len(srcTemplate['centreFrequency'])):
                sfs = lowHigh(srcTemplate['centreFrequency'][j], srcTemplate['channelWidth'])
            else:
                j -= 1
                break
        # Break point is fine this time.
        i = -2
        while (destTemplate['count'][i] == 0 and (abs(i) < (len(destTemplate['centreFrequency'])))):
            i -= 1
        destTemplate['value'][-1] = linearInterpolate({ 'value': srcTemplate['value'][j],
                                                        'frequency': srcTemplate['centreFrequency'][j] },
                                                      { 'value': destTemplate['value'][i],
                                                        'frequency': destTemplate['centreFrequency'][i] },
                                                      { 'frequency': destTemplate['centreFrequency'][-1] } )
        destTemplate['count'][-1] = 1

    templateInterpolate(destTemplate)

def templateEfficiency():
    # The template returned by this routine contains all the efficiencies for
    # all the bands.
    c = [   900.0,   1200.0,   1500.0,   1800.0,  2100.0,  2300.0,  2500.0,  4400.0,  5900.0,
           7400.0,   8800.0,  10600.0,  16000.0, 16500.0, 17000.0, 17500.0, 18000.0, 18500.0,
          19000.0,  19500.0,  20000.0,  20500.0, 21000.0, 21500.0, 22000.0, 22500.0, 23000.0,
          23500.0,  24000.0,  24500.0,  25000.0, 25400.0, 30000.0, 31000.0, 32000.0, 33000.0,
          34000.0,  35000.0,  36000.0,  37000.0, 38000.0, 39000.0, 40000.0, 41000.0, 42000.0,
          43000.0,  44000.0,  45000.0,  46000.0, 47000.0, 48000.0, 49000.0, 50000.0, 83781.1,
          85556.2,  86834.3,  88680.5,  90526.6, 91946.7, 94005.9, 95852.1, 97272.2, 98976.3,
         100254.4, 102200.0, 102300.0, 106432.0 ]
    v = [  0.57,     0.57,     0.60,     0.53,    0.43,    0.42,    0.44,    0.65,    0.72,
           0.65,     0.64,     0.65,     0.58,    0.62,    0.63,    0.65,    0.67,    0.70,
           0.68,     0.64,     0.64,     0.60,    0.53,    0.55,    0.54,    0.51,    0.51,
           0.53,     0.49,     0.49,     0.46,    0.47,    0.60,    0.60,    0.60,    0.60,
           0.60,     0.60,     0.60,     0.60,    0.60,    0.60,    0.60,    0.59,    0.58,
           0.57,     0.56,     0.55,     0.54,    0.53,    0.52,    0.51,    0.50,    0.3297,
           0.3065,   0.3020,   0.2856,   0.2689,  0.2670,  0.2734,  0.2727,  0.2521,  0.2403,
           0.2336,   0.2322,   0.14,     0.14 ]
    f = []
    n = []
    for i in xrange(0, len(c)):
        n.append(1)
        f.append(False)
    return { 'centreFrequency': np.array(c), 'value': np.array(v),
             'count': np.array(n), 'flags': f,
             'channelWidth': 1.0 }

def fillAtmosphereTemplate(templateOpacity, templateTemperature, t, p, h):
    # Calculate the opacity and atmospheric temperature at the zenith for each frequency
    # in the template.
    atmos = refract.calcOpacity(templateOpacity['centreFrequency'] * 1e6, math.radians(90.0), t, p, h)
    templateOpacity['value'] = np.array(atmos['tau'])
    templateTemperature['value'] = np.array(atmos['Tb'])

def plotTemplate(t, e, outname):
    plt.clf()
    plt.plot(t['centreFrequency'], t['value'])
    plt.plot(e['centreFrequency'], (e['value']), "green")
    plt.savefig(outname)

def plotSpectrum(template, conditions, outname):
    # Plot the template spectrum we are passed with frequency on the x-axis.
    # Initialise the plot.
    plt.clf()
    fig = plt.figure()
    ax = fig.add_subplot(111)

    # These are the colours we can use for the different lines.
    colours = [ "blue", "green", "red", "black", "yellow" ]

    # Go through the conditions (usually weather conditions) and plot a line for each.
    for i, c in enumerate(conditions):
        ax.plot(template[c]['centreFrequency'], template[c]['value'], colours[i], label=c)

    # Set the x-axis limits to be tight on the actual frequency range.
    plt.xlim(template[c]['centreFrequency'][0], template[c]['centreFrequency'][-1])
    plt.xlabel("Frequency [MHz]")
    plt.ylabel("RMS noise level [mJy/beam]")

    # Ensure that the x- and y-axes don't have an offset value.
    ax.get_yaxis().get_major_formatter().set_useOffset(False)
    ax.get_xaxis().get_major_formatter().set_useOffset(False)

    # Put the legend with the condition names at the top of the plot outside the border.
    plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
               ncol=len(c), mode="expand", borderaxespad=0.)

    # Highlight the regions that are flagged in the template.
    for i in xrange(0, len(template[conditions[0]]['flags'])):
        if (template[conditions[0]]['flags'][i] == True):
            x1 = template[conditions[0]]['centreFrequency'][i] - template[c]['channelWidth'] / 2.0
            x2 = template[conditions[0]]['centreFrequency'][i] + template[c]['channelWidth'] / 2.0
            plt.axvspan(x1, x2, alpha=0.2, edgecolor='none', facecolor='red')
    plt.savefig(outname)

def flagTemplate(t, flagType, corrMode, edgeChan):
    # Set the flags in the template.
    if ((flagType == "continuum") or (flagType == "birdies")):
        # This is channel based flagging.
        flagSrc = channelFlagging[flagType]
        if (corrMode in flagSrc):
            flagSrc = flagSrc[corrMode]
            for c in xrange(0, len(flagSrc)):
                for i in xrange(0, len(t['flags'])):
                    if (t['channelNumber'][i] == flagSrc[c]):
                        t['flags'][i] = True
                        break
    elif (flagType == "rfi"):
        # This is frequency based flagging.
        oldi = 0
        flagSrc = frequencyFlagging[flagType]
        for r in xrange(0, len(flagSrc)):
            for i in xrange(oldi, len(t['flags'])):
                f1 = t['centreFrequency'][i] - t['channelWidth'] / 2.0
                f2 = t['centreFrequency'][i] + t['channelWidth'] / 2.0
                if (f1 > flagSrc[r][1]):
                    break
                t['flaggedBandwidth'][i] += frequencyOverlap(f1, f2, flagSrc[r][0], flagSrc[r][1])
                oldi = i
        # Check for which channels are above the percentage flagged cut.
        for i in xrange(0, len(t['flags'])):
            p = t['flaggedBandwidth'][i] / t['channelWidth']
            if (p > 0.5):
                t['flags'][i] = True
    elif (flagType == "edge"):
        # Flag edge channels.
        for i in xrange(0, len(t['channelNumber'])):
            cn = i + 1
            rcn = len(t['channelNumber']) - i
            if ((cn <= edgeChan) or
                (rcn <= edgeChan)):
                t['flags'][i] = True

def calculateSensitivity(rmsTemplate, nAnts):
    # Given a template filled with the RMS noise in each channel in the continuum
    # band, return the average sensitivity of the continuum band channels (the spectral
    # RMS), and the spectral RMS divided by the bandwidth (the continuum RMS). This
    # routine does this while respecting any flagging present in the template.
    rmsTotal = 0.0
    rmsZoomTotal = 0.0
    rmsN = 0
    rmsZoomN = 0
    for i in xrange(0, len(rmsTemplate['value'])):
        # We count flagged continuum channels in the zoom RMS calculation.
        rmsZoomTotal += rmsTemplate['value'][i]
        rmsZoomN += 1
        if (rmsTemplate['flags'][i] == False):
            rmsTotal += rmsTemplate['value'][i]
            rmsN += 1
    
    if (rmsN > 0):
        rmsSpectral = rmsTotal / rmsN
        totalBandwidth = rmsN * rmsTemplate['channelWidth']
        rmsContinuum = rmsSpectral / math.sqrt(float(rmsN))
        rmsZoom = rmsSpectral * math.sqrt(float(nZoomChannels))
    else:
        rmsSpectral = None
        totalBandwidth = None
        rmsContinuum = None
        rmsZoom = None

    # Calculate the SEFDs for each antenna and the array as a whole.
    # We use TMS equation 1.6 for this and convert to Jy.
    Aone = surfaceArea(antennaDiameter)
    Aall = nAnts * Aone
    sefdOne = 2.0 * boltzmann * rmsTemplate['systemp'] / (Aone * 1e-26)
    sefdAll = 2.0 * boltzmann * rmsTemplate['systemp'] / (Aall * 1e-26)

    return { 'rms': { 'spectral': rmsSpectral, 'continuum': rmsContinuum, 'zoom': rmsZoom },
             'bandwidth': { 'unflagged': totalBandwidth }, 'sefd': { 'antenna': sefdOne,
                                                                     'array': sefdAll } }

def calculateRms(tsys, efficiency, opacity, temperature, minHa, maxHa, perHa, nAntenna,
                 totalTime, weighting, sind, cosd):
    # Given the tsys and efficiency templates, the number of antennas involved in the
    # imaging, the total integration time and the image weighting scheme, this routine
    # will return another template with each channel being the RMS noise expected in
    # that channel. This comes from eqn 6.62 of TMS, where eta_Q is 1 (for CABB's
    # digitisation) but A is multiplied by our efficiency factor. That equation is
    # for only a single polarisation though, so for an unpolarised source, the noise
    # level is sqrt(2) lower, which is where the sqrt(2) factor in the numerator comes from
    # instead of the 2.

    # The variables for our output template.
    c = []
    v = []
    n = []
    f = []

    # Figure out how much time is spent in each integration period.
    haRange = maxHa - minHa
    nIntegrations = math.ceil(haRange * perHa)
    intTime = totalTime / nIntegrations

    Texcess = []
    systemTemperature = []
    for j in xrange(0, int(nIntegrations + 1)):
        # The hour angle at this integration.
        jHa = minHa + float(j) / perHa
        
        # The elevation at this hour angle.
        cosha = math.cos(math.radians(jHa * 15.0))
        sinel = sinl * sind + cosl * cosd * cosha
        
        # Calculate the excess temperature due to the atmosphere
        # and CMB.
        elFactor = np.exp(-1.0 * opacity['value'] / sinel)
        cbFactor = 2.7 * elFactor
        ivFactor = 1.0 - elFactor
        atFactor = temperature['value'] * ivFactor
        Texcess.append(atFactor + cbFactor)

    for i in xrange(0, len(tsys['centreFrequency'])):
        # Check that the frequencies are the same in both templates.
        if (tsys['centreFrequency'][i] == efficiency['centreFrequency'][i]):
            # All's good.
            c.append(tsys['centreFrequency'][i])

            # Get the average excess temperature now.
            exTemp = [ row[i] for row in Texcess ]
            excessTemp = np.sum(exTemp) / float(len(exTemp))

            Tmeas = tsys['value'][i] + excessTemp
            TmeasEff = Tmeas / efficiency['value'][i]
            
            # The units of this is actually mJy since we keep the frequency
            # in MHz rather than converting to Hz (convenient isn't it!).
            v.append((math.sqrt(2.0) * boltzmann * Tmeas * weighting['avg']) /
                     (1e-26 * surfaceArea(antennaDiameter) *
                      efficiency['value'][i] *
                      math.sqrt(float(nAntenna) * float(nAntenna - 1) *
                                tsys['channelWidth'] * (totalTime * 60.0))))
            n.append(1)
            if (tsys['flags'][i] or efficiency['flags'][i]):
                f.append(True)
            else:
                f.append(False)
                systemTemperature.append(TmeasEff)

    return { 'centreFrequency': np.array(c), 'value': np.array(v),
             'count': np.array(n), 'flags': f,
             'channelWidth': tsys['channelWidth'], 'channelNumber': tsys['channelNumber'],
             'systemp': np.mean(systemTemperature),
             'systemTemperature': float("%.1f" % np.mean(systemTemperature))}

def surfaceArea(d):
    # Given the diameter of a dish (m), return its surface area (m^2).
    return (math.pi * ((d / 2.0) ** 2))

def weightingFactor(weighting, array, ant6):
    # Return the w_rms / w_mean weighting factors given the weighting scheme,
    # the array configuration and whether antenna 6 is included in the imaging.
    
    # The weighting factors we determined from simulations.
    factors = [
        { 'array': [ '6000', '6km', '3000', '3km' ],
          'factors': [
              { 'ca06': True,
                'R2': { 'avg': 1.039, 'min': 1.000, 'max': 1.079, 'beam': 1.32 },
                'R1': { 'avg': 1.040, 'min': 1.000, 'max': 1.080, 'beam': 1.32 },
                'R0': { 'avg': 1.871, 'min': 1.350, 'max': 2.781, 'beam': 0.84 },
                'R-1': { 'avg': 5.791, 'min': 3.685, 'max': 10.987, 'beam': 0.80 },
                'R-2': { 'avg': 5.847, 'min': 3.688, 'max': 11.240, 'beam': 0.80 } },
              { 'ca06': False,
                'R2': { 'avg': 1.000, 'min': 1.000, 'max': 1.000, 'beam': 0.97 },
                'R1': { 'avg': 1.002, 'min': 1.001, 'max': 1.004, 'beam': 0.89 },
                'R0': { 'avg': 1.882, 'min': 1.703, 'max': 1.943, 'beam': 0.66 },
                'R-1': { 'avg': 3.875, 'min': 2.543, 'max': 7.102, 'beam': 0.64 },
                'R-2': { 'avg': 3.908, 'min': 2.562, 'max': 7.222, 'beam': 0.64 } } ] },
        { 'array': [ '1500', '1.5km' ],
          'factors': [
              { 'ca06': True,
                'R2': { 'avg': 1.000, 'min': 1.000, 'max': 1.000, 'beam': 1.32 },
                'R1': { 'avg': 1.000, 'min': 1.000, 'max': 1.001, 'beam': 1.32 },
                'R0': { 'avg': 1.507, 'min': 1.181, 'max': 1.846, 'beam': 0.84 },
                'R-1': { 'avg': 7.925, 'min': 5.200, 'max': 16.732, 'beam': 0.80 },
                'R-2': { 'avg': 8.151, 'min': 5.163, 'max': 19.304, 'beam': 0.80 } },
              { 'ca06': False,
                'R2': { 'avg': 1.000, 'min': 1.000, 'max': 1.000, 'beam': 0.96 },
                'R1': { 'avg': 1.001, 'min': 1.000, 'max': 1.003, 'beam': 0.88 },
                'R0': { 'avg': 1.854, 'min': 1.576, 'max': 1.953, 'beam': 0.64 },
                'R-1': { 'avg': 3.900, 'min': 2.524, 'max': 8.218, 'beam': 0.62 },
                'R-2': { 'avg': 3.923, 'min': 2.506, 'max': 8.707, 'beam': 0.62 } } ] },
        { 'array': [ '750', '750m' ],
          'factors': [
              { 'ca06': True,
                'R2': { 'avg': 1.000, 'min': 1.000, 'max': 1.000, 'beam': 1.32 },
                'R1': { 'avg': 1.000, 'min': 1.000, 'max': 1.000, 'beam': 1.32 },
                'R0': { 'avg': 1.299, 'min': 1.143, 'max': 1.621, 'beam': 0.84 },
                'R-1': { 'avg': 12.893, 'min': 8.581, 'max': 17.674, 'beam': 0.80 },
                'R-2': { 'avg': 14.027, 'min': 8.882, 'max': 22.273, 'beam': 0.80 } },
              { 'ca06': False,
                'R2': { 'avg': 1.000, 'min': 1.000, 'max': 1.000, 'beam': 0.96 },
                'R1': { 'avg': 1.001, 'min': 1.000, 'max': 1.002, 'beam': 0.88 },
                'R0': { 'avg': 1.925, 'min': 1.850, 'max': 1.971, 'beam': 0.62 },
                'R-1': { 'avg': 3.557, 'min': 2.578, 'max': 5.255, 'beam': 0.59 },
                'R-2': { 'avg': 3.582, 'min': 2.583, 'max': 5.369, 'beam': 0.59 } } ] },
        { 'array': [ '367', 'EW352', 'EW367', 'EW352/367' ],
          'factors': [
              { 'ca06': True,
                'R2': { 'avg': 1.000, 'min': 1.000, 'max': 1.000, 'beam': 1.32 },
                'R1': { 'avg': 1.000, 'min': 1.000, 'max': 1.000, 'beam': 1.32 },
                'R0': { 'avg': 1.077, 'min': 1.029, 'max': 1.157, 'beam': 0.84 },
                'R-1': { 'avg': 18.304, 'min': 16.432, 'max': 17.498, 'beam': 0.80 },
                'R-2': { 'avg': 31.295, 'min': 20.574, 'max': 52.204, 'beam': 0.80 } },
              { 'ca06': False,
                'R2': { 'avg': 1.000, 'min': 1.000, 'max': 1.000, 'beam': 1.09 },
                'R1': { 'avg': 1.001, 'min': 1.000, 'max': 1.001, 'beam': 1.00 },
                'R0': { 'avg': 1.917, 'min': 1.838, 'max': 1.965, 'beam': 0.68 },
                'R-1': { 'avg': 3.271, 'min': 2.537, 'max': 4.639, 'beam': 0.64 },
                'R-2': { 'avg': 3.298, 'min': 2.550, 'max': 4.718, 'beam': 0.64 } } ] },
        { 'array': [ 'h214', 'H214', 'h168', 'H168', 'h75', 'H75' ],
          'factors': [
              { 'ca06': True,
                'R2': { 'avg': 1.000, 'min': 1.000, 'max': 1.000, 'beam': 1.32},
                'R1': { 'avg': 1.000, 'min': 1.000, 'max': 1.000, 'beam': 1.32},
                'R0': { 'avg': 1.106, 'min': 1.023, 'max': 1.186, 'beam': 0.84},
                'R-1': { 'avg': 16.865, 'min': 15.629, 'max': 18.294, 'beam': 0.80 },
                'R-2': { 'avg': 26.926, 'min': 18.717, 'max': 58.094, 'beam': 0.80 } },
              { 'ca06': False,
                'R2': { 'avg': 1.000, 'min': 1.000, 'max': 1.000, 'beam': 0.75 },
                'R1': { 'avg': 1.001, 'min': 1.001, 'max': 1.002, 'beam': 0.74 },
                'R0': { 'avg': 1.641, 'min': 1.529, 'max': 1.760, 'beam': 0.61 },
                'R-1': { 'avg': 1.984, 'min': 1.753, 'max': 2.281, 'beam': 0.59 },
                'R-2': { 'avg': 1.988, 'min': 1.755, 'max': 2.288, 'beam': 0.59 } } ] } ]

    # Search through the array.
    for f in xrange(0, len(factors)):
        arrayFound = False
        for i in xrange(0, len(factors[f]['array'])):
            if (array == factors[f]['array'][i]):
                arrayFound = True
                break
        if (arrayFound):
            g = 1
            if (ant6):
                g = 0
            if (weighting in factors[f]['factors'][g]):
                return (factors[f]['factors'][g][weighting])
    # We couldn't find the appropriate weighting factors.
    raise CalcError("Weighting factors are not available.")

def maximumBaseline(array):
    # Return the maximum baseline length for a named array, both on the track
    # only, and including CA06.

    stationLocations = {
        'W0': [ -4752438.459, 2790321.299, -3200483.747 ],
        'W2': [ -4752422.922, 2790347.675, -3200483.747 ],
        'W4': [ -4752407.385, 2790374.052, -3200483.747 ],
        'W6': [ -4752391.848, 2790400.428, -3200483.747 ],
        'W8': [ -4752376.311, 2790426.804, -3200483.747 ],
        'W10': [ -4752360.774, 2790453.181, -3200483.747 ],
        'W12': [ -4752345.237, 2790479.557, -3200483.747 ],
        'W14': [ -4752329.700, 2790505.934, -3200483.747 ],
        'W16': [ -4752314.163, 2790532.310, -3200483.747 ],
        'W32': [ -4752189.868, 2790743.321, -3200483.747 ],
        'W45': [ -4752088.877, 2790914.767, -3200483.747 ],
        'W64': [ -4751941.276, 2791165.342, -3200483.747 ],
        'W84': [ -4751785.907, 2791429.106, -3200483.747 ],
        'W98': [ -4751677.148, 2791613.741, -3200483.747 ],
        'W100': [ -4751661.611, 2791640.117, -3200483.747 ],
        'W102': [ -4751646.074, 2791666.493, -3200483.747 ],
        'W104': [ -4751630.537, 2791692.870, -3200483.747 ],
        'W106': [ -4751615.000, 2791719.246, -3200483.747 ],
        'W109': [ -4751591.695, 2791758.810, -3200483.747 ],
        'W110': [ -4751583.926, 2791771.999, -3200483.747 ],
        'W111': [ -4751576.158, 2791785.187, -3200483.747 ],
        'W112': [ -4751568.389, 2791798.375, -3200483.747 ],
        'W113': [ -4751560.621, 2791811.563, -3200483.747 ],
        'W124': [ -4751475.168, 2791956.633, -3200483.747 ],
        'W125': [ -4751467.399, 2791969.821, -3200483.747 ],
        'W128': [ -4751444.094, 2792009.386, -3200483.747 ],
        'W129': [ -4751436.325, 2792022.574, -3200483.747 ],
        'W140': [ -4751350.872, 2792167.644, -3200483.747 ],
        'W147': [ -4751296.492, 2792259.961, -3200483.747 ],
        'W148': [ -4751288.724, 2792273.149, -3200483.747 ],
        'W163': [ -4751172.197, 2792470.972, -3200483.747 ],
        'W168': [ -4751133.354, 2792536.913, -3200483.747 ],
        'W172': [ -4751102.281, 2792589.666, -3200483.747 ],
        'W173': [ -4751094.512, 2792602.854, -3200483.747 ],
        'W182': [ -4751024.596, 2792721.547, -3200483.747 ],
        'W189': [ -4750970.216, 2792813.865, -3200483.747 ],
        'W190': [ -4750962.448, 2792827.053, -3200483.747 ],
        'W195': [ -4750923.605, 2792892.994, -3200483.747 ],
        'W196': [ -4750915.837, 2792906.182, -3200483.747 ],
        'W392': [ -4749393.198, 2795491.050, -3200483.694 ],
        'N2': [ -4751628.291, 2791727.075, -3200457.305 ],
        'N5': [ -4751648.226, 2791738.818, -3200417.642 ],
        'N7': [ -4751661.517, 2791746.647, -3200391.200 ],
        'N11': [ -4751688.098, 2791762.304, -3200338.316 ],
        'N14': [ -4751708.034, 2791774.047, -3200298.653 ] }

    endStations = [
        { 'array': [ '6000', '6km', '3000', '3km' ],
          'stations': [ 'W2', 'W196' ] },
        { 'array': [ '1500', '1.5km' ],
          'stations': [ 'W98', 'W195' ] },
        { 'array': [ '750', '750m' ],
          'stations': [ 'W98', 'W148' ] },
        { 'array': [ '367', 'EW367', 'EW352/367' ],
          'stations': [ 'W104', 'W128' ] },
        { 'array': [ 'EW352' ],
          'stations': [ 'W102', 'W125' ] },
        { 'array': [ 'h214', 'H214' ],
          'stations': [ 'W98', 'W113', 'W104', 'N14' ] },
        { 'array': [ 'h168', 'H168' ],
          'stations': [ 'W100', 'W111', 'W104', 'N11' ] },
        { 'array': [ 'h75', 'H75' ],
          'stations': [ 'W104', 'W109', 'W104', 'N5' ] } ]

    # Search through the array.
    for s in xrange(0, len(endStations)):
        if (array in endStations[s]['array']):
            # Calculate the maximum dX, dY, dZ.
            mdX = 0
            mdY = 0
            mdZ = 0
            for i in xrange(0, len(endStations[s]['stations']) - 1):
                for j in xrange(i + 1, len(endStations[s]['stations'])):
                    dYp = abs(stationLocations[endStations[s]['stations'][i]][0] -
                              stationLocations[endStations[s]['stations'][j]][0])
                    dXp = abs(stationLocations[endStations[s]['stations'][i]][1] -
                              stationLocations[endStations[s]['stations'][j]][1])
                    dX = dXp * math.cos(cangle) - dYp * math.sin(cangle)
                    dY = dXp * math.sin(cangle) + dYp * math.cos(cangle)
                    if (dX > mdX):
                        mdX = dX
                    if (dY > mdY):
                        mdY = dY
                    dZ = abs(stationLocations[endStations[s]['stations'][i]][2] -
                             stationLocations[endStations[s]['stations'][j]][2])
                    if (dZ > mdZ):
                        mdZ = dZ
            mdX6 = 0
            mdY6 = 0
            mdZ6 = 0
            for i in xrange(0, len(endStations[s]['stations'])):
                dYp = abs(stationLocations[endStations[s]['stations'][i]][0] -
                          stationLocations['W392'][0])
                dXp = abs(stationLocations[endStations[s]['stations'][i]][1] -
                          stationLocations['W392'][1])
                dX = dXp * math.cos(cangle) - dYp * math.sin(cangle)
                dY = dXp * math.sin(cangle) + dYp * math.cos(cangle)
                if (dX > mdX6):
                    mdX6 = dX
                if (dY > mdY6):
                    mdY6 = dY
                dZ = abs(stationLocations[endStations[s]['stations'][i]][2] -
                         stationLocations['W392'][2])
                if (dZ > mdZ6):
                    mdZ6 = dZ
            return ( { 'track': { 'dX': mdX, 'dY': mdY, 'dZ': mdZ },
                       'ca06': { 'dX': mdX6, 'dY': mdY6, 'dZ': mdZ6 } } )

    # We couldn't find the appropriate maximum baseline lengths.
    raise CalcError("Baseline lengths are not available.")

def addToOutput(output, item, name, value, description, units):
    # Add some information to the JSON output object.
    if (isinstance(name, list) == False):
        output[item][name] = value
        output['description'][name] = description
        if (units is not None):
            output['units'][name] = units
    else:
        if (name[0] not in output[item]):
            output[item][name[0]] = {}
            output['description'][name[0]] = description
            if (units is not None):
                output['units'][name[0]] = units
        output[item][name[0]][name[1]] = value

def bandwidthToVelocity(lfreq, bw, restfreq):
    # Given a rest frequency in MHz, calculate the velocity span represented
    # by the specified bandwidth (MHz) starting at some low frequency (MHz).
    vr = bw * restfreq * speedoflight * mToKm / (lfreq * (lfreq + bw))
    vro = float("%.3f" % vr)
    return (vro)
