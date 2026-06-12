# crystal_engine.py

```python
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
        (1/3, 2/3, 0.5)
    ]
}


# ==================================================
# d-spacing
# ==================================================

@profile_performance
@st.cache_data
def d_spacing(
    a,
    h,
    k,
    l,
    crystal_type="SC",
    c=None
):
    """
    Calculate interplanar spacing.
    """

    if (h, k, l) == (0, 0, 0):
        return None

    if a <= 0:
        return None

    if crystal_type in ("SC", "BCC", "FCC"):

        denominator = h**2 + k**2 + l**2

        if denominator <= 0:
            return None

        return a / np.sqrt(denominator)

    if crystal_type == "HCP":

        if c is None or c <= 0:
            return None

        term1 = (
            4.0 / 3.0
        ) * (
            (h**2 + h*k + k**2) / (a**2)
        )

        term2 = (l**2) / (c**2)

        denominator = term1 + term2

        if denominator <= 0:
            return None

        return 1.0 / np.sqrt(denominator)

    return None


# ==================================================
# Structure Factor
# ==================================================

@profile_performance
@st.cache_data
def structure_factor(
    ctype,
    h,
    k,
    l
):
    """
    Structure factor using phase summation.

    Assumes atomic scattering factor:
        f = 1

    Returns:
        F_sq,
        F_rel,
        status,
        n_basis
    """

    basis = BASIS_MAP.get(ctype)

    if basis is None:
        return 0.0, 0.0, "Unknown", 0

    F = sum(
        np.exp(
            2j * np.pi *
            (h*x + k*y + l*z)
        )
        for x, y, z in basis
    )

    F_sq = float(abs(F) ** 2)

    n_basis = len(basis)

    F_rel = F_sq / (n_basis ** 2)

    if F_rel < 1e-2:
        status = "Forbidden"

    elif F_rel > 0.99:
        status = "Allowed"

    else:
        status = "Partial"

    return (
        F_sq,
        F_rel,
        status,
        n_basis
    )


# ==================================================
# XRD Peak Simulation
# ==================================================

@profile_performance
@st.cache_data
def xrd_peaks(
    crystal_type,
    a,
    wavelength,
    two_theta_max=120,
    c=None
):
    """
    Simulate diffraction peaks.

    Returns:
        (
            two_theta,
            intensity,
            h,
            k,
            l
        )
    """

    peaks = []

    for h in range(-6, 7):
        for k in range(-6, 7):
            for l in range(-6, 7):

                if (h, k, l) == (0, 0, 0):
                    continue

                d = d_spacing(
                    a,
                    h,
                    k,
                    l,
                    crystal_type,
                    c
                )

                if d is None:
                    continue

                sin_theta = wavelength / (2 * d)

                if sin_theta >= 1:
                    continue

                theta = np.arcsin(sin_theta)

                two_theta = (
                    np.degrees(theta) * 2
                )

                if two_theta > two_theta_max:
                    continue

                (
                    F_sq,
                    F_rel,
                    status,
                    _
                ) = structure_factor(
                    crystal_type,
                    h,
                    k,
                    l
                )

                if status == "Forbidden":
                    continue

                intensity = F_rel * 100

                duplicate = any(
                    abs(existing[0] - two_theta)
                    < 0.1
                    for existing in peaks
                )

                if not duplicate:

                    peaks.append(
                        (
                            float(two_theta),
                            float(intensity),
                            h,
                            k,
                            l
                        )
                    )

    peaks.sort(
        key=lambda item: item[0]
    )

    return peaks


# ==================================================
# Utility Functions
# ==================================================

def atomic_radius(a, ctype, c=None):

    return {
        "SC": a / 2,
        "BCC": (a * np.sqrt(3)) / 4,
        "FCC": (a * np.sqrt(2)) / 4,
        "HCP": a / 2,
    }.get(ctype, 0.0)


def packing_factor(ctype):

    return {
        "SC": 0.524,
        "BCC": 0.680,
        "FCC": 0.740,
        "HCP": 0.740
    }.get(ctype, 0.0)


def coordination_number(ctype):

    return {
        "SC": 6,
        "BCC": 8,
        "FCC": 12,
        "HCP": 12
    }.get(ctype, 0)


def close_packed_direction(ctype):

    return {
        "SC": "[100]",
        "BCC": "[111]",
        "FCC": "[110]",
        "HCP": "[11-20]"
    }.get(ctype, "N/A")


def atoms_per_unit_cell(ctype):

    return {
        "SC": 1,
        "BCC": 2,
        "FCC": 4,
        "HCP": 6
    }.get(ctype, 0)
```
