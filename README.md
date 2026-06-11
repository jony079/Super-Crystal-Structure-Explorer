# ⚛️ Crystal Structure Explorer

An interactive, premium 3D web application designed for materials science and engineering students, researchers, and educators. This toolkit simplifies the visualization and analysis of crystallographic concepts including unit cells, Miller indices, X-ray diffraction (XRD) simulation, and atomic packing dynamics.

✨ **Live Demo:** [View App on Streamlit](https://cubic-crystal-visualizer-mse-cxapykbcsf5a5aysnzscjj.streamlit.app/)

---

## 🚀 Key Features

* **📸 Interactive 3D Unit Cell & Miller Planes:** Visualize **SC, BCC, FCC, and HCP** crystal lattices in 360-degree freedom. Dynamically slide and render any `(hkl)` Miller plane with real-time intersection calculations.
* **🔬 XRD Diffraction Pattern Simulator:** Simulate custom X-ray diffraction profiles based on the selected crystal structure and X-ray wavelength ($\lambda$). Features adjustable peak widths (FWHM) and automated Bragg peak indexing.
* **⚡ Structure Factor ($F_{hkl}$) Breakdown:** Step-by-step mathematical derivation showing how constructive and destructive wave interferences determine **allowed** vs **forbidden** reflections.
* **📦 Atomic Packing & Coordination Visualizer:** Explore atomic coordination numbers via isolated 3D cluster maps and view full geometrical derivations for Atomic Packing Factors (APF).

---

## 🛠️ Tech Stack

* **Frontend & Dashboard:** Streamlit (Premium Dark UI theme)
* **3D Graphics & Plotting:** Plotly (Scatter3D, Mesh3D, and Graph Objects)
* **Mathematical Engine:** NumPy & Math
* **Data Management:** Pandas

---

## 💻 Local Installation & Setup

Follow these steps to clone and run this project locally on your machine:

### 1. Clone the Repository
git clone https://github.com/jony079/Super-Crystal-Structure-Explorer.git
cd Super-Crystal-Structure-Explorer
