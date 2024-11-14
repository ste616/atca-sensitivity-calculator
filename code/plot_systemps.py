######################################################################
# The ATCA Sensitivity Calculator
# System temperature plotters.
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

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import atsenscalc_routines as sens
import refract as refract
import math

# This module takes the system temperatures we know about and makes
# nice plots of them, including SEFDs.

# Go through each of the bands, but first get all the efficiencies.
eff = sens.templateEfficiency()
bands = [ "16cm", "4cm", "15mm", "7mm", "3mm" ]
freqs = [ [ 1100, 3500 ], [ 3501, 12000 ], [ 13000, 27000 ], [ 28000, 51000 ],
          [ 80000, 110000 ] ]
wholeBands = [ [ 2100.0, 2000.0 ], [ 8000.0, 8000.0 ], [ 20000.0, 10000.0 ], [ 39500.0, 23000.0 ],
               [ 95000.0, 30000.0 ] ]
btsys = {}
bsefd = {}
ctsys = {}
compsens = {}
speed = {}
for i in range(0, len(bands)):
    b = bands[i]
    print("reading band %s" % b)
    tsys = sens.readTsys(sens.frequencyBands[b]['tsys'],
                         freqs[i][0], freqs[i][1])
    btsys[b] = tsys
    # Get the efficiencies at each of the Tsys frequencies.
    teff = np.interp(tsys['centreFrequency'], eff['centreFrequency'],
                     eff['value'])
    # Calculate the SEFDs.
    ae = np.pi * 11.0 * 11.0 * teff
    ctsys[b] = { 'centreFrequency': tsys['centreFrequency'],
                 'value': tsys['value'] / teff }
    sefd = (2.0 * 1.38064852e-23 / 1e-26) * (tsys['value'] / ae)
    bsefd[b] = { 'centreFrequency': tsys['centreFrequency'],
                 'value': sefd }
    # Do it with the templating.
    cont = sens.makeTemplate(wholeBands[i][0], wholeBands[i][1], 50.0)
    lowfreq = (cont['centreFrequency'][0] - 25.0)
    highfreq = (cont['centreFrequency'][-1] + 25.0)
    sens.templateFill(tsys, cont)
    eff = sens.makeTemplate(wholeBands[i][0], wholeBands[i][1], 50.0)
    effmt = sens.templateEfficiency()
    sens.templateFill(effmt, eff)
    opac = sens.makeTemplate(wholeBands[i][0], wholeBands[i][1], 50.0)
    atemp = sens.makeTemplate(wholeBands[i][0], wholeBands[i][1], 50.0)
    pwv = sens.fillAtmosphereTemplate(opac, atemp, (273.15 + 21.8), 98700.0, 0.7)
    effArea = (5 * math.pi * 11.0 * 11.0) * eff['value']
    effTemp = (cont['value'] + atemp['value'] + 2.73 +
               25.2 * np.power((408 / cont['centreFrequency']), 2.75))
    quantTemp = 4.79924466e-11 * 1.0e6 * cont['centreFrequency'] / effTemp
    effTempx = effTemp * quantTemp / (np.exp(quantTemp) - 1)
    sysTemp = effTempx / np.exp(opac['fac'])
    compsens[b] = { 'centreFrequency': cont['centreFrequency'],
                    'value': effArea / sysTemp }
    wavel = 299792458.0 / (1.0e6 * cont['centreFrequency'])
    effFOV = 2340.0 * np.power((wavel / 22.0), 2)
    speed[b] = { 'centreFrequency': cont['centreFrequency'],
                 'value': (np.power(compsens[b]['value'], 2) * effFOV) }

def tickthinner_y(ax):
    for n, label in enumerate(ax.yaxis.get_ticklabels()):
        if n % 2 != 0:
            label.set_visible(False)
    
def plotter(ax, obj, band):
    f = np.array(obj[band]['centreFrequency']) / 1000.
    ax.plot(f, obj[band]['value'], '-', color="black")
    ax.set_xlim(f[0], f[-1])
    #ax.set_yscale('log')

