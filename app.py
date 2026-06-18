# app.py
import streamlit as st
import numpy as np
import math
import plotly.graph_objects as go
import pandas as pd

# 1. Import cached logic from engine
from crystal_engine import (
    d_spacing, atomic_radius, close_packed_direction, 
    coordination_number, packing_factor, atoms_per_unit_cell, 
    structure_factor, xrd_peaks
)

# Page Configuration
st.set_page_config(page_title="Crystal Structure Explorer", page_icon="⚛️", layout="wide")

# Global Source of Truth for Basis Positions to prevent duplication
BASIS_MAP = {
    "SC": [(0.0, 0.0, 0.0)],
    "BCC": [(0.0, 0.0, 0.0), (0.5, 0.5, 0.5)],
    "FCC": [(0.0, 0.0, 0.0), (0.5, 0.5, 0.0), (0.5, 0.0, 0.5), (0.0, 0.5, 0.5)],
    "HCP": [(0.0, 0.0, 0.0), (1/3, 2/3, 0.5)]
}

# Premium Dark Mode Custom UI CSS
st.markdown("""
<style>
    body { background-color: #0d1117; color: #c9d1d9; }
    .stApp { background-color: #0d1117; }
    .kpi-card {
        background: linear-gradient(135deg, #161b22 0%, #21262d 100%);
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin-bottom: 15px;
    }
    .kpi-title { font-size: 0.85rem; color: #8b949e; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px; }
    .kpi-value { font-size: 2rem; color: #58a6ff; font-weight: 700; margin: 5px 0; }
    .kpi-delta { font-size: 0.8rem; color: #3fb950; }
    .status-box-forbidden {
        background-color: #2c1a1d; border: 1px solid #6b2d2d;
        border-radius: 6px; padding: 15px; color: #ff7b72; margin: 10px 0;
    }
    .status-box-allowed {
        background-color: #142c16; border: 1px solid #2da44e;
        border-radius: 6px; padding: 15px; color: #7ee787; margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)
# ==========================================
# STEP 1: SIDEBAR USER INTERFACE
# ==========================================

# THE FINAL ULTIMATE GLOW INJECTION: Targets by exact structural position
st.markdown(
    """
    <style>
    /* 1. Target the absolute first button in the top header section (Always the >> button) */
    div[data-testid="stHeader"] > header button:first-child,
    div[class*="stHeader"] button:first-child,
    button[data-testid="stSidebarCollapseButton"] {
        background-color: #1e293b !important;   /* Solid dark background contrast */
        border: 2px solid #38bdf8 !important;   /* Permanent bright neon border */
        border-radius: 8px !important;          /* Sharp curved border */
        padding: 6px !important;
        opacity: 1 !important;                  /* Prevents Streamlit from auto-fading */
        visibility: visible !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        
        /* CONSTANT HIGH-INTENSITY CYAN NEON GLOW */
        box-shadow: 0px 0px 15px rgba(56, 189, 248, 0.95) !important;
        -webkit-box-shadow: 0px 0px 15px rgba(56, 189, 248, 0.95) !important;
    }
    
    /* 2. Target the expanded button (<<) inside the sidebar panel */
    section[data-testid="stSidebar"] button[aria-label="Collapse sidebar"],
    section[data-testid="stSidebar"] button:first-child {
        background-color: #1e293b !important;
        border: 2px solid #38bdf8 !important;
        border-radius: 8px !important;
        padding: 6px !important;
        opacity: 1 !important;
        visibility: visible !important;
        
        /* CONSTANT MATCHING GLOW */
        box-shadow: 0px 0px 15px rgba(56, 189, 248, 0.95) !important;
    }

    /* 3. Force color glow on the icon vectors inside these two specific positions */
    div[data-testid="stHeader"] > header button:first-child svg,
    div[class*="stHeader"] button:first-child svg,
    section[data-testid="stSidebar"] button svg {
        fill: #38bdf8 !important;               /* Cyan vector color */
        color: #38bdf8 !important;              /* Outline fallback */
        transform: scale(1.25) !important;      /* Icon size magnification */
    }

    /* Hover state micro-interaction */
    div[data-testid="stHeader"] > header button:first-child:hover,
    section[data-testid="stSidebar"] button:hover {
        background-color: #0f172a !important;
        box-shadow: 0px 0px 22px #38bdf8 !important; /* Hyper boost glow on hover/touch */
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown("## CRYSTAL TYPE")
ctype = st.sidebar.radio("", ["SC", "BCC", "FCC", "HCP"], index=2, label_visibility="collapsed")

st.sidebar.markdown("### LATTICE PARAMETERS")
a_val = st.sidebar.number_input("Lattice parameter a (Å)", value=4.050, min_value=0.1, step=0.001, format="%.3f")

# Explicit fallback mapping at the UI instantiation layer
if ctype == "HCP":
    c_val = st.sidebar.number_input("Lattice parameter c (Å)", value=6.600, min_value=0.1, step=0.001, format="%.3f")
else:
    c_val = None  # Explicit, never implicit guess vectors

st.sidebar.markdown("### MILLER INDICES (HKL)")
# FIXED BUG: Columns dynamic explicit sidebar rendering mapping via grid framework
col_h, col_k, col_l = st.sidebar.columns(3)
with col_h: h = col_h.number_input("h", value=1, step=1, key="input_h")
with col_k: k = col_k.number_input("k", value=1, step=1, key="input_k")
with col_l: l = col_l.number_input("l", value=0, step=1, key="input_l")

st.sidebar.markdown("### VISUALIZATION OPTIONS")
plane_shift = st.sidebar.slider("Plane shift C (hx+ky+lz = C)", min_value=-2.0, max_value=2.0, value=1.00, step=0.1)
atom_size = st.sidebar.slider("Atom display size", min_value=0.05, max_value=0.5, value=0.18, step=0.01)

st.sidebar.markdown("### XRD SETTINGS")
wavelength_A = st.sidebar.number_input("X-ray wavelength λ (Å)", value=1.5406, min_value=0.1, step=0.0001, format="%.4f")

# CRITICAL FIX: Dynamic zero plane checking configuration pipeline safely evaluation
if h == 0 and k == 0 and l == 0:
    st.sidebar.error("❌ Miller indices (h,k,l) cannot all be zero!")
    d, F_sq, F_rel, F_rule = float('inf'), 0.0, 0.0, "Forbidden"
    r = atomic_radius(a_val, ctype, c=c_val)
    apf = packing_factor(ctype)
    cn = coordination_number(ctype)
    cpd = close_packed_direction(ctype)
    n_atoms = atoms_per_unit_cell(ctype)
    n_basis = 0
else:
    # Safe numerical execution pipelines
    d = d_spacing(a_val, h, k, l, crystal_type=ctype, c=c_val)
    r = atomic_radius(a_val, ctype, c=c_val)
    apf = packing_factor(ctype)
    cn = coordination_number(ctype)
    cpd = close_packed_direction(ctype)
    n_atoms = atoms_per_unit_cell(ctype)
    F_sq, F_rel, F_rule, n_basis = structure_factor(ctype, h, k, l)
# ==========================================
# STEP 2: MAIN DASHBOARD HEADER & KPI CARDS
# ==========================================
st.markdown('# <span style="color:#58a6ff">■</span> Crystal Structure Explorer', unsafe_allow_html=True)
st.markdown("> Interactive materials science toolkit for crystal structure visualization, diffraction simulation, and structural analysis.")

kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
with kpi_col1:
    d_str = f"{d:.4f}" if d is not None else "N/A"
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">Interplanar Spacing D<sub>HKL</sub></div><div class="kpi-value">{d_str}</div><div class="kpi-delta">Angstroms (Å)</div></div>', unsafe_allow_html=True)
with kpi_col2:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">Atomic Radius R</div><div class="kpi-value">{r:.4f}</div><div class="kpi-delta">Angstroms (Å)</div></div>', unsafe_allow_html=True)
with kpi_col3:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">Packing Factor (APF)</div><div class="kpi-value">{apf:.4f}</div><div class="kpi-delta">{apf*100:.1f}% of volume filled</div></div>', unsafe_allow_html=True)

kpi_col4, kpi_col5, kpi_col6 = st.columns(3)
with kpi_col4:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">Coordination Number</div><div class="kpi-value">{cn}</div><div class="kpi-delta">Nearest neighbours</div></div>', unsafe_allow_html=True)
with kpi_col5:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">Atoms / Unit Cell</div><div class="kpi-value">{n_atoms}</div><div class="kpi-delta">Effective atoms</div></div>', unsafe_allow_html=True)
with kpi_col6:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">Close-Packed Direction</div><div class="kpi-value">{cpd}</div><div class="kpi-delta">Max linear atomic density</div></div>', unsafe_allow_html=True)

# Main Navigation
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📸 3D Structure", "📊 Calculations", "🔬 XRD Simulator", "⚡ Structure Factor", "📦 Packing & Coordination"
])

