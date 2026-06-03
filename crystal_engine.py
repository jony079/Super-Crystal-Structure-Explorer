# crystal_engine.py
import numpy as np
import streamlit as st
import math
from metrics import profile_performance

@st.cache_data
@profile_performance
def d_spacing(a, h, k, l, crystal_type="SC", c=None):
    if h == 0 and k == 0 and l == 0:
        return None
    if crystal_type in ["SC", "BCC", "FCC"]:
        return a / np.sqrt(h**2 + k**2 + l**2)
    elif crystal_type == "HCP":
        if c is None:
            return None
        # True HCP Geometrical plane spacing equation
        term1 = (4.0 / 3.0) * ((h**2 + h*k + k**2) / (a**2))
        term2 = (l**2) / (c**2)
        if term1 + term2 == 0:
            return None
        return 1.0 / np.sqrt(term1 + term2)
    return None

@st.cache_data
@profile_performance
def xrd_peaks(crystal_type, a, wavelength, two_theta_max=120, c=None):
    """
    Optimized XRD Simulator with systematic absence checks 
    and built-in caching to kill the 2,197 iteration rerun overhead.
    """
    peaks = []
    # Vectorized loop lookup zone (-6 to 6)
    for h in range(-6, 7):
        for k in range(-6, 7):
            for l in range(-6, 7):
                if h == 0 and k == 0 and l == 0:
                    continue
                
                # Check Systematic Absences / Selection Rules
                allowed = False
                if crystal_type == "SC":
                    allowed = True
                elif crystal_type == "BCC":
                    if (h + k + l) % 2 == 0:
                        allowed = True
                elif crystal_type == "FCC":
                    if (h%2 == k%2 == l%2): # Unmixed indices
                        allowed = True
                elif crystal_type == "HCP":
                    # REAL HCP Reflection Conditions: 
                    # Forbidden if h + 2k = 3n AND l is odd
                    if not ((h + 2*k) % 3 == 0 and l % 2 != 0):
                        allowed = True
                
                if not allowed:
                    continue
                
                d = d_spacing(a, h, k, l, crystal_type, c)
                if d is None:
                    continue
                
                # Bragg's Law Validation
                sin_theta = wavelength / (2 * d)
                if sin_theta < 1.0:
                    theta = np.arcsin(sin_theta)
                    two_theta = np.degrees(theta) * 2
                    if two_theta <= two_theta_max:
                        # Structure factor relative intensity calculations
                        if crystal_type == "HCP":
                            # HCP Basis calculation logic: |F|^2 = 4*cos^2(pi * (h + 2k/3 + l/2))
                            phase_angle = np.pi * ((h + 2*k)/3.0 + l/2.0)
                            f_sq = 4 * (np.cos(phase_angle) ** 2)
                            if f_sq < 1e-3: continue
                            intensity = (f_sq / 4.0) * 100
                        else:
                            intensity = 100.0 # Normalized baseline for cubics
                            
                        label = f"({h}{k}{l})"
                        
                        # Filter out duplicate overlapping peaks
                        duplicate = False
                        for p in peaks:
                            if abs(p[0] - two_theta) < 0.1:
                                duplicate = True
                                break
                        if not duplicate:
                            peaks.append((two_theta, intensity, label))
                            
    peaks.sort(key=lambda x: x[0])
    return peaks

# Keep other small utility functions basic and light
def atomic_radius(a, ctype, c=None):
    if ctype == "SC": return a / 2
    elif ctype == "BCC": return (a * np.sqrt(3)) / 4
    elif ctype == "FCC": return (a * np.sqrt(2)) / 4
    elif ctype == "HCP": return a / 2
    return 0.0

def packing_factor(ctype):
    return {"SC": 0.524, "BCC": 0.680, "FCC": 0.740, "HCP": 0.740}.get(ctype, 0.0)

def coordination_number(ctype):
    return {"SC": 6, "BCC": 8, "FCC": 12, "HCP": 12}.get(ctype, 0)

def close_packed_direction(ctype):
    return {"SC": "[100]", "BCC": "[111]", "FCC": "[110]", "HCP": "[11-20]"}.get(ctype, "N/A")

def atoms_per_unit_cell(ctype):
    return {"SC": 1, "BCC": 2, "FCC": 4, "HCP": 6}.get(ctype, 0)

def structure_factor(ctype, h, k, l):
    if ctype == "SC": return 1, 1.0, "Allowed", 1
    elif ctype == "BCC":
        allowed = (h + k + l) % 2 == 0
        return (4, 1.0, "Allowed", 2) if allowed else (0, 0.0, "Forbidden", 2)
    elif ctype == "FCC":
        allowed = (h%2 == k%2 == l%2)
        return (16, 1.0, "Allowed", 4) if allowed else (0, 0.0, "Forbidden", 4)
    else: # HCP
        phase = np.pi * ((h + 2*k)/3.0 + l/2.0)
        f_sq = 4 * (np.cos(phase) ** 2)
        return f_sq, f_sq/4.0, "Allowed" if f_sq > 0.001 else "Forbidden", 2
