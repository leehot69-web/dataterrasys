
# GeoMind Cloud - Core Architecture

## Tech Stack
*   **Web Framework**: Streamlit
*   **Data Processing**: Pandas, NumPy, lasio, segyio
*   **Math**: petro_core_web.py (Extracted Logic)
*   **Visualization**: Plotly (2D/3D Interactive)
*   **Deploy**: SaaS (Zero-Storage, RAM-only processing)

## Components
1.  **Frontend (app_saas.py)**:
    *   Authentication (Simple SaaS Guard)
    *   File Upload (Ephemeral)
    *   Dashboard
2.  **Backend Logic (petro_core_web.py)**:
    *   Petrophysics Class (Vsh, Phi, Sw, Perm)
    *   Reservoir Detection (Full Intervals)
    *   Geostats (Kriging, Surface Interpolation)
3.  **Data Flow**:
    *   Upload -> TempFile (RAM) -> DataFrame -> Compute -> Plotly Graph -> TempFile Delete.

## Security Constraints
*   **NO** persistent storage of user data (LGS/SEGY).
*   **NO** executables (.exe) sent to client.
*   **NO** mixing UI frameworks (PyQt/Kivy are banned).