# --- TAB 1: 3D INTERACTIVE VISUALIZATION ---
with tab1:
    st.markdown(f"### 3D Unit Cell + Miller Plane")
    c_disp = f"{c_val:.2f} Å" if c_val else "N/A"
    st.caption(f"Crystal type: **{ctype}** · a = {a_val:.2f} Å · c = {c_disp} · Plane: **({h} {k} {l})** · C = {plane_shift:.2f}")
    
    fig = go.Figure()
    atom_coords, colors, names = [], [], []

    if ctype in ["SC", "BCC", "FCC"]:
        corners = [(x, y, z) for x in [0, 1] for y in [0, 1] for z in [0, 1]]
        atom_coords.extend(corners)
        colors.extend(["#636EFA"] * 8); names.extend(["Corner Atom"] * 8)
        if ctype == "BCC":
            atom_coords.append((0.5, 0.5, 0.5)); colors.append("#EF553B"); names.append("Body-Centered Atom")
        elif ctype == "FCC":
            faces = [(0.5,0.5,0), (0.5,0.5,1), (0.5,0,0.5), (0.5,1,0.5), (0,0.5,0.5), (1,0.5,0.5)]
            atom_coords.extend(faces); colors.extend(["#00CC96"] * 6); names.extend(["Face-Centered Atom"] * 6)
        
        box_edges = [((0,0,0),(1,0,0)), ((1,0,0),(1,1,0)), ((1,1,0),(0,1,0)), ((0,1,0),(0,0,0)),
                     ((0,0,1),(1,0,1)), ((1,0,1),(1,1,1)), ((1,1,1),(0,1,1)), ((0,1,1),(0,0,1)),
                     ((0,0,0),(0,0,1)), ((1,0,0),(1,0,1)), ((1,1,0),(1,1,1)), ((0,1,0),(0,1,1))]
        for p1, p2 in box_edges:
            fig.add_trace(go.Scatter3d(x=[p1[0], p2[0]], y=[p1[1], p2[1]], z=[p1[2], p2[2]], mode='lines', line=dict(color='#8b949e', width=3), showlegend=False))
    else:  # HCP Framework
        for z in [0, 1]:
            hex_pts = []
            for idx in range(6):
                ang = math.radians(idx * 60)
                hx, hy = 0.5 + 0.5 * math.cos(ang), 0.5 + 0.5 * math.sin(ang)
                hex_pts.append((hx, hy, z)); atom_coords.append((hx, hy, z)); colors.append("#636EFA"); names.append("Hexagonal Corner")
            atom_coords.append((0.5, 0.5, z)); colors.append("#00CC96"); names.append("Hex Base Center")
            for idx in range(6):
                p1, p2 = hex_pts[idx], hex_pts[(idx + 1) % 6]
                fig.add_trace(go.Scatter3d(x=[p1[0], p2[0]], y=[p1[1], p2[1]], z=[p1[2], p2[2]], mode='lines', line=dict(color='#8b949e', width=2), showlegend=False))
        mid_layer = [(0.5, 0.22, 0.5), (0.25, 0.62, 0.5), (0.75, 0.62, 0.5)]
        atom_coords.extend(mid_layer); colors.extend(["#EF553B"] * 3); names.extend(["Internal Mid Atom"] * 3)
        for idx in range(6):
            ang = math.radians(idx * 60)
            hx, hy = 0.5 + 0.5 * math.cos(ang), 0.5 + 0.5 * math.sin(ang)
            fig.add_trace(go.Scatter3d(x=[hx, hx], y=[hy, hy], z=[0, 1], mode='lines', line=dict(color='#8b949e', width=2), showlegend=False))

    x_a, y_a, z_a = zip(*atom_coords)
    fig.add_trace(go.Scatter3d(x=x_a, y=y_a, z=z_a, mode='markers', marker=dict(size=atom_size * 100, color=colors, opacity=0.85), text=names, hoverinfo='text', name="Atoms"))

    # Render Miller Plane properly using a microscopic thickness trick for 3D Mesh
    if not (h == 0 and k == 0 and l == 0):
        intersect_points = []
        for fx in [0.0, 1.0]:
            for fy in [0.0, 1.0]:
                if l != 0:
                    fz = (plane_shift - h*fx - k*fy) / l
                    if 0 <= fz <= 1: intersect_points.append((fx, fy, fz))
        for fx in [0.0, 1.0]:
            for fz in [0.0, 1.0]:
                if k != 0:
                    fy = (plane_shift - h*fx - l*fz) / k
                    if 0 <= fy <= 1: intersect_points.append((fx, fy, fz))
        for fy in [0.0, 1.0]:
            for fz in [0.0, 1.0]:
                if h != 0:
                    fx = (plane_shift - k*fy - l*fz) / h
                    if 0 <= fx <= 1: intersect_points.append((fx, fy, fz))
                    
        intersect_points = list(set(intersect_points))
        
        if len(intersect_points) >= 3:
            n_mag = math.sqrt(h**2 + k**2 + l**2)
            nx, ny, nz = h/n_mag, k/n_mag, l/n_mag
            
            px_vol, py_vol, pz_vol = [], [], []
            for p in intersect_points:
                px_vol.extend([p[0] + nx*0.001, p[0] - nx*0.001])
                py_vol.extend([p[1] + ny*0.001, p[1] - ny*0.001])
                pz_vol.extend([p[2] + nz*0.001, p[2] - nz*0.001])
                
            fig.add_trace(go.Mesh3d(
                x=px_vol, y=py_vol, z=pz_vol, 
                color='#ab63fa', opacity=0.55, 
                alphahull=0, 
                name=f"({h}{k}{l}) Plane", 
                showlegend=True
            ))

    fig.update_layout(scene=dict(xaxis=dict(backgroundcolor="#0d1117", gridcolor="#30363d"), yaxis=dict(backgroundcolor="#0d1117", gridcolor="#30363d"), zaxis=dict(backgroundcolor="#0d1117", gridcolor="#30363d")), margin=dict(l=0,r=0,b=0,t=0), paper_bgcolor='#0d1117')
    st.plotly_chart(fig, use_container_width=True)

