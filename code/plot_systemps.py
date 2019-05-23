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
import numpy as np
import atsenscalc_routines as sens

# This module takes the system temperatures we know about and makes
# nice plots of them, including SEFDs.

# Go through each of the bands, but first get all the efficiencies.
eff = sens.templateEfficiency()
bands = [ "16cm", "4cm", "15mm", "7mm", "3mm" ]
freqs = [ [ 1100, 3500 ], [ 3501, 12000 ], [ 13000, 27000 ], [ 28000, 51000 ],
          [ 80000, 110000 ] ]
btsys = {}
bsefd = {}
for i in xrange(0, len(bands)):
    b = bands[i]
    tsys = sens.readTsys(sens.frequencyBands[b]['tsys'],
                         freqs[i][0], freqs[i][1])
    btsys[b] = tsys
    # Get the efficiencies at each of the Tsys frequencies.
    teff = np.interp(tsys['centreFrequency'], eff['centreFrequency'],
                     eff['value'])
    # Calculate the SEFDs.
    ae = np.pi * 22.0 * 22.0 * teff
    sefd = (2.0 * 1.38064852e-23 / 1e-26) * (tsys['value'] / ae)
    bsefd[b] = { 'centreFrequency': tsys['centreFrequency'],
                 'value': sefd }

def plotter(ax, obj, band):
    f = np.array(obj[band]['centreFrequency']) / 1000.
    ax.plot(f, obj[band]['value'], '-', color="black")
    ax.set_xlim(f[0], f[-1])
    ax.set_yscale('log')

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
# 7mm.
plotter(ax2, btsys, "7mm")
# 15mm.
plotter(ax3, btsys, "15mm")
# 4cm.
plotter(ax4, btsys, "4cm")
# 16cm.
plotter(ax5, btsys, "16cm")
# All.
plotter(ax6, btsys, "3mm")
plotter(ax6, btsys, "7mm")
plotter(ax6, btsys, "15mm")
plotter(ax6, btsys, "4cm")
plotter(ax6, btsys, "16cm")
ax6.set_xlim((btsys['16cm']['centreFrequency'][0] / 1000.),
             (btsys['3mm']['centreFrequency'][-1] / 1000.))
ax6.set_xlabel('Frequency [GHz]')
fig.text(0.04, 0.5, "System Temperature [K]", va='center', rotation='vertical')
plt.savefig("tsys.png")

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

# Output the median Tsys and SEFD for each band.
print "Band  Tsys    SEFD1   SEFD2   SEFD3   SEFD4   SEFD5   SEFD6"
for b in bands:
    mdtsys = np.median(btsys[b]['value'])
    mdsefd = np.median(bsefd[b]['value'])
    if b != "3mm":
        print "%4s  %-7.1f %-7.1f %-7.1f %-7.1f %-7.1f %-7.1f %-7.1f" % (b, mdtsys, mdsefd, (mdsefd / 2.),
                                                                         (mdsefd / 3.), (mdsefd / 4.),
                                                                         (mdsefd / 5.), (mdsefd / 6.))
    else:
        print "%4s  %-7.1f %-7.1f %-7.1f %-7.1f %-7.1f %-7.1f NA" % (b, mdtsys, mdsefd, (mdsefd / 2.),
                                                                     (mdsefd / 3.), (mdsefd / 4.),
                                                                     (mdsefd / 5.))
        
