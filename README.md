# ⚛️ Crystal Structure Explorer

An interactive, premium 3D web application designed for materials science and engineering students, researchers, and educators. This toolkit simplifies the visualization and analysis of crystallographic concepts including unit cells, Miller indices, X-ray diffraction (XRD) simulation, and atomic packing dynamics.

✨Live app :https://super-crystal-structure-explorer-qjpuamxeaehdxefv63d6re.streamlit.app/

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


## 💻 Local Installation & Setup

Follow these simple steps to set up and run the application locally on your machine in under 5 minutes.

### 1. Clone the Repository
Open your terminal or command prompt and run the following commands to clone the project repository and navigate into the directory:
git clone [https://github.com/jony079/Super-Crystal-Structure-Explorer.git](https://github.com/jony079/Super-Crystal-Structure-Explorer.git)
cd Super-Crystal-Structure-Explorer

git clone [https://github.com/jony079/Super-Crystal-Structure-Explorer.git](https://github.com/jony079/Super-Crystal-Structure-Explorer.git)
cd Super-Crystal-Structure-
2. Create and Activate a Virtual Enviroment
For Windows:
python -m venv venv
venv\Scripts\activate
3. Install Project Dependencies
pip install -r requirements.txt
4. Launch the Interactive Dashboard!
streamlit run app.py
🎉 That's it! Your default web browser will automatically open a new active tab hosting the dashboard at http://localhost:8501. If it doesn't open automatically, just copy and paste that exact link into your browser.
