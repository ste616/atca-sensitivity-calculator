######################################################################
# The ATCA Sensitivity Calculator
# Atmospheric refraction calculation routines.
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

def refdry(nu, T, Pdry, Pvap):
    # From Miriad: Determine the complex refractivity of the dry components
    # of the atmosphere.
    #
    # Input:
    #  nu = observing frequency (Hz)
    #  T = temperature (K)
    #  Pdry = partial pressure of dry components (Pa)
    #  Pvap = partial pressure of water vapour (Pa)

    # Table of microwave oxygen lines and their parameters.
    nu0 = [ 49.452379, 49.962257, 50.474238, 50.987748, 51.503350, 52.021409,
            52.542393, 53.066906, 53.595748, 54.129999, 54.671157, 55.221365,
            55.783800, 56.264777, 56.363387, 56.968180, 57.612481, 58.323874,
            58.446589, 59.164204, 59.590982, 60.306057, 60.434775, 61.150558,
            61.800152, 62.411212, 62.486253, 62.997974, 63.568515, 64.127764,
            64.678900, 65.224067, 65.764769, 66.302088, 66.836827, 67.369595,
            67.900862, 68.431001, 68.960306, 69.489021, 70.017342, 18.750341,
            68.498350, 24.763120, 87.249370, 15.393150, 73.838730, 34.145330 ]
    a1 = [    0.12E-6,    0.34E-6,    0.94E-6,    2.46E-6,    6.08E-6,   14.14E-6,
              31.02E-6,   64.10E-6,  124.70E-6,  228.00E-6,  391.80E-6,  631.60E-6,
              953.50E-6,  548.90E-6, 1344.00E-6, 1763.00E-6, 2141.00E-6, 2386.00E-6,
              1457.00E-6, 2404.00E-6, 2112.00E-6, 2124.00E-6, 2461.00E-6, 2504.00E-6,
              2298.00E-6, 1933.00E-6, 1517.00E-6, 1503.00E-6, 1087.00E-6,  733.50E-6,
              463.50E-6,  274.80E-6,  153.00E-6,   80.09E-6,   39.46E-6,   18.32E-6,
              8.01E-6,    3.30E-6,    1.28E-6,    0.47E-6,    0.16E-6,  945.00E-6,
              67.90E-6,  638.00E-6,  235.00E-6,   99.60E-6,  671.00E-6,  180.00E-6 ]
    a2 = [  11.830, 10.720,  9.690,  8.690,  7.740,  6.840,
            6.000,  5.220,  4.480,  3.810,  3.190,  2.620,
            2.115,  0.010,  1.655,  1.255,  0.910,  0.621,
            0.079,  0.386,  0.207,  0.207,  0.386,  0.621,
            0.910,  1.255,  0.078,  1.660,  2.110,  2.620,
            3.190,  3.810,  4.480,  5.220,  6.000,  6.840,
            7.740,  8.690,  9.690, 10.720, 11.830,  0.000,
            0.020,  0.011,  0.011,  0.089,  0.079,  0.079 ]
    a3 = [   8.40E-3,  8.50E-3,  8.60E-3,  8.70E-3,  8.90E-3,  9.20E-3,
             9.40E-3,  9.70E-3, 10.00E-3, 10.20E-3, 10.50E-3, 10.79E-3,
             11.10E-3, 16.46E-3, 11.44E-3, 11.81E-3, 12.21E-3, 12.66E-3,
             14.49E-3, 13.19E-3, 13.60E-3, 13.82E-3, 12.97E-3, 12.48E-3,
             12.07E-3, 11.71E-3, 14.68E-3, 11.39E-3, 11.08E-3, 10.78E-3,
             10.50E-3, 10.20E-3, 10.00E-3,  9.70E-3,  9.40E-3,  9.20E-3,
             8.90E-3,  8.70E-3,  8.60E-3,  8.50E-3,  8.40E-3, 15.92E-3,
             19.20E-3, 19.16E-3, 19.20E-3, 18.10E-3, 18.10E-3, 18.10E-3 ]
    a4 = [  0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.6, 0.6, 0.6, 0.6, 0.6, 0.6 ]
    a5 = [  5.60E-3,  5.60E-3,  5.60E-3,  5.50E-3,  5.60E-3,  5.50E-3,
            5.70E-3,  5.30E-3,  5.40E-3,  4.80E-3,  4.80E-3,  4.17E-3,
            3.75E-3,  7.74E-3,  2.97E-3,  2.12E-3,  0.94E-3, -0.55E-3,
            5.97E-3, -2.44E-3,  3.44E-3, -4.13E-3,  1.32E-3, -0.36E-3,
            -1.59E-3, -2.66E-3, -4.77E-3, -3.34E-3, -4.17E-3, -4.48E-3,
            -5.10E-3, -5.10E-3, -5.70E-3, -5.50E-3, -5.90E-3, -5.60E-3,
            -5.80E-3, -5.70E-3, -5.60E-3, -5.60E-3, -5.60E-3, -0.44E-3,
            0.00E00,  0.00E00,  0.00E00,  0.00E00,  0.00E00,  0.00E00 ]
    a6 = [  1.7,  1.7,  1.7,  1.7,  1.8,  1.8,
            1.8,  1.9,  1.8,  2.0,  1.9,  2.1,
            2.1,  0.9,  2.3,  2.5,  3.7, -3.1,
            0.8,  0.1,  0.5,  0.7, -1.0,  5.8,
            2.9,  2.3,  0.9,  2.2,  2.0,  2.0,
            1.8,  1.9,  1.8,  1.8,  1.7,  1.8,
            1.7,  1.7,  1.7,  1.7,  1.7,  0.9,
            1.0,  1.0,  1.0,  1.0,  1.0,  1.0 ]

    # Convert to the units of Liebe.
    theta = 300.0 / T
    e = 0.001 * Pvap
    p = 0.001 * Pdry
    f = nu * 1e-9

    ap = 1.4e-10 * (1.0 - 1.2e-5 * f ** 1.5)
    gamma0 = 5.6e-3 * (p + 1.1 * e) * theta ** 0.8
    nr = 2.588 * p * theta + 3.07e-4 * (1.0 / (1.0 + (f / gamma0) ** 2) - 1.0) * p * theta * theta
    ni = (2.0 * 3.07e-4 / (gamma0 * (1.0 + (f / gamma0) ** 2) * (1.0 + (f / 60.0) ** 2)) +
          ap * p * theta ** 2.5) * f * p * theta * theta

    # Sum the contributions of the lines.
    for i in xrange(0, len(nu0)):
        S = a1[i] * p * theta ** 3 * math.exp(a2[i] * (1.0 - theta))
        gamma = a3[i] * (p * theta ** (0.8 - a4[i])) + 1.1 * e * theta
        delta = a5[i] * p * theta ** a6[i]
        x = (nu0[i] - f) * (nu0[i] - f) + gamma * gamma
        y = (nu0[i] + f) * (nu0[i] + f) + gamma * gamma
        z = (nu0[i] + gamma * gamma / nu0[i])
        nr = nr + S * ((z - f) / x + (z + f) / y - 2 / nu0[i] + delta *
                       (1.0 / x - 1.0 / y) * gamma * f / nu0[i])
        ni = ni + S * ((1.0 / x + 1.0 / y) * gamma * f / nu0[i] - delta *
                       ((nu0[i] - f) / x + (nu0[i] + f) / y) * f / nu0[i])

    # Return the result.
    return complex(nr, ni)