# --- TAB 2: CALCULATIONS & DERIVATIONS ---
with tab2:
    st.markdown("#### Crystallographic Geometrical Derivations")
    st.markdown("---")
    st.write(f"**Unit Cell Volume ($V_{{cell}}$):** `{pow(a_val, 3):.4f}` Å³" if ctype != "HCP" else f"**Unit Cell Volume ($V_{{cell}}$):** `{(1.5 * math.sqrt(3) * pow(a_val, 2) * c_val):.4f}` Å³")
    st.write(f"**Total Volume Filled by Atoms:** `{(n_atoms * (4/3) * math.pi * pow(r, 3)):.4f}` Å³")

# --- TAB 3: XRD SIMULATOR ---
with tab3:
    st.markdown("### XRD Diffraction Pattern Simulator")
    st.caption(f"Crystal: **{ctype}** · a = {a_val} Å · λ = {wavelength_A} Å")
    
    xrd_ctrl1, xrd_ctrl2, xrd_ctrl3 = st.columns([1, 1, 1])
    with xrd_ctrl1: 
        max_2theta = st.slider("Max 2θ (°)", min_value=45, max_value=120, value=90, step=5)
    with xrd_ctrl2: 
        show_labels = st.checkbox("Show hkl labels", value=True)
    with xrd_ctrl3: 
        peak_width = st.slider("Peak width (°)", min_value=0.10, max_value=2.00, value=0.40, step=0.05)

    # Fetching structured peak list data dictionaries from the single source of truth core
    peaks_list = xrd_peaks(ctype, a_val, wavelength_A, two_theta_max=max_2theta, c=c_val)
    
    if peaks_list:
        two_theta_axis = np.linspace(5, max_2theta, 1000)
        continuous_intensity = np.zeros_like(two_theta_axis)
        
        # Exact Analytical FWHM to Gaussian Standard Deviation Conversion
        # FWHM = 2 * sqrt(2 * ln(2)) * sigma -> sigma = FWHM / 2.354820045...
        _FWHM_TO_SIGMA = 2.0 * math.sqrt(2.0 * math.log(2.0))
        sigma = peak_width / _FWHM_TO_SIGMA
        
        # FIXED: Removed the redundant copy paste loop block to keep the logic clean
        for peak in peaks_list:
            tt_peak = peak["two_theta"] if isinstance(peak, dict) else peak[0]
            intensity = peak["intensity"] if isinstance(peak, dict) else peak[1]
            continuous_intensity += intensity * np.exp(-0.5 * ((two_theta_axis - tt_peak) / sigma) ** 2)
            
        if max(continuous_intensity) > 0:
            continuous_intensity = (continuous_intensity / max(continuous_intensity)) * 100

        xrd_fig = go.Figure()
        xrd_fig.add_trace(go.Scatter(
            x=two_theta_axis, y=continuous_intensity, 
            mode='lines', line=dict(color='#26d0ce', width=2), 
            name="Profile Curve"
        ))
        
        for peak in peaks_list:
            if isinstance(peak, dict):
                tt_peak = peak["two_theta"]
                intensity = peak["intensity"]
                label = peak["label"]
            else:  # Fallback just in case raw tuples are processed
                tt_peak, intensity, hp, kp, lp = peak
                label = f"({hp} {kp} {lp})"
            
            xrd_fig.add_trace(go.Scatter(
                x=[tt_peak, tt_peak], y=[0, intensity], 
                mode='lines', line=dict(color='#f0883e', width=1, dash='dash'), 
                showlegend=False, hoverinfo='skip'
            ))
            if show_labels:
                xrd_fig.add_trace(go.Scatter(
                    x=[tt_peak], y=[intensity + 3], 
                    mode='text', text=[label], 
                    textposition="top center", 
                    textfont=dict(size=10, color="#c9d1d9"), 
                    showlegend=False
                ))

        xrd_fig.update_layout(
            xaxis_title="2θ (°)", yaxis_title="Relative Intensity (%)",
            xaxis=dict(range=[5, max_2theta], gridcolor="#21262d"), 
            yaxis=dict(range=[0, 115], gridcolor="#21262d"),
            paper_bgcolor='#0d1117', plot_bgcolor='#0d1117', 
            margin=dict(l=40, r=40, b=40, t=20)
        )
        st.plotly_chart(xrd_fig, use_container_width=True)
        
        # THE HONEST & ROBUST DATA TABLE PIPELINE
        st.markdown("#### 📋 PEAK LIST")
        table_data = []
        
        for peak in peaks_list:
            if isinstance(peak, dict):
                h_p, k_p, l_p = peak["h"], peak["k"], peak["l"]
                tt_val = peak["two_theta"]
                int_val = peak["intensity"]
                lbl_val = peak["label"]
            else:
                tt_val, int_val, h_p, k_p, l_p = peak
                lbl_val = f"({h_p} {k_p} {l_p})"

            d_space = d_spacing(a_val, h_p, k_p, l_p, crystal_type=ctype, c=c_val)
            d_display = f"{d_space:.4f}" if d_space else "N/A"
            
            table_data.append({
                "2θ (°)": f"{tt_val:.2f}", 
                "I_rel (%)": f"{int_val:.1f}", 
                "d (Å)": d_display, 
                "hkl families": lbl_val
            })
            
        st.dataframe(pd.DataFrame(table_data), use_container_width=True)
    else:
        st.error("No reflection vectors fit the current simulation bounds or systematic absence rules.")

