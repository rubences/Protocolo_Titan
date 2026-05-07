import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from protocolo_titan.config import GSMConfig, ConvoyScenario, CampScenario, AnalyzerConfig
from protocolo_titan.radio_access import gsm_access_summary
from protocolo_titan.scenario_a import analyze_convoy_mobility, analyze_convoy_fading
from protocolo_titan.scenario_b import analyze_camp_base


st.set_page_config(page_title="Protocolo Titán", layout="wide")

st.title("Protocolo Titán — GSM/EDGE Tactical Network Lab")
st.write("Simulador docente para movilidad, fading, planificación celular e instrumentación.")

with st.sidebar:
    st.header("GSM/EDGE")
    fc_mhz = st.number_input("Frecuencia central (MHz)", min_value=100.0, value=900.0, step=10.0)
    timeslot_us = st.number_input("Timeslot GSM (µs)", min_value=1.0, value=577.0, step=1.0)

    st.header("Escenario A")
    speed_low = st.number_input("Velocidad baja (km/h)", min_value=0.0, value=50.0, step=10.0)
    speed_high = st.number_input("Velocidad alta (km/h)", min_value=0.0, value=250.0, step=10.0)

    st.header("Escenario B")
    total_carriers = st.number_input("Portadoras totales", min_value=1, value=24, step=1)
    cluster_size = st.number_input("Clúster N", min_value=1, value=4, step=1)
    radius_km = st.number_input("Radio celda campamento (km)", min_value=0.1, value=1.5, step=0.1)

    st.header("Instrumentación")
    nf_db = st.number_input("Figura de ruido NF (dB)", min_value=0.0, value=6.0, step=0.5)

gsm = GSMConfig(carrier_frequency_hz=fc_mhz * 1e6, timeslot_duration_s=timeslot_us * 1e-6)
convoy = ConvoyScenario(speeds_kmh=(speed_low, speed_high))
camp = CampScenario(total_carriers=int(total_carriers), cluster_size=int(cluster_size), cell_radius_km=radius_km)
analyzer = AnalyzerConfig(noise_figure_db=nf_db)

tab0, tab1, tab2, tab3 = st.tabs(["FDMA/TDMA", "Escenario A", "Escenario B", "RED/RBW"])

with tab0:
    st.subheader("Capa física y acceso")
    st.dataframe(gsm_access_summary(gsm), use_container_width=True)
    st.markdown(
        "- FDMA: separación de portadoras de 200 kHz.\n"
        "- TDMA: 8 timeslots por trama.\n"
        "- BCCH/TCH se analizan en la planificación del campamento."
    )

with tab1:
    st.subheader("Convoy: Doppler, coherencia y fading")
    mobility = analyze_convoy_mobility(convoy, gsm)
    fading_summary, traces = analyze_convoy_fading(convoy, gsm)
    st.dataframe(mobility, use_container_width=True)
    st.dataframe(fading_summary, use_container_width=True)

    selected_trace = st.selectbox("Traza de fading", list(traces.keys()))
    st.line_chart(traces[selected_trace], x="time_us", y="envelope_normalized")

with tab2:
    st.subheader("Campamento: reutilización, ARFCNs y canales")
    try:
        results = analyze_camp_base(camp, gsm, analyzer)
        st.dataframe(results["frequency_planning"], use_container_width=True)
        st.dataframe(results["logical_channels"], use_container_width=True)
    except ValueError as exc:
        st.error(str(exc))

with tab3:
    st.subheader("Certificación: ruido integrado y checklist RED")
    results = analyze_camp_base(camp, gsm, analyzer)
    st.dataframe(results["rbw_noise"], use_container_width=True)
    st.line_chart(results["rbw_noise"], x="rbw_khz", y="noise_floor_dbm")
    st.dataframe(results["red_checklist"], use_container_width=True)
