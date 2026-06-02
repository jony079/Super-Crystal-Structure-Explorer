# crystal_engine.py
import math
import numpy as np
import streamlit as st
from metrics import profile_performance

@st.cache_data
def d_spacing(a, h, k, l, crystal_type="cubic", c=None):
    if h == 0 and k == 0 and l == 0:
        return None
    if crystal_type in ("SC", "BCC", "FCC"):
        return a / math.sqrt(h**2 + k**2 + l**2)
    else:  # HCP
        if c is None:
            c = a * 1.633
        denom = (4/3) * (h**2 + h*k + k**2) / (a**2) + l**2 / (c**2)
        return 1.0 / math.sqrt(denom) if denom > 0 else None

@st.cache_data
def atomic_radius(a, crystal_type, c=None):
    if crystal_type == "SC": return a / 2.0
    elif crystal_type == "BCC": return math.sqrt(3) * a / 4.0
    elif crystal_type == "FCC": return math.sqrt(2) * a / 4.0
    else: return a / 2.0

def close_packed_direction(crystal_type):
    dirs = {"SC": "[100]", "BCC": "[111]", "FCC": "[110]", "HCP": "[11̄20]"}
    return dirs.get(crystal_type, "—")

def coordination_number(crystal_type):
    cn = {"SC": 6, "BCC": 8, "FCC": 12, "HCP": 12}
    return cn.get(crystal_type, 0)

@st.cache_data
def packing_factor(crystal_type):
    apfs = {
        "SC":  math.pi / 6,
        "BCC": math.pi * math.sqrt(3) / 8,
        "FCC": math.pi * math.sqrt(2) / 6,
        "HCP": math.pi * math.sqrt(2) / 6, 
    }
    return apfs.get(crystal_type, 0)

def atoms_per_unit_cell(crystal_type):
    n = {"SC": 1, "BCC": 2, "FCC": 4, "HCP": 6}
    return n.get(crystal_type, 0)

@st.cache_data
def structure_factor(crystal_type, h, k, l):
    """
    Fixed HCP hallucination by using explicit crystallographic extinction rules.
    """
    def phase(x, y, z):
        return np.exp(2j * math.pi * (h*x + k*y + z*l))

    if crystal_type == "SC":
        atoms = [(0, 0, 0)]
    elif crystal_type == "BCC":
        atoms = [(0, 0, 0), (0.5, 0.5, 0.5)]
    elif crystal_type == "FCC":
        atoms = [(0,0,0),(0.5,0.5,0),(0.5,0,0.5),(0,0.5,0.5)]
    else:  # HCP
        # Exact extinction rule for HCP to avoid floating point hallucinations
        if (h + 2*k) % 3 == 0 and l % 2 != 0:
            return 0.0, 0.0, "Forbidden (destructive interference) — intensity ≈ 0", 2
        atoms = [(0,0,0),(1/3, 2/3, 0.5)]

    F = sum(phase(x, y, z) for x, y, z in atoms)
    F_sq = abs(F)**2
    n_atoms = len(atoms)
    F_rel = F_sq / (n_atoms**2)

    if F_rel < 0.01:
        rule = "Forbidden (destructive interference) — intensity ≈ 0"
    elif F_rel > 0.99:
        rule = "Fully allowed (constructive interference) — maximum intensity"
    else:
        rule = f"Partially allowed — relative intensity {F_rel:.3f}"

    return F_sq, F_rel, rule, n_atoms

@st.cache_data(show_spinner=False)
@profile_performance # Health metric tracking execution time
def xrd_peaks(crystal_type, a, wavelength_A, two_theta_max=90, c=None):
    peak_dict = {} 
    
    # Reduced loop limits practically for fast generation without losing data
    if crystal_type == "HCP":
        hkl_range = range(-4, 5)
        l_range = range(-4, 5)
    else:
        hkl_range = range(-5, 6)
        l_range = range(-5, 6)

    for h in hkl_range:
        for k in hkl_range:
            for l in l_range:
                if h == 0 and k == 0 and l == 0:
                    continue
                d = d_spacing(a, h, k, l, crystal_type=crystal_type, c=c)
                if d is None or d <= 0:
                    continue
                sin_theta = wavelength_A / (2 * d)
                if not (0 < sin_theta <= 1):
                    continue
                theta = math.asin(sin_theta)
                two_theta = math.degrees(2 * theta)
                if two_theta > two_theta_max:
                    continue

                _, F_rel, _, _ = structure_factor(crystal_type, h, k, l)
                if F_rel < 0.005:
                    continue 

                key = round(two_theta, 1)
                if key in peak_dict:
                    peak_dict[key][0] += F_rel
                    peak_dict[key][1].add(f"({h}{k}{l})")
                else:
                    peak_dict[key] = [F_rel, {f"({h}{k}{l})"}]

    if not peak_dict:
        return []

    peaks = [(tt, v[0], ", ".join(sorted(v[1]))) for tt, v in peak_dict.items()]
    peaks.sort()
    max_I = max(p[1] for p in peaks)
    peaks = [(tt, I/max_I*100, lbl) for tt, I, lbl in peaks]
    return peaks