def splotter(ax, obj, band, no6=False):
    f = np.array(obj[band]['centreFrequency']) / 1000.
    ax.plot(f, obj[band]['value'], '-', color="black")
    ax.plot(f, (obj[band]['value'] / 2.), '-', color='purple')
    ax.plot(f, (obj[band]['value'] / 3.), '-', color='blue')
    ax.plot(f, (obj[band]['value'] / 4.), '-', color='green')
    ax.plot(f, (obj[band]['value'] / 5.), '-', color='orange')
    if not no6:
        ax.plot(f, (obj[band]['value'] / 6.), '-', color='red')
    ax.set_xlim(f[0], f[-1])
    ax.set_yscale('log')
    
# Make the plots.
plt.clf()
fig, (ax1, ax2, ax3, ax4, ax5, ax6) = plt.subplots(6, 1)
fig.subplots_adjust(hspace=0.5)
# Top plot is 3mm.
plotter(ax1, btsys, "3mm")
tickthinner_y(ax1)
# 7mm.
plotter(ax2, btsys, "7mm")
tickthinner_y(ax2)
# 15mm.
plotter(ax3, btsys, "15mm")
tickthinner_y(ax3)
# 4cm.
plotter(ax4, btsys, "4cm")
tickthinner_y(ax4)
# 16cm.
plotter(ax5, btsys, "16cm")
tickthinner_y(ax5)
# All.
plotter(ax6, btsys, "3mm")
plotter(ax6, btsys, "7mm")
plotter(ax6, btsys, "15mm")
plotter(ax6, btsys, "4cm")
plotter(ax6, btsys, "16cm")
ax6.set_xlim((btsys['16cm']['centreFrequency'][0] / 1000.),
             (btsys['3mm']['centreFrequency'][-1] / 1000.))
ax6.set_xlabel('Frequency [GHz]')
ax6.set_yscale('log')
ax6.yaxis.set_major_formatter(mtick.ScalarFormatter())
fig.text(0.04, 0.5, "System Temperature [K]", va='center', rotation='vertical')
plt.savefig("tsys.png", dpi=300)

# A Tsys plot compensating for efficiency.
plt.clf()
fig, (ax1, ax2, ax3, ax4, ax5, ax6) = plt.subplots(6, 1)
fig.subplots_adjust(hspace=0.5)
# Top plot is 3mm.
plotter(ax1, ctsys, "3mm")
# 7mm.
plotter(ax2, ctsys, "7mm")
# 15mm.
plotter(ax3, ctsys, "15mm")
# 4cm.
plotter(ax4, ctsys, "4cm")
# 16cm.
plotter(ax5, ctsys, "16cm")
# All.
plotter(ax6, ctsys, "3mm")
plotter(ax6, ctsys, "7mm")
plotter(ax6, ctsys, "15mm")
plotter(ax6, ctsys, "4cm")
plotter(ax6, ctsys, "16cm")
ax6.set_xlim((ctsys['16cm']['centreFrequency'][0] / 1000.),
             (ctsys['3mm']['centreFrequency'][-1] / 1000.))
ax6.set_xlabel('Frequency [GHz]')
fig.text(0.04, 0.5, "System Temperature / Eff. [K]", va='center', rotation='vertical')
plt.savefig("tsys_div_eff.png")


plt.clf()
fig, (ax1, ax2, ax3, ax4, ax5, ax6) = plt.subplots(6, 1)
fig.subplots_adjust(hspace=0.5)
# Top plot is 3mm.
splotter(ax1, bsefd, "3mm", True)
# 7mm.
splotter(ax2, bsefd, "7mm")
# 15mm.
splotter(ax3, bsefd, "15mm")
# 4cm.
splotter(ax4, bsefd, "4cm")
# 16cm.
splotter(ax5, bsefd, "16cm")
# All.
splotter(ax6, bsefd, "3mm")
splotter(ax6, bsefd, "7mm")
splotter(ax6, bsefd, "15mm")
splotter(ax6, bsefd, "4cm")
splotter(ax6, bsefd, "16cm")
ax6.set_xlim((bsefd['16cm']['centreFrequency'][0] / 1000.),
             (bsefd['3mm']['centreFrequency'][-1] / 1000.))
ax6.set_xlabel('Frequency [GHz]')
fig.text(0.04, 0.5, "SEFD [Jy]", va='center', rotation='vertical')
plt.savefig("sefd.png")