def refvap(nu, T, Pdry, Pvap):
    # From Miriad; Determine the complex refractivity of the water vapour monomers.
    #
    # Inputs:
    #  nu = observating frequency (Hz)
    #  T = temperature (K)
    #  Pdry = partial pressure of dry components (Pa)
    #  Pvap = partial pressure of water vapour (Pa)

    # Table of the microwave water lines.
    mnu0 = [  22.235080,  67.813960, 119.995940, 183.310117, 321.225644, 325.152919,
              336.187000, 380.197372, 390.134508, 437.346667, 439.150812, 443.018295,
              448.001075, 470.888947, 474.689127, 488.491133, 503.568532, 504.482692,
              556.936002, 620.700807, 658.006500, 752.033227, 841.073593, 859.865000,
              899.407000, 902.555000, 906.205524, 916.171582, 970.315022, 987.926764 ]
    b1 = [   0.1090,  0.0011,  0.0007,   2.3000,  0.0464,  1.5400,
             0.0010, 11.9000,  0.0044,   0.0637,  0.9210,  0.1940,
             10.6000,  0.3300,  1.2800,   0.2530,  0.0374,  0.0125,
             510.0000,  5.0900,  0.2740, 250.0000,  0.0130,  0.1330,
             0.0550,  0.0380,  0.1830,   8.5600,  9.1600, 138.000 ]
    b2 = [ 2.143, 8.730, 8.347, 0.653, 6.156, 1.515,
           9.802, 1.018, 7.318, 5.015, 3.561, 5.015,
           1.370, 3.561, 2.342, 2.814, 6.693, 6.693,
           0.114, 2.150, 7.767, 0.336, 8.113, 7.989,
           7.845, 8.360, 5.039, 1.369, 1.842, 0.178 ]
    b3 = [ 27.84E-3, 27.60E-3, 27.00E-3, 28.35E-3, 21.40E-3, 27.00E-3,
           26.50E-3, 27.60E-3, 19.00E-3, 13.70E-3, 16.40E-3, 14.40E-3,
           23.80E-3, 18.20E-3, 19.80E-3, 24.90E-3, 11.50E-3, 11.90E-3,
           30.00E-3, 22.30E-3, 30.00E-3, 28.60E-3, 14.10E-3, 28.60E-3,
           28.60E-3, 26.40E-3, 23.40E-3, 25.30E-3, 24.00E-3, 28.60E-3 ]

    # Convert to the units of Liebe.
    theta = 300.0 / T
    e = 0.001 * Pvap
    p = 0.001 * Pdry
    f = nu * 1e-9

    nr = 2.39 * e * theta + 41.6 * e * theta * theta + 6.47e-6 * f ** 2.05 * e * theta ** 2.4
    ni = (0.915 * 1.40e-6 * p + 5.41e-5 * e * theta * theta * theta) * f * e * theta ** 2.5

    # Sum the contributions of the lines.
    for i in xrange(0, len(mnu0)):
        S = b1[i] * e * theta ** 3.5 * math.exp(b2[i] * (1.0 - theta))
        gamma = b3[i] * (p * theta ** 0.8 + 4.80 * e * theta)
        x = (mnu0[i] - f) * (mnu0[i] - f) + gamma * gamma
        y = (mnu0[i] + f) * (mnu0[i] + f) + gamma * gamma
        z = (mnu0[i] + gamma * gamma / mnu0[i])
        nr = nr + S * ((z - f) / x + (z + f) / y - 2 / mnu0[i])
        ni = ni + S * ((1.0 / x + 1.0 / y) * gamma * f / mnu0[i])

    # Return the result.
    return complex(nr, ni)
    
