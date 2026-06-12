import math
import numpy as np
import streamlit as st

from metrics import profile_performance


# --------------------------------------------------
# Core Crystallography Functions
# --------------------------------------------------

@profile_performance
@st.cache_data
def d_spacing(a, h, k, l, crystal_type="SC", c=None):
    """
    Calculate interplanar spacing (d-spacing).
    """

    if h == 0 and k == 0 and l == 0:
        return None

    if crystal_type in ("SC", "BCC", "FCC"):
        return a / np.sqrt(h**2 + k**2 + l**2)

    if crystal_type == "HCP":
        if c is None:
            return None

        term1 = (4.0 / 3.0) * (
            (h**2 + h * k + k**2) / (a**2)
        )
        term2 = (l**2) / (c**2)

        denominator = term1 + term2

        if denominator <= 0:
            return None

        return 1.0 / np.sqrt(denominator)

    return None


@profile_performance
@st.cache_data
def xrd_peaks(
    crystal_type,
    a,
    wavelength,
    two_theta_max=120,
    c=None,
):
    """
    Simulate XRD peaks with selection rules and
    duplicate peak suppression.
    """

    peaks = []

    for h in range(-6, 7):
        for k in range(-6, 7):
            for l in range(-6, 7):

                if h == 0 and k == 0 and l == 0:
                    continue

                # --------------------------
                # Selection Rules
                # --------------------------

                allowed = False

                if crystal_type == "SC":
                    allowed = True

                elif crystal_type == "BCC":
                    allowed = ((h + k + l) % 2 == 0)

                elif crystal_type == "FCC":
                    allowed = (h % 2 == k % 2 == l % 2)

                elif crystal_type == "HCP":
                    allowed = not (
                        ((h + 2 * k) % 3 == 0)
                        and (l % 2 != 0)
                    )

                if not allowed:
                    continue

                d = d_spacing(
                    a,
                    h,
                    k,
                    l,
                    crystal_type,
                    c,
                )

                if d is None:
                    continue

                sin_theta = wavelength / (2 * d)

                if sin_theta >= 1.0:
                    continue

                theta = np.arcsin(sin_theta)
                two_theta = np.degrees(theta) * 2

                if two_theta > two_theta_max:
                    continue

                # --------------------------
                # Relative Intensity
                # --------------------------

                if crystal_type == "HCP":

                    phase_angle = np.pi * (
                        ((h + 2 * k) / 3.0)
                        + (l / 2.0)
                    )

                    f_sq = 4 * (np.cos(phase_angle) ** 2)

                    if f_sq < 1e-3:
                        continue

                    intensity = (f_sq / 4.0) * 100

                else:
                    intensity = 100.0

                # Cleaner Miller notation
                label = f"({h} {k} {l})"

                duplicate = any(
                    abs(existing[0] - two_theta) < 0.1
                    for existing in peaks
                )

                if not duplicate:
                    peaks.append(
                        (
                            two_theta,
                            intensity,
                            label,
                        )
                    )

    peaks.sort(key=lambda x: x[0])

    return peaks


# --------------------------------------------------
# Utility Functions
# --------------------------------------------------

def atomic_radius(a, ctype, c=None):
    if ctype == "SC":
        return a / 2

    if ctype == "BCC":
        return (a * np.sqrt(3)) / 4

    if ctype == "FCC":
        return (a * np.sqrt(2)) / 4

    if ctype == "HCP":
        return a / 2

    return 0.0


def packing_factor(ctype):
    return {
        "SC": 0.524,
        "BCC": 0.680,
        "FCC": 0.740,
        "HCP": 0.740,
    }.get(ctype, 0.0)


def coordination_number(ctype):
    return {
        "SC": 6,
        "BCC": 8,
        "FCC": 12,
        "HCP": 12,
    }.get(ctype, 0)


def close_packed_direction(ctype):
    return {
        "SC": "[100]",
        "BCC": "[111]",
        "FCC": "[110]",
        "HCP": "[11-20]",
    }.get(ctype, "N/A")


def atoms_per_unit_cell(ctype):
    return {
        "SC": 1,
        "BCC": 2,
        "FCC": 4,
        "HCP": 6,
    }.get(ctype, 0)


def structure_factor(ctype, h, k, l):

    if ctype == "SC":
        return 1, 1.0, "Allowed", 1

    if ctype == "BCC":
        allowed = ((h + k + l) % 2 == 0)

        return (
            (4, 1.0, "Allowed", 2)
            if allowed
            else (0, 0.0, "Forbidden", 2)
        )

    if ctype == "FCC":
        allowed = (h % 2 == k % 2 == l % 2)

        return (
            (16, 1.0, "Allowed", 4)
            if allowed
            else (0, 0.0, "Forbidden", 4)
        )

    # HCP

    phase = np.pi * (
        ((h + 2 * k) / 3.0)
        + (l / 2.0)
    )

    f_sq = 4 * (np.cos(phase) ** 2)

    return (
        f_sq,
        f_sq / 4.0,
        "Allowed" if f_sq > 0.001 else "Forbidden",
        2,
    )