plt.clf()
fig, (ax1, ax2, ax3, ax4, ax5, ax6) = plt.subplots(6, 1)
fig.subplots_adjust(hspace=0.5)
# Top plot is 3mm.
plotter(ax1, bsefd, "3mm")
# 7mm.
plotter(ax2, bsefd, "7mm")
# 15mm.
plotter(ax3, bsefd, "15mm")
# 4cm.
plotter(ax4, bsefd, "4cm")
# 16cm.
plotter(ax5, bsefd, "16cm")
# All.
plotter(ax6, bsefd, "3mm")
plotter(ax6, bsefd, "7mm")
plotter(ax6, bsefd, "15mm")
plotter(ax6, bsefd, "4cm")
plotter(ax6, bsefd, "16cm")
ax6.set_xlim((bsefd['16cm']['centreFrequency'][0] / 1000.),
             (bsefd['3mm']['centreFrequency'][-1] / 1000.))
ax6.set_xlabel('Frequency [GHz]')
fig.text(0.04, 0.5, "SEFD [Jy]", va='center', rotation='vertical')
plt.savefig("single_sefd.png")

plt.clf()
fig, ax = plt.subplots(1, 1)
plotter(ax, bsefd, "16cm")
ax.set_xlabel('Frequency [GHz]')
fig.text(0.04, 0.5, "SEFD [Jy]", va='center', rotation='vertical')
plt.savefig("sefd_16cm.png")

# The sensitivity for SKA comparison.
plt.clf()
fig, ax = plt.subplots(1, 1)
plotter(ax, compsens, "16cm")
plotter(ax, compsens, "4cm")
plotter(ax, compsens, "15mm")
plotter(ax, compsens, "7mm")
plotter(ax, compsens, "3mm")
ax.set_xlim(0.03, 130.0)
ax.set_ylim(1, 8e4)
ax.set_xlabel('Frequency [GHz]')
ax.set_xscale('log')
ax.set_yscale('log')
fig.text(0.04, 0.5, "Sensitivity", va='center', rotation='vertical')
plt.savefig("skacomp_sens.png")

# The survey speed for SKA comparison.
plt.clf()
fig, ax = plt.subplots(1, 1)
plotter(ax, speed, "16cm")
plotter(ax, speed, "4cm")
plotter(ax, speed, "15mm")
plotter(ax, speed, "7mm")
plotter(ax, speed, "3mm")
ax.set_xlim(0.03, 130.0)
ax.set_ylim(0.01, 1.1e10)
ax.set_xlabel('Frequency [GHz]')
ax.set_xscale('log')
ax.set_yscale('log')
fig.text(0.04, 0.5, "Survey Speed", va='center', rotation='vertical')
plt.savefig("skacomp_surveyspeed.png")

# Output the median Tsys and SEFD for each band.
print ("Band  Tsys    Tsys/e  SEFD1   SEFD2   SEFD3   SEFD4   SEFD5   SEFD6")
for b in bands:
    mdtsys = np.median(btsys[b]['value'])
    mdsefd = np.median(bsefd[b]['value'])
    mdetsys = np.max(ctsys[b]['value'])
    if b != "3mm":
        print ("%4s  %-7.1f %-7.1f %-7.1f %-7.1f %-7.1f %-7.1f %-7.1f %-7.1f" % (b, mdtsys, mdetsys, mdsefd,
                                                                                 (mdsefd / 2.),
                                                                                 (mdsefd / 3.), (mdsefd / 4.),
                                                                                 (mdsefd / 5.), (mdsefd / 6.)))
    else:
        print ("%4s  %-7.1f %-7.1f %-7.1f %-7.1f %-7.1f %-7.1f %-7.1f NA" % (b, mdtsys, mdetsys, mdsefd,
                                                                             (mdsefd / 2.),
                                                                             (mdsefd / 3.), (mdsefd / 4.),
                                                                             (mdsefd / 5.)))
        
# Output the numbers for sensitivity and survey speed.
with open("atca_comparison_ska.dat", "w") as fp:
    fp.write("# Freq(GHz)  Sensitivity   SurveySpeed\n")
    for b in bands:
        for i in range(0, len(compsens[b]['centreFrequency'])):
            fp.write("%.3f  %.3f  %.3f\n" % ((compsens[b]['centreFrequency'][i] / 1000.0),
                                             compsens[b]['value'][i], speed[b]['value'][i]))