# --- TAB 4: STRUCTURE FACTOR STEP BREAKDOWN ---
with tab4:
    st.markdown("### Structure Factor F(hkl)")
    st.write("The structure factor determines whether a reflection is **allowed** or **forbidden** by symmetry.")
    
    sf_col1, sf_col2 = st.columns(2)
    with sf_col1:
        st.markdown("##### FORMULA")
        st.latex(r"F_{hkl} = \sum_{j=1}^{N} f_j e^{2\pi i (hx_j + ky_j + lz_j)}")
        st.write("For an elemental crystal all scattering factors $f_j = f$:")
        st.latex(r"F_{hkl} = f \sum_{j} e^{2\pi i (hx_j + ky_j + lz_j)}")
        
        st.markdown("##### ATOM BASIS")
        basis = BASIS_MAP.get(ctype, [(0.0, 0.0, 0.0)])
        
        for idx, (bx, by, bz) in enumerate(basis):
            st.write(f"**Atom {idx+1}:** `({bx:.4f}, {by:.4f}, {bz:.4f})`")

    with sf_col2:
        st.markdown(f"##### RESULT FOR ({h} {k} {l})")
        
        for idx, (bx, by, bz) in enumerate(basis):
            val = h*bx + k*by + l*bz
            st.latex(f"\\text{{Atom }}{idx+1}: e^{{i\\pi \\cdot {val*2:.4f}}}")
            
        st.latex(f"|F|^2 = {F_sq:.4f} \\cdot f^2")
        st.latex(f"\\text{{Relative intensity}} = {F_rel:.4f}")
        
        if F_rule == "Forbidden":
            st.markdown(f'<div class="status-box-forbidden">❌ **FORBIDDEN reflection — systematic absence**<br>Forbidden (destructive interference) — intensity ≈ 0</div>', unsafe_allow_html=True)
        elif F_rule == "Allowed":
            st.markdown(f'<div class="status-box-allowed">✅ **ALLOWED reflection — transmission track path**<br>Constructive profile match found!</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="status-box-forbidden" style="background-color:#2a2515; border-color:#6b5a2d; color:#f0c665;">⚠️ **PARTIAL reflection**<br>Mixed profile diffraction state detected.</div>', unsafe_allow_html=True)