def pvapsat(T):
    # From Miriad; Determine the saturation pressure of water vapour.
    # Input:
    #  T = temperature (K)
    #
    # Output:
    #  vapour saturation pressure (Pa)

    if (T > 215):
        theta = 300.0 / T
        return 1e5 / (41.51 * (theta ** -5) * (10 **(9.384 * theta - 10.0)))
    else:
        return 0.0

def refract(t, pdry, pvap, z, n, nu, T0, el):
    # From Miriad; Compute refractive index for an atmosphere.
    # Determine the sky brightness and excess path lengths for a parallel
    # slab atmosphere. Liebe's model (1985) is used to determine the complex
    # refractive index of air.
    #
    # Input:
    #  n = the number of atmospheric layers.
    #  t = temperature of the layers. T[0] is the temperature at the lowest
    #      layer (K)
    #  Pdry = partial pressure of the dry components (Pa)
    #  Pvap = partial pressure of the water vapour components (Pa)
    #  z = height of the layer.
    #  nu = frequency of interest (Hz)
    #  T0 = astronomical brightness temperature (K)
    #  el = elevation angle of the source above the atmosphere (rad)
    #
    # Output:
    #  { 'Tb' = brightness temperature (K),
    #    'tau' = opacity (nepers)
    #    'Ldry' = excess path, dry component (m)
    #    'Lvap' = excess path, water vapour component (m) }

    # Some constants.
    HMKS = 6.6260755e-34 # Planck constant, J.s
    KMKS = 1.380658e-23 # Boltzmann constant, J/K
    CMKS = 299792458 # Speed of light, m/s

    tau = 0.0
    Tb = HMKS * nu / (KMKS * (math.exp(HMKS * nu / (KMKS * T0)) - 1))
    Ldry = 0.0
    Lvap = 0.0

    snell = math.sin(el)
    for i in xrange(n, 0, -1):
        if (i == 1):
            dz = 0.5 * (z[1] - z[0])
        elif (i == n):
            dz = 0.5 * (z[n] - z[n - 1])
        else:
            dz = 0.5 * (z[i + 1] - z[i - 1])
        Ndry = refdry(nu, t[i], pdry[i], pvap[i])
        Nvap = refvap(nu, t[i], pdry[i], pvap[i])
        nr = 1 + (Ndry.real + Nvap.real) * 1e-6
        ni = (Ndry.imag + Nvap.imag) * 1e-6
        l = dz * nr / math.sqrt(nr * nr + (snell * snell) - 1.0)
        dtau = l * 4.0 * math.pi * nu / CMKS * ni
        Tb = (Tb - t[i]) * math.exp(-dtau) + t[i]
        tau = tau + dtau
        Ldry = Ldry + l * Ndry.real * 1e-6
        Lvap = Lvap + l * Nvap.real * 1e-6

    return { 'Tb': Tb, 'tau': tau, 'Ldry': Ldry, 'Lvap': Lvap }

