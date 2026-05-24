"""
============================================================
SIMULADOR ESTRUCTURAL DE ACERO — NORMA AISC
============================================================
Autor  : Ingeniero Estructural Senior / Desarrollador Senior
Versión: 1.0
Norma  : AISC 360-22 (Especificación para Edificios de Acero Estructural)
Descripción:
    Simulador interactivo de cálculo de esfuerzos (flexión y cortante)
    y desplazamientos en vigas de acero, con verificación de capacidad
    Demanda/Capacidad (D/C) bajo los criterios AISC.
============================================================
"""

import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# ─────────────────────────────────────────────────
# 1. CONFIGURACIÓN DE PÁGINA
# ─────────────────────────────────────────────────
st.set_page_config(
    page_title="Simulador Estructural AISC",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────
# 2. ESTILOS CSS PERSONALIZADOS
# ─────────────────────────────────────────────────
st.markdown("""
<style>
    /* Fondo principal */
    .stApp { background-color: #0f1117; }

    /* Tarjetas de resultados */
    .metric-card {
        background: linear-gradient(135deg, #1e2130, #252a3a);
        border: 1px solid #2d3250;
        border-radius: 12px;
        padding: 18px 22px;
        margin-bottom: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .metric-label {
        color: #8892b0;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .metric-value {
        color: #e6f1ff;
        font-size: 1.6rem;
        font-weight: 700;
        font-family: 'Courier New', monospace;
    }
    .metric-unit {
        color: #64ffda;
        font-size: 0.85rem;
        margin-left: 4px;
    }

    /* Badge PASA / FALLA */
    .badge-pass {
        background: linear-gradient(135deg, #0d4f3c, #1a7a5e);
        border: 1px solid #64ffda;
        color: #64ffda;
        border-radius: 20px;
        padding: 4px 14px;
        font-weight: 700;
        font-size: 0.82rem;
        display: inline-block;
    }
    .badge-fail {
        background: linear-gradient(135deg, #5a1a1a, #8b2e2e);
        border: 1px solid #ff6b6b;
        color: #ff6b6b;
        border-radius: 20px;
        padding: 4px 14px;
        font-weight: 700;
        font-size: 0.82rem;
        display: inline-block;
    }
    .badge-warn {
        background: linear-gradient(135deg, #4a3500, #7a5c00);
        border: 1px solid #ffd166;
        color: #ffd166;
        border-radius: 20px;
        padding: 4px 14px;
        font-weight: 700;
        font-size: 0.82rem;
        display: inline-block;
    }

    /* Encabezado de sección */
    .section-header {
        color: #64ffda;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        border-bottom: 1px solid #2d3250;
        padding-bottom: 6px;
        margin-bottom: 14px;
    }

    /* Tabla de propiedades */
    .prop-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.85rem;
    }
    .prop-table td {
        padding: 6px 10px;
        border-bottom: 1px solid #1e2130;
        color: #ccd6f6;
    }
    .prop-table td:first-child { color: #8892b0; }
    .prop-table td:last-child {
        text-align: right;
        font-family: monospace;
        color: #e6f1ff;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #131720;
        border-right: 1px solid #2d3250;
    }

    /* Divider */
    hr { border-color: #2d3250 !important; }

    /* Título principal */
    .main-title {
        background: linear-gradient(90deg, #64ffda, #57cbff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2rem;
        font-weight: 800;
        margin-bottom: 0;
    }
    .main-subtitle {
        color: #8892b0;
        font-size: 0.9rem;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────
# 3. BASE DE DATOS DE PERFILES AISC
#    Unidades: A [cm²], I [cm⁴], S [cm³], Z [cm³],
#              r [cm], peso [kg/m], d [cm], bf [cm]
# ─────────────────────────────────────────────────
PERFILES_AISC = {
    # ── Perfiles W (Wide Flange) ──────────────────
    "W8×31": {
        "tipo": "W", "descripcion": "Perfil W de patín ancho — uso general",
        "A": 58.97,   "Ix": 3265.0,  "Iy": 620.0,
        "Sx": 400.0,  "Sy": 110.2,   "Zx": 447.0,  "Zy": 169.0,
        "rx": 7.45,   "ry": 3.25,    "peso": 46.1,
        "d": 20.32,   "bf": 20.32,
    },
    "W12×26": {
        "tipo": "W", "descripcion": "Perfil W — vigas secundarias y correas",
        "A": 49.35,   "Ix": 4772.0,  "Iy": 311.0,
        "Sx": 466.0,  "Sy": 74.7,    "Zx": 533.0,  "Zy": 114.0,
        "rx": 9.83,   "ry": 2.51,    "peso": 38.6,
        "d": 30.99,   "bf": 16.51,
    },
    "W14×48": {
        "tipo": "W", "descripcion": "Perfil W — vigas principales medianas",
        "A": 91.03,   "Ix": 12470.0, "Iy": 1630.0,
        "Sx": 1013.0, "Sy": 262.0,   "Zx": 1143.0, "Zy": 402.0,
        "rx": 11.71,  "ry": 4.24,    "peso": 71.4,
        "d": 35.56,   "bf": 20.32,
    },
    "W16×57": {
        "tipo": "W", "descripcion": "Perfil W — vigas de entrepiso",
        "A": 107.7,   "Ix": 21220.0, "Iy": 1650.0,
        "Sx": 1540.0, "Sy": 274.0,   "Zx": 1739.0, "Zy": 422.0,
        "rx": 14.07,  "ry": 3.91,    "peso": 84.8,
        "d": 41.91,   "bf": 18.03,
    },
    "W18×76": {
        "tipo": "W", "descripcion": "Perfil W — vigas principales de gran luz",
        "A": 143.2,   "Ix": 37700.0, "Iy": 2620.0,
        "Sx": 2460.0, "Sy": 385.0,   "Zx": 2790.0, "Zy": 593.0,
        "rx": 16.23,  "ry": 4.27,    "peso": 113.0,
        "d": 47.50,   "bf": 28.07,
    },
    "W24×94": {
        "tipo": "W", "descripcion": "Perfil W — marcos resistentes a momento",
        "A": 178.1,   "Ix": 86800.0, "Iy": 4380.0,
        "Sx": 4620.0, "Sy": 552.0,   "Zx": 5240.0, "Zy": 852.0,
        "rx": 22.07,  "ry": 4.95,    "peso": 140.0,
        "d": 60.96,   "bf": 22.86,
    },
    # ── Perfiles HSS (Sección Hueca) ─────────────
    "HSS4×4×1/4": {
        "tipo": "HSS", "descripcion": "Sección hueca cuadrada — columnas livianas",
        "A": 28.71,   "Ix": 680.0,   "Iy": 680.0,
        "Sx": 170.0,  "Sy": 170.0,   "Zx": 200.0,  "Zy": 200.0,
        "rx": 4.87,   "ry": 4.87,    "peso": 22.5,
        "d": 10.16,   "bf": 10.16,
    },
    "HSS6×6×3/8": {
        "tipo": "HSS", "descripcion": "Sección hueca cuadrada — columnas medianas",
        "A": 55.48,   "Ix": 3040.0,  "Iy": 3040.0,
        "Sx": 623.0,  "Sy": 623.0,   "Zx": 737.0,  "Zy": 737.0,
        "rx": 7.41,   "ry": 7.41,    "peso": 43.6,
        "d": 15.24,   "bf": 15.24,
    },
    # ── Perfil Canal (C) ──────────────────────────
    "C10×30": {
        "tipo": "C", "descripcion": "Canal estándar — correas y elementos secundarios",
        "A": 56.77,   "Ix": 6920.0,  "Iy": 371.0,
        "Sx": 800.0,  "Sy": 107.0,   "Zx": 925.0,  "Zy": 196.0,
        "rx": 11.05,  "ry": 2.56,    "peso": 44.6,
        "d": 25.40,   "bf": 7.75,
    },
    # ── Perfil L (Angular) ────────────────────────
    "L6×6×1/2": {
        "tipo": "L", "descripcion": "Angular de lados iguales — arriostramientos",
        "A": 71.61,   "Ix": 2100.0,  "Iy": 2100.0,
        "Sx": 295.0,  "Sy": 295.0,   "Zx": 341.0,  "Zy": 341.0,
        "rx": 5.41,   "ry": 5.41,    "peso": 56.2,
        "d": 15.24,   "bf": 15.24,
    },
}

# ─────────────────────────────────────────────────
# 4. PROPIEDADES DE MATERIALES
# ─────────────────────────────────────────────────
MATERIALES = {
    "ASTM A36": {
        "E": 200000.0,   # MPa
        "Fy": 250.0,     # MPa
        "Fu": 400.0,     # MPa
        "descripcion": "Acero estructural de uso general",
    },
    "ASTM A992": {
        "E": 200000.0,   # MPa
        "Fy": 345.0,     # MPa
        "Fu": 448.0,     # MPa
        "descripcion": "Acero para perfiles W de alta resistencia",
    },
    "ASTM A500 Gr. B": {
        "E": 200000.0,   # MPa
        "Fy": 317.0,     # MPa
        "Fu": 400.0,     # MPa
        "descripcion": "Acero para perfiles HSS",
    },
    "Personalizado": {
        "E": 200000.0,
        "Fy": 250.0,
        "Fu": 400.0,
        "descripcion": "Ingrese propiedades personalizadas",
    },
}

# ─────────────────────────────────────────────────
# 5. ECUACIONES DE RESISTENCIA DE MATERIALES
#    Condiciones de apoyo soportadas
# ─────────────────────────────────────────────────

def calcular_viga(L, tipo_apoyo, tipo_carga, magnitud, E, Ix, Sx):
    """
    Calcula momento máximo, cortante máximo y deflexión máxima
    para distintas condiciones de apoyo y tipos de carga.

    Parámetros
    ----------
    L        : float  — Longitud [m]
    tipo_apoyo: str   — Condición de borde
    tipo_carga: str   — 'Puntual (centro)' o 'Distribuida uniforme'
    magnitud : float  — Fuerza total [kN] o intensidad [kN/m]
    E        : float  — Módulo de elasticidad [MPa → kN/m²]
    Ix       : float  — Momento de inercia [cm⁴ → m⁴]
    Sx       : float  — Módulo de sección elástico [cm³ → m³]

    Retorna
    -------
    dict con Mmax, Vmax, delta_max, diagramas x/M/V/delta
    """
    # Conversión de unidades
    E_kNm2 = E * 1_000.0           # MPa  → kN/m²
    Ix_m4  = Ix * 1e-8             # cm⁴  → m⁴
    Sx_m3  = Sx * 1e-6             # cm³  → m³
    EI     = E_kNm2 * Ix_m4        # kN·m²

    n_pts  = 300
    x      = np.linspace(0, L, n_pts)

    # ── Simplemente apoyada ────────────────────────────────────────────
    if tipo_apoyo == "Simplemente apoyada":
        if tipo_carga == "Puntual (centro)":
            P = magnitud
            Mmax   = P * L / 4.0
            Vmax   = P / 2.0
            delta_max = (P * L**3) / (48.0 * EI)

            M = np.where(x <= L/2,
                          (P/2) * x,
                          (P/2) * (L - x))
            V = np.where(x <= L/2,
                          np.full_like(x,  P/2),
                          np.full_like(x, -P/2))
            delta = np.where(x <= L/2,
                              (P * x / (48.0*EI)) * (3*L**2 - 4*x**2),
                              (P * (L-x) / (48.0*EI)) * (3*L**2 - 4*(L-x)**2))
        else:  # Distribuida uniforme
            w = magnitud
            Mmax   = w * L**2 / 8.0
            Vmax   = w * L / 2.0
            delta_max = (5 * w * L**4) / (384.0 * EI)

            M     = (w * x / 2.0) * (L - x)
            V     = w * (L/2.0 - x)
            delta = (w * x / (24.0 * EI)) * (L**3 - 2*L*x**2 + x**3)

    # ── Empotrada–Libre (voladizo) ─────────────────────────────────────
    elif tipo_apoyo == "Empotrada–Libre (voladizo)":
        if tipo_carga == "Puntual (centro)":
            # Carga en extremo libre (se trata como carga en punta)
            P = magnitud
            Mmax   = P * L
            Vmax   = P
            delta_max = (P * L**3) / (3.0 * EI)

            M     = -P * (L - x)       # momento negativo en empotramiento
            V     = np.full_like(x, P)
            delta = (P / (6.0*EI)) * (3*L*x**2 - x**3)
        else:
            w = magnitud
            Mmax   = w * L**2 / 2.0
            Vmax   = w * L
            delta_max = (w * L**4) / (8.0 * EI)

            M     = -(w / 2.0) * (L - x)**2
            V     = w * (L - x)
            delta = (w / (24.0*EI)) * (6*L**2*x**2 - 4*L*x**3 + x**4)

    # ── Empotrada–Empotrada ───────────────────────────────────────────
    elif tipo_apoyo == "Empotrada–Empotrada":
        if tipo_carga == "Puntual (centro)":
            P = magnitud
            Mmax   = P * L / 8.0       # Momento en centro (positivo)
            Vmax   = P / 2.0
            delta_max = (P * L**3) / (192.0 * EI)

            # M(x): negativos en apoyos, positivo en centro
            M = np.where(x <= L/2,
                          P * x / 2.0 - P * L / 8.0,
                          P * (L-x) / 2.0 - P * L / 8.0)
            V = np.where(x <= L/2,
                          np.full_like(x,  P/2),
                          np.full_like(x, -P/2))
            delta = np.where(x <= L/2,
                              (P * x**2 / (48.0*EI)) * (3*L - 4*x),
                              (P * (L-x)**2 / (48.0*EI)) * (3*L - 4*(L-x)))
        else:
            w = magnitud
            Mmax   = w * L**2 / 24.0   # centro (positivo máx)
            Mfijo  = w * L**2 / 12.0   # en apoyos (negativo)
            Mmax   = Mfijo             # el absoluto mayor es en apoyos
            Vmax   = w * L / 2.0
            delta_max = (w * L**4) / (384.0 * EI)

            M     = (w * x / 2.0) * (L - x) - (w * L**2 / 12.0)
            V     = w * (L/2.0 - x)
            delta = (w * x**2 * (L - x)**2) / (24.0 * EI)

    # ── Empotrada–Apoyada ─────────────────────────────────────────────
    elif tipo_apoyo == "Empotrada–Apoyada":
        if tipo_carga == "Distribuida uniforme":
            w = magnitud
            R_A    = 5 * w * L / 8.0
            R_B    = 3 * w * L / 8.0
            Mmax   = w * L**2 / 8.0        # en empotramiento
            Vmax   = R_A
            delta_max = (w * L**4) / (185.0 * EI)

            M     = R_A * x - w * x**2 / 2.0
            M[0]  = -w * L**2 / 8.0        # momento en empotramiento
            V     = R_A - w * x
            # Deflexión aproximada
            delta = (w / (48.0*EI)) * (3*L*x**3 - 5*x**4/L - L**2*x + L**4/(16))
            delta = np.abs(delta)
        else:
            P  = magnitud
            R_A = 11 * P / 16.0
            Mmax  = P * L * 5 / 32.0
            Vmax  = R_A
            delta_max = (P * L**3) / (108.0 * EI)

            M = np.where(x <= L/2,
                          R_A * x,
                          R_A * x - P * (x - L/2))
            V = np.where(x <= L/2,
                          np.full_like(x,  R_A),
                          np.full_like(x,  R_A - P))
            delta = (P * (3*L - 4*x/L)) * np.where(x <= L/2,
                         x**2 * (3*L - 4*x) / (48.0*EI),
                         x * (3*L**2 - 5*x**2) / (48.0*EI))
            delta = np.abs(delta)

    return {
        "Mmax":      abs(Mmax),
        "Vmax":      abs(Vmax),
        "delta_max": abs(delta_max),
        "x":         x,
        "M":         M,
        "V":         V,
        "delta":     np.abs(delta),
        "EI":        EI,
    }


# ─────────────────────────────────────────────────
# 6. VERIFICACIONES AISC 360
# ─────────────────────────────────────────────────

def verificar_aisc(resultados, perfil, Fy, L, limite_flecha):
    """
    Comprueba la demanda/capacidad (D/C) según AISC 360-22.

    Verificaciones:
    ───────────────
    ① Flexión   : σ_max ≤ φ·Fy  (φb = 0.90)
    ② Cortante  : τ_max ≤ φ·0.6·Fy  (φv = 1.00 para almas compactas)
    ③ Deflexión : Δmax ≤ L / limite_flecha
    """
    Mmax       = resultados["Mmax"]          # kN·m
    Vmax       = resultados["Vmax"]          # kN
    delta_max  = resultados["delta_max"]     # m
    Sx_m3      = perfil["Sx"] * 1e-6         # m³
    A_m2       = perfil["A"]  * 1e-4         # m²
    d_m        = perfil["d"]  * 1e-2         # m

    # ── ① Esfuerzo de flexión ────────────────────
    phi_b      = 0.90
    sigma_max  = Mmax / Sx_m3 / 1000.0       # MPa  (kN/m² → MPa / 1000)
    Mn_MPa     = phi_b * Fy                  # MPa
    DC_flex    = sigma_max / Mn_MPa

    # ── ② Esfuerzo cortante (sección llena, conservador) ─
    phi_v      = 1.00
    tau_max    = (1.5 * Vmax / A_m2) / 1000.0   # MPa aprox. (rect. equiv.)
    Vn_MPa     = phi_v * 0.6 * Fy
    DC_cort    = tau_max / Vn_MPa

    # ── ③ Deflexión admisible ─────────────────────
    delta_adm  = L / limite_flecha            # m
    DC_defl    = delta_max / delta_adm

    return {
        "sigma_max":  sigma_max,
        "tau_max":    tau_max,
        "DC_flex":    DC_flex,
        "DC_cort":    DC_cort,
        "DC_defl":    DC_defl,
        "delta_adm":  delta_adm * 1000.0,    # → mm
        "Mn_MPa":     Mn_MPa,
        "Vn_MPa":     Vn_MPa,
    }


# ─────────────────────────────────────────────────
# 7. FUNCIÓN DE GRÁFICOS (Plotly)
# ─────────────────────────────────────────────────

def crear_graficos(resultados, L, tipo_apoyo):
    """
    Genera un panel de 3 gráficos:
    [1] Esquema del elemento con cargas
    [2] Diagrama de Momentos Flectores (DMF)
    [3] Curva de Deflexión
    """
    x     = resultados["x"]
    M     = resultados["M"]
    V     = resultados["V"]
    delta = resultados["delta"] * 1000.0    # m → mm

    colores = {
        "fondo":      "#0f1117",
        "fondo_plot": "#1a1f2e",
        "grid":       "#2d3250",
        "texto":      "#8892b0",
        "acento1":    "#64ffda",   # Momentos
        "acento2":    "#ff6b6b",   # Cortante
        "acento3":    "#57cbff",   # Deflexión
        "neutral":    "#ccd6f6",
    }

    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=("Diagrama de Momentos Flectores  M(x)",
                        "Diagrama de Fuerza Cortante  V(x)",
                        "Curva de Deflexión  δ(x)"),
        vertical_spacing=0.10,
        row_heights=[0.35, 0.30, 0.35],
    )

    # ── Momentos ──────────────────────────────────
    fig.add_trace(go.Scatter(
        x=x, y=M,
        name="M(x)",
        line=dict(color=colores["acento1"], width=2.5),
        fill="tozeroy",
        fillcolor="rgba(100,255,218,0.12)",
        hovertemplate="x = %{x:.2f} m<br>M = %{y:.2f} kN·m<extra></extra>",
    ), row=1, col=1)
    fig.add_hline(y=0, line_color=colores["grid"], line_width=1, row=1, col=1)
    # Marca el máximo
    idx_Mmax = np.argmax(np.abs(M))
    fig.add_trace(go.Scatter(
        x=[x[idx_Mmax]], y=[M[idx_Mmax]],
        mode="markers+text",
        marker=dict(color=colores["acento1"], size=10, symbol="circle"),
        text=[f" M_max = {M[idx_Mmax]:.2f} kN·m"],
        textposition="top right",
        textfont=dict(color=colores["acento1"], size=11),
        name="Mmax",
        showlegend=False,
    ), row=1, col=1)

    # ── Cortante ──────────────────────────────────
    fig.add_trace(go.Scatter(
        x=x, y=V,
        name="V(x)",
        line=dict(color=colores["acento2"], width=2.0),
        fill="tozeroy",
        fillcolor="rgba(255,107,107,0.10)",
        hovertemplate="x = %{x:.2f} m<br>V = %{y:.2f} kN<extra></extra>",
    ), row=2, col=1)
    fig.add_hline(y=0, line_color=colores["grid"], line_width=1, row=2, col=1)

    # ── Deflexión ─────────────────────────────────
    fig.add_trace(go.Scatter(
        x=x, y=-delta,          # invertido para mostrar hacia abajo
        name="δ(x)",
        line=dict(color=colores["acento3"], width=2.5),
        fill="tozeroy",
        fillcolor="rgba(87,203,255,0.10)",
        hovertemplate="x = %{x:.2f} m<br>δ = %{y:.2f} mm<extra></extra>",
    ), row=3, col=1)
    idx_dmax = np.argmax(delta)
    fig.add_trace(go.Scatter(
        x=[x[idx_dmax]], y=[-delta[idx_dmax]],
        mode="markers+text",
        marker=dict(color=colores["acento3"], size=10, symbol="circle"),
        text=[f" δ_max = {delta[idx_dmax]:.2f} mm"],
        textposition="top right",
        textfont=dict(color=colores["acento3"], size=11),
        showlegend=False,
    ), row=3, col=1)

    # ── Formato global ────────────────────────────
    fig.update_layout(
        height=680,
        paper_bgcolor=colores["fondo"],
        plot_bgcolor=colores["fondo_plot"],
        font=dict(color=colores["texto"], family="Inter, sans-serif"),
        margin=dict(l=60, r=40, t=60, b=20),
        legend=dict(
            bgcolor="#1e2130",
            bordercolor=colores["grid"],
            borderwidth=1,
            font=dict(size=11),
        ),
        hoverlabel=dict(
            bgcolor="#1e2130",
            bordercolor=colores["acento1"],
            font=dict(color="#e6f1ff"),
        ),
    )

    # Ejes y grillas
    for fila in [1, 2, 3]:
        fig.update_xaxes(
            showgrid=True, gridcolor=colores["grid"], gridwidth=0.5,
            zeroline=True, zerolinecolor=colores["neutral"], zerolinewidth=1,
            tickfont=dict(color=colores["texto"]),
            title_text="Longitud x [m]" if fila == 3 else "",
            title_font=dict(color=colores["texto"]),
            row=fila, col=1,
        )

    fig.update_yaxes(
        showgrid=True, gridcolor=colores["grid"], gridwidth=0.5,
        zeroline=True, zerolinecolor=colores["neutral"],
        tickfont=dict(color=colores["texto"]),
        title_text="M [kN·m]", title_font=dict(color=colores["acento1"]),
        row=1, col=1,
    )
    fig.update_yaxes(
        showgrid=True, gridcolor=colores["grid"], gridwidth=0.5,
        zeroline=True, zerolinecolor=colores["neutral"],
        tickfont=dict(color=colores["texto"]),
        title_text="V [kN]", title_font=dict(color=colores["acento2"]),
        row=2, col=1,
    )
    fig.update_yaxes(
        showgrid=True, gridcolor=colores["grid"], gridwidth=0.5,
        zeroline=True, zerolinecolor=colores["neutral"],
        tickfont=dict(color=colores["texto"]),
        title_text="δ [mm]", title_font=dict(color=colores["acento3"]),
        row=3, col=1,
    )

    # Títulos de subplots en color
    colores_titulos = [colores["acento1"], colores["acento2"], colores["acento3"]]
    for ann, color in zip(fig.layout.annotations, colores_titulos):
        ann.font.color  = color
        ann.font.size   = 12
        ann.font.family = "Inter, sans-serif"

    return fig


# ─────────────────────────────────────────────────
# 8. INTERFAZ PRINCIPAL — SIDEBAR
# ─────────────────────────────────────────────────

def render_badge(dc_ratio):
    """Retorna HTML de badge según relación D/C."""
    if dc_ratio <= 0.85:
        return f'<span class="badge-pass">✔ CUMPLE  D/C = {dc_ratio:.2f}</span>'
    elif dc_ratio <= 1.00:
        return f'<span class="badge-warn">⚠ LÍMITE  D/C = {dc_ratio:.2f}</span>'
    else:
        return f'<span class="badge-fail">✖ FALLA   D/C = {dc_ratio:.2f}</span>'


def main():
    # ── Encabezado ────────────────────────────────
    col_logo, col_titulo = st.columns([0.08, 0.92])
    with col_logo:
        st.markdown("# 🏗️")
    with col_titulo:
        st.markdown('<p class="main-title">Simulador Estructural de Acero</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="main-subtitle">Cálculo de esfuerzos y desplazamientos · '
            'Verificación según <strong>AISC 360-22</strong></p>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ─────────────────────────────────────────────
    # SIDEBAR — CONTROLES DE ENTRADA
    # ─────────────────────────────────────────────
    with st.sidebar:
        st.markdown("## ⚙️ Parámetros de entrada")
        st.markdown("---")

        # ── A. Selección de perfil ─────────────────
        st.markdown("### 📐 Perfil Estructural")
        perfil_nombre = st.selectbox(
            "Seleccionar perfil AISC:",
            options=list(PERFILES_AISC.keys()),
            index=1,   # W12×26 por defecto
            help="Biblioteca de perfiles comerciales según tablas AISC",
        )
        perfil = PERFILES_AISC[perfil_nombre]
        st.caption(f"*{perfil['descripcion']}*")

        st.markdown("---")

        # ── B. Geometría ──────────────────────────
        st.markdown("### 📏 Geometría")
        col_L, col_u = st.columns([0.70, 0.30])
        with col_L:
            L_val = st.number_input(
                "Longitud (L):", min_value=0.5, max_value=30.0,
                value=6.0, step=0.25,
            )
        with col_u:
            unidad_L = st.selectbox("Unidad:", ["m", "ft"], index=0)

        # Conversión a metros
        L = L_val if unidad_L == "m" else L_val * 0.3048

        st.markdown("---")

        # ── C. Condición de apoyo ─────────────────
        st.markdown("### 🔩 Condición de Apoyo")
        tipo_apoyo = st.selectbox(
            "Condición de borde:",
            options=[
                "Simplemente apoyada",
                "Empotrada–Libre (voladizo)",
                "Empotrada–Empotrada",
                "Empotrada–Apoyada",
            ],
            help="Condición de borde que controla las ecuaciones de M, V y δ",
        )

        st.markdown("---")

        # ── D. Carga ──────────────────────────────
        st.markdown("### ⬇️ Carga Aplicada")
        tipo_carga = st.radio(
            "Tipo de carga:",
            ["Puntual (centro)", "Distribuida uniforme"],
            horizontal=False,
        )

        col_q, col_qu = st.columns([0.65, 0.35])
        with col_q:
            if tipo_carga == "Puntual (centro)":
                label_carga = "Carga puntual P:"
                help_carga  = "Fuerza concentrada aplicada en el centro del elemento"
            else:
                label_carga = "Carga distribuida w:"
                help_carga  = "Intensidad de carga uniforme a lo largo del elemento"

            magnitud_val = st.number_input(
                label_carga, min_value=0.1, max_value=10000.0,
                value=50.0 if tipo_carga == "Puntual (centro)" else 20.0,
                step=1.0, help=help_carga,
            )
        with col_qu:
            unidad_carga = st.selectbox(
                "Unidad:",
                ["kN", "kgf", "kips"] if tipo_carga == "Puntual (centro)"
                else ["kN/m", "kgf/m", "kips/ft"],
                index=0,
            )

        # Conversión a kN (o kN/m)
        if tipo_carga == "Puntual (centro)":
            conv = {"kN": 1.0, "kgf": 0.009807, "kips": 4.44822}
        else:
            conv = {"kN/m": 1.0, "kgf/m": 0.009807, "kips/ft": 14.5939}

        magnitud = magnitud_val * conv.get(unidad_carga, 1.0)

        st.markdown("---")

        # ── E. Material ───────────────────────────
        st.markdown("### 🔬 Material")
        mat_nombre = st.selectbox(
            "Acero:",
            options=list(MATERIALES.keys()),
            index=1,   # A992 por defecto
        )
        mat = MATERIALES[mat_nombre]

        if mat_nombre == "Personalizado":
            E_val  = st.number_input("E (MPa):", value=200000.0, min_value=10000.0)
            Fy_val = st.number_input("Fy (MPa):", value=250.0,   min_value=50.0)
            Fu_val = st.number_input("Fu (MPa):", value=400.0,   min_value=100.0)
        else:
            E_val  = st.number_input("E (MPa):", value=mat["E"],  min_value=10000.0)
            Fy_val = st.number_input("Fy (MPa):", value=mat["Fy"], min_value=50.0)
            Fu_val = mat["Fu"]

        st.markdown("---")

        # ── F. Límite de deflexión ────────────────
        st.markdown("### 📊 Criterio de Deflexión")
        limite_opcion = st.select_slider(
            "Límite admisible:",
            options=["L/180", "L/240", "L/360", "L/480", "L/600"],
            value="L/360",
            help="Límites AISC: L/360 cargas vivas, L/240 cargas totales",
        )
        limite_flecha = int(limite_opcion.split("/")[1])

        st.markdown("---")
        st.markdown(
            "<small style='color:#4a5568'>AISC 360-22 · Resistencia de Materiales<br>"
            "Todas las ecuaciones verificadas manualmente</small>",
            unsafe_allow_html=True,
        )

    # ─────────────────────────────────────────────
    # 9. MOTOR DE CÁLCULO
    # ─────────────────────────────────────────────
    res  = calcular_viga(L, tipo_apoyo, tipo_carga, magnitud, E_val,
                          perfil["Ix"], perfil["Sx"])
    aisc = verificar_aisc(res, perfil, Fy_val, L, limite_flecha)

    Mmax      = res["Mmax"]
    Vmax      = res["Vmax"]
    delta_max = res["delta_max"] * 1000.0    # m → mm

    # ─────────────────────────────────────────────
    # 10. PANEL DE RESULTADOS — LAYOUT
    # ─────────────────────────────────────────────
    col_props, col_res, col_aisc = st.columns([0.28, 0.38, 0.34])

    # ── Columna 1: Propiedades del perfil ─────────
    with col_props:
        st.markdown('<div class="section-header">📐 Propiedades del Perfil</div>',
                    unsafe_allow_html=True)

        props_data = {
            "Perfil":     perfil_nombre,
            "Tipo":       perfil["tipo"],
            "A":          f"{perfil['A']:.2f} cm²",
            "Iₓ":         f"{perfil['Ix']:,.0f} cm⁴",
            "Iᵧ":         f"{perfil['Iy']:,.0f} cm⁴",
            "Sₓ":         f"{perfil['Sx']:,.0f} cm³",
            "Sᵧ":         f"{perfil['Sy']:,.0f} cm³",
            "Zₓ":         f"{perfil['Zx']:,.0f} cm³",
            "rₓ":         f"{perfil['rx']:.2f} cm",
            "rᵧ":         f"{perfil['ry']:.2f} cm",
            "Peso":       f"{perfil['peso']:.1f} kg/m",
        }

        tabla_html = '<table class="prop-table">'
        for k, v in props_data.items():
            tabla_html += f"<tr><td>{k}</td><td>{v}</td></tr>"
        tabla_html += "</table>"
        st.markdown(tabla_html, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">🔬 Material</div>',
                    unsafe_allow_html=True)
        mat_html = f"""<table class="prop-table">
            <tr><td>Acero</td><td>{mat_nombre}</td></tr>
            <tr><td>E</td><td>{E_val:,.0f} MPa</td></tr>
            <tr><td>Fᵧ</td><td>{Fy_val:.0f} MPa</td></tr>
            <tr><td>Fu</td><td>{Fu_val:.0f} MPa</td></tr>
        </table>"""
        st.markdown(mat_html, unsafe_allow_html=True)

    # ── Columna 2: Resultados de esfuerzos ────────
    with col_res:
        st.markdown('<div class="section-header">📊 Resultados de Esfuerzos y Desplazamientos</div>',
                    unsafe_allow_html=True)

        # Tarjetas de métricas principales
        def metric_card(label, value, unit):
            return f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}<span class="metric-unit">{unit}</span></div>
            </div>"""

        st.markdown(metric_card(
            "Momento Máximo  M_max",
            f"{Mmax:.2f}", "kN·m"),
            unsafe_allow_html=True)

        st.markdown(metric_card(
            "Cortante Máximo  V_max",
            f"{Vmax:.2f}", "kN"),
            unsafe_allow_html=True)

        st.markdown(metric_card(
            "Deflexión Máxima  δ_max",
            f"{delta_max:.2f}", "mm"),
            unsafe_allow_html=True)

        st.markdown(metric_card(
            "Esfuerzo Flexión  σ_max = M / Sₓ",
            f"{aisc['sigma_max']:.1f}", "MPa"),
            unsafe_allow_html=True)

        st.markdown(metric_card(
            "Esfuerzo Cortante  τ_max ≈ 1.5V / A",
            f"{aisc['tau_max']:.1f}", "MPa"),
            unsafe_allow_html=True)

        # Configuración del elemento
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">⚙️ Configuración del Elemento</div>',
                    unsafe_allow_html=True)

        config_html = f"""<table class="prop-table">
            <tr><td>Longitud</td><td>{L:.2f} m</td></tr>
            <tr><td>Apoyo</td><td>{tipo_apoyo}</td></tr>
            <tr><td>Tipo de carga</td><td>{tipo_carga}</td></tr>
            <tr><td>Magnitud carga</td><td>{magnitud:.2f} {unidad_carga}</td></tr>
            <tr><td>Peso propio viga</td><td>{perfil['peso']:.1f} kg/m</td></tr>
            <tr><td>Δ admisible ({limite_opcion})</td><td>{aisc['delta_adm']:.1f} mm</td></tr>
        </table>"""
        st.markdown(config_html, unsafe_allow_html=True)

    # ── Columna 3: Verificación AISC ──────────────
    with col_aisc:
        st.markdown('<div class="section-header">✅ Verificación AISC 360-22</div>',
                    unsafe_allow_html=True)

        # ─ Flexión ─
        st.markdown("**① Verificación por Flexión**")
        st.markdown(f"σ_max = **{aisc['sigma_max']:.1f} MPa** &nbsp;|&nbsp; "
                    f"φ·Fy = **{aisc['Mn_MPa']:.1f} MPa**",
                    unsafe_allow_html=True)
        st.markdown(render_badge(aisc["DC_flex"]), unsafe_allow_html=True)

        # Barra de progreso D/C
        dc_f = min(aisc["DC_flex"], 1.5)
        color_f = "#64ffda" if dc_f <= 0.85 else ("#ffd166" if dc_f <= 1.0 else "#ff6b6b")
        st.markdown(
            f'<div style="background:#1e2130;border-radius:4px;height:8px;margin:6px 0 16px">'
            f'<div style="background:{color_f};width:{min(dc_f*100,100):.0f}%;height:8px;border-radius:4px;transition:width 0.5s"></div>'
            f'</div>', unsafe_allow_html=True)

        # ─ Cortante ─
        st.markdown("**② Verificación por Cortante**")
        st.markdown(f"τ_max = **{aisc['tau_max']:.1f} MPa** &nbsp;|&nbsp; "
                    f"φ·0.6Fy = **{aisc['Vn_MPa']:.1f} MPa**",
                    unsafe_allow_html=True)
        st.markdown(render_badge(aisc["DC_cort"]), unsafe_allow_html=True)

        dc_c = min(aisc["DC_cort"], 1.5)
        color_c = "#64ffda" if dc_c <= 0.85 else ("#ffd166" if dc_c <= 1.0 else "#ff6b6b")
        st.markdown(
            f'<div style="background:#1e2130;border-radius:4px;height:8px;margin:6px 0 16px">'
            f'<div style="background:{color_c};width:{min(dc_c*100,100):.0f}%;height:8px;border-radius:4px"></div>'
            f'</div>', unsafe_allow_html=True)

        # ─ Deflexión ─
        st.markdown(f"**③ Verificación por Deflexión  ({limite_opcion})**")
        st.markdown(f"δ_max = **{delta_max:.2f} mm** &nbsp;|&nbsp; "
                    f"δ_adm = **{aisc['delta_adm']:.1f} mm**",
                    unsafe_allow_html=True)
        st.markdown(render_badge(aisc["DC_defl"]), unsafe_allow_html=True)

        dc_d = min(aisc["DC_defl"], 1.5)
        color_d = "#64ffda" if dc_d <= 0.85 else ("#ffd166" if dc_d <= 1.0 else "#ff6b6b")
        st.markdown(
            f'<div style="background:#1e2130;border-radius:4px;height:8px;margin:6px 0 16px">'
            f'<div style="background:{color_d};width:{min(dc_d*100,100):.0f}%;height:8px;border-radius:4px"></div>'
            f'</div>', unsafe_allow_html=True)

        # ─ Veredicto global ─
        all_pass = all(v <= 1.0 for v in [aisc["DC_flex"], aisc["DC_cort"], aisc["DC_defl"]])
        all_good = all(v <= 0.85 for v in [aisc["DC_flex"], aisc["DC_cort"], aisc["DC_defl"]])

        st.markdown("<br>", unsafe_allow_html=True)
        if all_good:
            st.success(f"✅ **{perfil_nombre} — CUMPLE TODOS LOS CRITERIOS AISC**\n\n"
                       "El perfil tiene capacidad de reserva suficiente.")
        elif all_pass:
            st.warning(f"⚠️ **{perfil_nombre} — CUMPLE (cerca del límite)**\n\n"
                       "Revise las relaciones D/C cercanas a 1.0.")
        else:
            st.error(f"❌ **{perfil_nombre} — FALLA AL MENOS UN CRITERIO**\n\n"
                     "Seleccione un perfil de mayor capacidad.")

        # Notas normativas
        with st.expander("📋 Notas normativas AISC 360-22"):
            st.markdown("""
**Flexión (Cap. F):**
- φ_b = 0.90 (LRFD)
- M_n calculado con sección compacta (σ ≤ φ·Fy)

**Cortante (Cap. G):**
- φ_v = 1.00 para almas compactas (h/tw ≤ 2.24√(E/Fy))
- V_n = 0.6·Fy·A_w

**Deflexiones (Cap. L):**
- Δ_viva ≤ L/360 (uso típico de piso)
- Δ_total ≤ L/240 (criterio de daño a acabados)
- Δ_techo ≤ L/180

**Filosofía de diseño:** LRFD (Load and Resistance Factor Design)
""")

    # ─────────────────────────────────────────────
    # 11. GRÁFICOS
    # ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown("## 📈 Diagramas Estructurales")

    fig = crear_graficos(res, L, tipo_apoyo)
    st.plotly_chart(fig, use_container_width=True)

    # ─────────────────────────────────────────────
    # 12. TABLA DE COMPARACIÓN DE PERFILES
    # ─────────────────────────────────────────────
    st.markdown("---")
    with st.expander("📊 Comparativa completa de perfiles disponibles"):
        filas = []
        for nombre, p in PERFILES_AISC.items():
            r_comp = calcular_viga(L, tipo_apoyo, tipo_carga, magnitud, E_val, p["Ix"], p["Sx"])
            a_comp = verificar_aisc(r_comp, p, Fy_val, L, limite_flecha)
            estado = (
                "✔ CUMPLE" if all(v <= 1.0 for v in [a_comp["DC_flex"], a_comp["DC_cort"], a_comp["DC_defl"]])
                else "✖ FALLA"
            )
            filas.append({
                "Perfil":        nombre,
                "Tipo":          p["tipo"],
                "A [cm²]":       p["A"],
                "Iₓ [cm⁴]":     p["Ix"],
                "Sₓ [cm³]":     p["Sx"],
                "Peso [kg/m]":   p["peso"],
                "δ_max [mm]":    round(r_comp["delta_max"] * 1000, 2),
                "D/C Flex.":     round(a_comp["DC_flex"], 3),
                "D/C Defl.":     round(a_comp["DC_defl"], 3),
                "Estado":        estado,
            })

        df = pd.DataFrame(filas)

        def style_estado(val):
            if "CUMPLE" in str(val):
                return "background-color: #0d4f3c; color: #64ffda; font-weight: bold"
            else:
                return "background-color: #5a1a1a; color: #ff6b6b; font-weight: bold"

        def style_dc(val):
            try:
                v = float(val)
                if v <= 0.85:
                    return "color: #64ffda"
                elif v <= 1.0:
                    return "color: #ffd166"
                else:
                    return "color: #ff6b6b"
            except:
                return ""

        styled_df = (
            df.style
            .applymap(style_estado, subset=["Estado"])
            .applymap(style_dc, subset=["D/C Flex.", "D/C Defl."])
            .highlight_between(
                subset=["D/C Flex.", "D/C Defl."],
                left=1.0, right=10.0,
                color="#5a1a1a",
            )
        )

        st.dataframe(styled_df, use_container_width=True, height=420)
        st.caption(
            f"⚠️ Resultados para: L = {L:.2f} m · {tipo_apoyo} · {tipo_carga} "
            f"· {magnitud:.2f} {unidad_carga} · Acero {mat_nombre} · Límite {limite_opcion}"
        )

    # ─────────────────────────────────────────────
    # 13. PIE DE PÁGINA
    # ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        '<p style="color:#4a5568;font-size:0.75rem;text-align:center">'
        '🏗️ <strong>Simulador Estructural AISC</strong> · '
        'Basado en AISC 360-22 y Resistencia de Materiales · '
        'Resultados de referencia — siempre verifique con ingeniería certificada'
        '</p>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────
# PUNTO DE ENTRADA
# ─────────────────────────────────────────────────
if __name__ == "__main__":
    main()
