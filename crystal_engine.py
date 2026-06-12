# crystal_engine.py
import numpy as np
import streamlit as st
from metrics import profile_performance

# ==================================================
# Crystal Basis Definitions
# ==================================================

BASIS_MAP = {
    "SC": [
        (0.0, 0.0, 0.0)
    ],
    "BCC": [
        (0.0, 0.0, 0.0),
        (0.5, 0.5, 0.5)
    ],
    "FCC": [
        (0.0, 0.0, 0.0),
        (0.5, 0.5, 0.0),
        (0.5, 0.0, 0.5),
        (0.0, 0.5, 0.5)
    ],
    "HCP": [
        (0.0, 0.0, 0.0),
        (1.0/3.0, 2.0/3.0, 0.5)
    ]
}

# ==================================================
# d-spacing
# ==================================================

@profile_performance
@st.cache_data
def d_spacing(a, h, k, l, crystal_type="SC", c=None):
    """
    Calculate interplanar spacing dynamically.
    """
    if (h, k, l) == (0, 0, 0) or a <= 0:
        return None

    if crystal_type in ("SC", "BCC", "FCC"):
        denominator = h**2 + k**2 + l**2
        if denominator <= 0:
            return None
        return float(a / np.sqrt(denominator))

    if crystal_type == "HCP":
        if c is None or c <= 0:
            return None
        # HCP d-spacing standard formula
        term1 = (4.0 / 3.0) * ((h**2 + h*k + k**2) / (a**2))
        term2 = (l**2) / (c**2)
        denominator = term1 + term2
        if denominator <= 0:
            return None
        return float(1.0 / np.sqrt(denominator))

    return None

# ==================================================
# Structure Factor
# ==================================================

@profile_performance
@st.cache_data
def structure_factor(ctype, h, k, l):
    """
    Structure factor calculation using pure vector phase summation.
    Assumes atomic scattering factor: f = 1
    """
    basis = BASIS_MAP.get(ctype)
    if basis is None:
        return 0.0, 0.0, "Unknown", 0

    F = sum(
        np.exp(2j * np.pi * (h*x + k*y + l*z))
        for x, y, z in basis
    )

    F_sq = float(abs(F) ** 2)
    n_basis = len(basis)
    F_rel = float(F_sq / (n_basis ** 2))

    # Analytical floating-point boundary thresholding
    if F_rel < 1e-2:
        status = "Forbidden"
    elif F_rel > 0.99:
        status = "Allowed"
    else:
        status = "Partial"

    return F_sq, F_rel, status, n_basis

# ==================================================
# XRD Peak Simulation
# ==================================================
@profile_performance
@st.cache_data
def xrd_peaks(crystal_type, a, wavelength, two_theta_max=120, c=None):
    """
    Simulate diffraction peaks and return raw structured data.
    No UI-bound text hacking inside the mathematical core.
    """
    peaks = []

    for h in range(-5, 6):
        for k in range(-5, 6):
            for l in range(-5, 6):
                if (h, k, l) == (0, 0, 0):
                    continue

                # Structural absences filter from engine
                F_sq, F_rel, status, _ = structure_factor(crystal_type, h, k, l)
                if status == "Forbidden":
                    continue

                d = d_spacing(a, h, k, l, crystal_type, c)
                if d is None:
                    continue

                sin_theta = wavelength / (2.0 * d)
                if sin_theta >= 1.0 or sin_theta <= 0.0:
                    continue

                theta = np.arcsin(sin_theta)
                two_theta = float(np.degrees(theta) * 2.0)

                if two_theta > two_theta_max:
                    continue

                intensity = float(F_rel * 100.0)
                
                # Standard physical label mapping
                if crystal_type == "HCP":
                    i = -(h + k)
                    label = f"({h} {k} {i} {l})"
                else:
                    label = f"({h} {k} {l})"

                # Check for duplicate peak angles
                duplicate = False
                for p in peaks:
                    if abs(p["two_theta"] - two_theta) < 0.1:
                        duplicate = True
                        if intensity > p["intensity"]:
                            p["intensity"] = intensity
                            p["label"] = label
                            p["h"], p["k"], p["l"] = h, k, l
                        break

                if not duplicate and intensity > 0.1:
                    # Explicit structured contract instead of ambiguous tuple
                    peaks.append({
                        "two_theta": two_theta,
                        "intensity": intensity,
                        "label": label,
                        "h": h,
                        "k": k,
                        "l": l
                    })

    # Sort dictionary items chronologically by angle
    peaks.sort(key=lambda x: x["two_theta"])
    return peaks

# ==================================================
# Material Property Core Helpers
# ==================================================

def atomic_radius(a, ctype, c=None):
    if a <= 0: return 0.0
    return {
        "SC": a / 2.0,
        "BCC": (a * np.sqrt(3.0)) / 4.0,
        "FCC": (a * np.sqrt(2.0)) / 4.0,
        "HCP": a / 2.0,
    }.get(ctype, 0.0)

def packing_factor(ctype):
    return {"SC": 0.524, "BCC": 0.680, "FCC": 0.740, "HCP": 0.740}.get(ctype, 0.0)

def coordination_number(ctype):
    return {"SC": 6, "BCC": 8, "FCC": 12, "HCP": 12}.get(ctype, 0)

def close_packed_direction(ctype):
    return {"SC": "[100]", "BCC": "[111]", "FCC": "[110]", "HCP": "[11-20]"}.get(ctype, "N/A")

def atoms_per_unit_cell(ctype):
    return {"SC": 1, "BCC": 2, "FCC": 4, "HCP": 6}.get(ctype, 0)