def calcOpacity(freq, el, t0, p0, h0):
    # From Miriad; Compute sky brightness and opacity of a model atmosphere.
    # Returns the transmissivity of the atmosphere given frequency, elevation
    # angle and meteorological data. This uses a simple model of the atmosphere
    # and Liebe's model (1985) of the complex refractive index of air.
    # Input:
    #  freq = frequency (Hz)
    #  el = elevation angle (radians)
    #  t0,p0,h0 = Met data; observatory temperature, pressure and humidity
    #             (K, Pa, fraction)
    # Output:
    #  { 'fac' = transmissivity (fraction between 0 and 1)
    #    'Tb' = sky brightness temperature (K) }

    # Atmospheric parameters.
    M = 28.96e-3
    R = 8.314
    Mv = 18e-3
    rho0 = 1e3
    g = 9.81

    # d = temperature lapse rate (K/m)
    d = 0.0065
    # z0 = water vapour scale height (m)
    z0 = 1540.0
    # zmax = max altitude of model atmosphere (m)
    zmax = 10000.0

    # Generate a model of the atmosphere - T is temperature, Pdry is
    # partial pressure of "dry" constituents, Pvap is the partial
    # pressure of the water vapour.
    N = 50 # Number of iterations through the atmosphere in height
    z = []
    T = []
    Pvap = []
    Pdry = []
    fac = []
    Tb = []
    tau = []
    ofreq = []
    for i in xrange(0, (N + 1)):
        zd = float(i) * zmax / float(N)
        z.append(zd)
        T.append(t0 / (1 + d / t0 * zd))
        P = p0 * math.exp(-1.0 * M * g / (R * t0) * (zd + 0.5 * d * zd * zd / t0))
        Pvap.append(min(h0 * math.exp(-1.0 * zd / z0) * pvapsat(T[0]),
                        pvapsat(T[i])))
        Pdry.append(P - Pvap[i])

    # Determine the transmissivity and sky brightness.
    for i in xrange(0, len(freq)):
        resref = refract(T, Pdry, Pvap, z, N, freq[i], 2.7, el)
        fac.append(math.exp(-1.0 * resref['tau']))
        Tb.append(resref['Tb'])
        tau.append(resref['tau'])
        ofreq.append(freq[i])

    return { 'fac': fac, 'Tb': Tb, 'tau': tau, 'freq': ofreq }