# --- TAB 5: PACKING & COORDINATION VISUALIZATIONS ---
with tab5:
    st.markdown("### Atomic Packing Factor & Coordination Number")
    
    pack_col1, pack_col2 = st.columns([1.2, 1])
    with pack_col1:
        st.markdown("##### APF DERIVATION & METRICS")
        st.latex(r"APF = \frac{N_{\text{atoms}} \cdot \frac{4}{3}\pi r^3}{V_{\text{cell}}}")
        
        st.markdown(f"**Current Structural $APF_{{{ctype}}}$:** `{apf:.5f}` ({apf*100:.3f}%)")
        
        # 📊 SINGLE SOURCE OF TRUTH: Derive chart metrics directly from the engine
        structures = ["SC", "BCC", "FCC", "HCP"]
        apf_values = [packing_factor(s) * 100.0 for s in structures]
        text_labels = [f"{v:.2f}%" for v in apf_values]
        
        bar_fig = go.Figure(go.Bar(
            x=structures, 
            y=apf_values,
            text=text_labels, 
            textposition='auto',
            marker_color=['#707a8a', '#f0883e', '#ff4b4b', '#ab63fa']
        ))
        
        bar_fig.add_shape(
            type="line", x0=-0.5, x1=3.5, 
            y0=apf * 100.0, y1=apf * 100.0, 
            line=dict(color="#ff4b4b", width=2, dash="dash")
        )
        
        bar_fig.update_layout(
            yaxis_title="Dynamic APF (%)", 
            paper_bgcolor='#0d1117', plot_bgcolor='#0d1117', 
            margin=dict(t=10, b=10, l=10, r=10), height=250,
            xaxis=dict(gridcolor="#21262d"), yaxis=dict(gridcolor="#21262d")
        )
        st.plotly_chart(bar_fig, use_container_width=True)

    with pack_col2:
        st.markdown("##### COORDINATION NUMBER VISUALIZATION")
        st.write(f"**{ctype}** has a coordination number of **{cn}**.")
        st.info(f"Interactive 3D View: Central atom surrounded by {cn} nearest neighbors.")
        
        net_fig = go.Figure()
        net_fig.add_trace(go.Scatter3d(
            x=[0], y=[0], z=[0], 
            mode='markers', 
            marker=dict(size=22, color='#ff4b4b'), 
            name="Central Atom"
        ))
        
        neighbors = []
        if ctype == "SC": 
            neighbors = [(1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1)]
        elif ctype == "BCC": 
            r_n = 0.5
            neighbors = [(r_n,r_n,r_n), (r_n,r_n,-r_n), (r_n,-r_n,r_n), (r_n,-r_n,-r_n), 
                         (-r_n,r_n,r_n), (-r_n,r_n,-r_n), (-r_n,-r_n,r_n), (-r_n,-r_n,-r_n)]
        elif ctype == "FCC": 
            r_n = 0.5
            neighbors = [(r_n,r_n,0), (r_n,-r_n,0), (-r_n,r_n,0), (-r_n,-r_n,0), 
                         (r_n,0,r_n), (r_n,0,-r_n), (-r_n,0,r_n), (-r_n,0,-r_n), 
                         (0,r_n,r_n), (0,r_n,-r_n), (0,-r_n,r_n), (0,-r_n,-r_n)]
        elif ctype == "HCP": 
            neighbors = [(1,0,0), (-1,0,0), (0.5, 0.866, 0), (-0.5, 0.866, 0), 
                         (0.5, -0.288, 0.816), (-0.5, -0.288, 0.816), (0, 0.577, 0.816), 
                         (0, 0.577, -0.816), (0.5, -0.288, -0.816), (-0.5, -0.288, -0.816)]

        for i, (nx, ny, nz) in enumerate(neighbors):
            net_fig.add_trace(go.Scatter3d(
                x=[0, nx], y=[0, ny], z=[0, nz], 
                mode='lines', line=dict(color='#30363d', width=3), 
                hoverinfo='skip', showlegend=False
            ))
            net_fig.add_trace(go.Scatter3d(
                x=[nx], y=[ny], z=[nz], 
                mode='markers+text', 
                marker=dict(size=14, color='#26d0ce'), 
                text=[str(i+1)], textposition="middle center", 
                textfont=dict(size=9, color="#000"), showlegend=False
            ))
            
        net_fig.update_layout(
            scene=dict(xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False)),
            paper_bgcolor='#0d1117', margin=dict(t=10, b=10, l=10, r=10), height=300, showlegend=False
        )
        st.plotly_chart(net_fig, use_container_width=True)

    st.markdown("##### ALL STRUCTURES SUMMARY")
    summary_df = pd.DataFrame([
        {
            "Type": s, 
            "CN": str(coordination_number(s)), 
            "N/cell": str(atoms_per_unit_cell(s)), 
            "APF": f"{packing_factor(s):.5f}", 
            "CP Dir": close_packed_direction(s)
        }
        for s in structures
    ])
    st.table(summary_df)

# --- SYSTEM OBSERVABILITY LOGS ---
st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ SYSTEM OBSERVABILITY")
if 'telemetry_logs' in st.session_state and isinstance(st.session_state.telemetry_logs, dict):
    for func, data in st.session_state.telemetry_logs.items():
        if isinstance(data, dict) and 'execution_time_ms' in data:
            st.sidebar.caption(f"**{func}**: `{data['execution_time_ms']:.2f} ms` ⚡")
        else:
            st.sidebar.caption(f"**{func}**: telemetry trace pending...")
else:
    st.sidebar.caption("No system performance logs tracked yet.")
