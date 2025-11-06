"""
AgriEase — Soil & Irrigation Assistant
-------------------------------------
Beginner‑friendly, single‑file Streamlit app for agricultural engineering students.

How to run locally
------------------
1) Install dependencies:
   pip install -r requirements.txt

2) Start the app:
   streamlit run app.py

Deploy on Streamlit Community Cloud
-----------------------------------
- Push this file (named app.py) and requirements.txt to a public GitHub repo.
- On https://streamlit.io/cloud, create an app pointing to app.py.

requirements.txt
----------------
streamlit>=1.37
pandas>=2.0

Notes & disclaimer
------------------
This app provides simple rule‑based guidance for learning/demo purposes. It does not replace local agronomy advice.
"""

import os
import io
from datetime import date, datetime, timedelta
from typing import Dict, List, Tuple

import pandas as pd
import streamlit as st

# ----------------------------
# Page config & styling
# ----------------------------
st.set_page_config(
    page_title="AgriEase — Soil & Irrigation Assistant",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

PRIMARY = "#2f855a"  # Tailwind green-700 vibe
ACCENT = "#0ea5e9"    # sky-500
BG_SOFT = "#f8fafc"   # slate-50

st.markdown(
    f"""
    <style>
      body {{ color:#000000 !important; }}
      .stApp {{ background: linear-gradient(180deg, #e6f4ea 0%, #ffffff 70%); color:#000000 !important; }}
      .pill {{
        display:inline-block; padding:6px 12px; border-radius:999px; font-size:12px;
        border:1px solid #000000; background:#f0f7f2; margin-right:6px; color:#000000 !important;
      }}
      .soft-card {{
        border-radius: 18px; border:1px solid #000000; padding:20px; background:#f9fdfb;
        box-shadow: 0 6px 20px rgba(0,0,0,0.05); color:#000000 !important;
      }}
      .heading {{ font-weight:900; letter-spacing:-0.02em; color:#000000 !important; font-size:36px !important; text-shadow:0 0 2px rgba(0,0,0,0.4); }}
      .subtle {{ color:#000000 !important; }}
      .ok {{ color:#000000 !important; font-weight:600; }}
      .warn {{ color:#000000 !important; font-weight:600; }}
      .bad {{ color:#000000 !important; font-weight:600; }}
      .good {{ color:#000000 !important; font-weight:600; }}
      .footer-note {{ color:#000000 !important; font-size:12px; }}
      .metric-chip {{
        display:flex; gap:8px; align-items:center; padding:12px 14px; border-radius:14px;
        border:1px dashed #000000; background:#eef7f1; font-size:15px; color:#000000 !important;
      }}
</style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------
# Demo data & simple rules
# ----------------------------
CROPS: Dict[str, Dict] = {
    "Rice": {
        "water_need": "High",
        "npk_opt": {"N": (80, 120), "P": (40, 60), "K": (40, 60)},  # kg/ha (educational ranges)
        "stages": [
            ("Sowing", 15), ("Vegetative", 30), ("Tillering", 25), ("Flowering", 20), ("Maturity", 20)
        ],
    },
    "Wheat": {
        "water_need": "Medium",
        "npk_opt": {"N": (60, 100), "P": (30, 50), "K": (30, 50)},
        "stages": [
            ("Sowing", 10), ("Tillering", 25), ("Jointing", 25), ("Heading", 20), ("Maturity", 20)
        ],
    },
    "Maize": {
        "water_need": "Medium-High",
        "npk_opt": {"N": (80, 150), "P": (40, 80), "K": (40, 80)},
        "stages": [
            ("Planting", 10), ("Vegetative", 35), ("Silking", 20), ("Grain Fill", 25), ("Maturity", 20)
        ],
    },
    "Tomato": {
        "water_need": "Medium-High",
        "npk_opt": {"N": (100, 150), "P": (50, 80), "K": (80, 120)},
        "stages": [
            ("Transplant", 10), ("Vegetative", 20), ("Flowering", 25), ("Fruiting", 30), ("Harvest", 15)
        ],
    },
    "Groundnut": {
        "water_need": "Medium",
        "npk_opt": {"N": (15, 30), "P": (40, 60), "K": (30, 50)},
        "stages": [
            ("Sowing", 10), ("Vegetative", 30), ("Flowering", 25), ("Pegging", 20), ("Maturity", 20)
        ],
    },
}

FERT_GUIDE = {
    # very simplified – for beginner demo only
    "N": {
        "low": ("Apply 50–70 kg/acre urea split across stages.", "bad"),
        "mid": ("Apply ~25–40 kg/acre urea; split dosing.", "warn"),
        "ok": ("Maintain with small top dress if crop looks pale.", "ok"),
        "high": ("No N needed now; monitor for lodging risk.", "good"),
    },
    "P": {
        "low": ("Apply 25–35 kg/acre DAP/basal placement.", "bad"),
        "mid": ("Add 15–20 kg/acre DAP near root zone.", "warn"),
        "ok": ("P level is adequate; no extra basal needed.", "ok"),
        "high": ("Skip P; excessive P can lock micronutrients.", "good"),
    },
    "K": {
        "low": ("Apply 20–30 kg/acre MOP in 1–2 splits.", "bad"),
        "mid": ("Top up 10–15 kg/acre MOP.", "warn"),
        "ok": ("K level is adequate; small maintenance dose only.", "ok"),
        "high": ("Skip K; watch fruit quality/firmness.", "good"),
    },
}

WATER_TABLE = {
    # Approximate mm/day by temp band & need category (1 mm = 1 L/m²)
    "Low":    [(0, 25, 2), (25, 32, 3), (32, 100, 4)],
    "Medium": [(0, 25, 3), (25, 32, 4), (32, 100, 5.5)],
    "Medium-High": [(0, 25, 4), (25, 32, 5.5), (32, 100, 7)],
    "High":   [(0, 25, 5), (25, 32, 7), (32, 100, 9)],
}

# ----------------------------
# Utility functions
# ----------------------------

def classify_level(value: float, low: float, high: float) -> str:
    if value < low * 0.8:
        return "low"
    if value < low:
        return "mid"
    if low <= value <= high:
        return "ok"
    return "high"


def fert_reco(n: float, p: float, k: float, crop: str) -> List[Tuple[str, str, str]]:
    ranges = CROPS[crop]["npk_opt"]
    recs = []
    for key, val in zip(["N", "P", "K"], [n, p, k]):
        lo, hi = ranges[key]
        cls = classify_level(val, lo, hi)
        msg, tag = FERT_GUIDE[key][cls]
        recs.append((key, cls, msg))
    return recs


def irrigation_reco(crop: str, temp_c: float, stage: str, soil: str) -> Tuple[float, str]:
    need = CROPS[crop]["water_need"]
    base_mm = 4.0
    for lo, hi, mm in WATER_TABLE[need]:
        if lo <= temp_c < hi:
            base_mm = mm
            break
    # stage modifier (simple): peak demand near flowering/fruiting
    stage_boost = 1.2 if any(s in stage.lower() for s in ["flower", "silk", "fruit"]) else (1.1 if "vegetative" in stage.lower() else 1.0)
    # soil texture modifier
    soil_map = {"Sandy": 1.15, "Loam": 1.0, "Clay": 0.85}
    soil_factor = soil_map.get(soil, 1.0)

    mm_day = round(base_mm * stage_boost * soil_factor, 1)
    tip = (
        "Irrigate in the early morning or late evening to reduce losses. Use mulches and avoid waterlogging."
    )
    return mm_day, tip


def build_calendar(crop: str, sow_date: date) -> pd.DataFrame:
    stages = CROPS[crop]["stages"]
    rows = []
    cursor = sow_date
    for name, days in stages:
        start = cursor
        end = cursor + timedelta(days=days)
        rows.append({
            "Stage": name,
            "Start": start,
            "End": end,
            "Key Tasks": stage_tasks(name)
        })
        cursor = end
    return pd.DataFrame(rows)


def stage_tasks(stage_name: str) -> str:
    stage_name = stage_name.lower()
    if "sow" in stage_name or "plant" in stage_name or "transplant" in stage_name:
        return "Seed treatment, basal manure, proper spacing"
    if "vegetative" in stage_name or "tiller" in stage_name:
        return "Weeding, top-dress N, pest scouting"
    if "flower" in stage_name or "silk" in stage_name:
        return "Irrigation at peak demand, micronutrient spray if needed"
    if "fruit" in stage_name or "grain" in stage_name or "heading" in stage_name:
        return "K supplementation, disease monitoring"
    if "maturity" in stage_name or "harvest" in stage_name:
        return "Reduce irrigation, harvest planning"
    return "General crop care"


def ensure_store() -> str:
    os.makedirs("data", exist_ok=True)
    path = os.path.join("data", "records.csv")
    if not os.path.exists(path):
        pd.DataFrame(columns=[
            "timestamp","farmer","field","crop","sow_date","N","P","K","pH","temp","soil","stage","irrigation_mm"
        ]).to_csv(path, index=False)
    return path


def save_record(**kwargs):
    path = ensure_store()
    df = pd.read_csv(path)
    df.loc[len(df)] = kwargs
    df.to_csv(path, index=False)


def make_report_html(meta: Dict, fert: List[Tuple[str,str,str]], irr_mm: float, irr_tip: str, calendar_df: pd.DataFrame) -> bytes:
    def chip(text, kind="pill"):
        return f'<span class="pill">{text}</span>'
    fert_lines = "".join([
        f"<li><b>{k}</b>: <span class='{lvl}'>{lvl.upper()}</span> — {msg}</li>" for k,lvl,msg in fert
    ])
    cal_rows = "".join([
        f"<tr><td>{r['Stage']}</td><td>{r['Start']}</td><td>{r['End']}</td><td>{r['Key Tasks']}</td></tr>"
        for _, r in calendar_df.iterrows()
    ])
    html = f"""
    <html>
    <head>
      <meta charset='utf-8'/>
      <style>
        body {{ font-family: Inter, system-ui, -apple-system, Segoe UI, Arial; padding:24px; }}
        h1 {{ color:{PRIMARY}; }}
        .pill {{ display:inline-block; padding:6px 12px; border-radius:999px; border:1px solid #e2e8f0; }}
        .ok {{ color:{PRIMARY}; }} .warn {{ color:#b45309; }} .bad {{ color:#dc2626; }} .good {{ color:{ACCENT}; }}
        table {{ border-collapse: collapse; width:100%; }}
        td,th {{ border:1px solid #e5e7eb; padding:8px; }}
      </style>
    </head>
    <body>
      <h1>AgriEase — Field Report</h1>
      <p>{chip(meta['crop'])} {chip(meta['soil'])} {chip(f"{meta['temp']}°C")}</p>
      <h2>Soil & Fertility</h2>
      <ul>{fert_lines}</ul>
      <h2>Irrigation</h2>
      <p>Recommended: <b>{irr_mm} mm/day</b> (≈ {irr_mm} L/m²/day). Tip: {irr_tip}</p>
      <h2>Crop Calendar</h2>
      <table>
        <tr><th>Stage</th><th>Start</th><th>End</th><th>Key Tasks</th></tr>
        {cal_rows}
      </table>
      <p style='color:#64748b;font-size:12px;margin-top:24px'>Generated by AgriEase — for education/demo; consult local experts for exact doses.</p>
    </body>
    </html>
    """
    return html.encode("utf-8")

# ----------------------------
# Sidebar — project meta
# ----------------------------
st.sidebar.title("🌾 AgriEase")
st.sidebar.caption("Soil • Irrigation • Calendar • Records")

farmer = st.sidebar.text_input("Your name / farm name", value="Demo Farm")
field = st.sidebar.text_input("Field / plot ID", value="Plot‑A1")
with st.sidebar.expander("About this app"):
    st.write("Beginner‑friendly agriculture helper built with Streamlit. Save quick records and export a report.")

# ----------------------------
# Header
# ----------------------------
st.markdown(f"<h1 class='heading'>🌱 AgriEase — Soil & Irrigation Assistant</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtle'>Elegant demo app for agricultural engineers: input soil & weather, get fertilizer and irrigation tips, and auto‑build a crop calendar.</p>", unsafe_allow_html=True)

# ----------------------------
# Tabs
# ----------------------------
Tabs = st.tabs(["Dashboard", "Soil Analyzer", "Irrigation", "Crop Calendar", "Tools ⚙️", "Records ▤"])

# ---- Dashboard ----
with Tabs[0]:
    st.markdown("### Quick Overview")
    col1, col2, col3 = st.columns(3)
    col1.metric("Saved records", value=str(len(pd.read_csv(ensure_store()))))
    col2.markdown("<div class='metric-chip'>💾 Data stored in ./data/records.csv</div>", unsafe_allow_html=True)
    col3.markdown("<div class='metric-chip'>⚠️ Educational demo — verify doses locally</div>", unsafe_allow_html=True)
    st.write("")
    st.markdown("<div class='soft-card'>Use the tabs to enter soil N‑P‑K‑pH, temperature, crop & soil type. The app suggests simple fertilizer and irrigation plans and builds a stage‑wise calendar. You can also export a clean HTML report.</div>", unsafe_allow_html=True)

# ---- Soil Analyzer ----
with Tabs[1]:
    st.subheader("🔬 Soil Analyzer")
    cc1, cc2 = st.columns([1,1])
    with cc1:
        crop = st.selectbox("Crop", options=list(CROPS.keys()), index=0)
        sow_date = st.date_input("Sowing / transplant date", value=date.today())
        pH = st.slider("Soil pH", 4.5, 9.5, 6.8, 0.1)
        N = st.number_input("Available Nitrogen (kg/ha, estimate)", min_value=0.0, max_value=300.0, value=70.0, step=5.0)
        P = st.number_input("Available Phosphorus (kg/ha, estimate)", min_value=0.0, max_value=200.0, value=40.0, step=5.0)
        K = st.number_input("Available Potassium (kg/ha, estimate)", min_value=0.0, max_value=250.0, value=40.0, step=5.0)
    with cc2:
        st.markdown("**Optimal ranges (educational):**")
        ranges = CROPS[crop]["npk_opt"]
        st.write(ranges)
        lvl = fert_reco(N, P, K, crop)
        cols = st.columns(3)
        for i,(k,l,m) in enumerate(lvl):
            tone = {"ok":"ok","mid":"warn","low":"bad","high":"good"}[l]
            cols[i].markdown(f"<div class='soft-card'><b>{k}</b><br><span class='{tone}'>{l.upper()}</span><br><span class='subtle'>{m}</span></div>", unsafe_allow_html=True)
        if pH < 5.5:
            st.info("pH is acidic; consider liming and avoid overusing ammonium fertilizers.")
        elif pH > 8.0:
            st.info("pH is alkaline; consider gypsum for sodic soils and choose P sources wisely.")

# ---- Irrigation ----
with Tabs[2]:
    st.subheader("💧 Irrigation Helper")
    colL, colR = st.columns(2)
    with colL:
        temp = st.slider("Current average temperature (°C)", 10.0, 45.0, 30.0, 0.5)
        soil_type = st.selectbox("Soil texture", ["Sandy", "Loam", "Clay"], index=1)
        stage = st.selectbox("Current crop stage", [s for s,_ in CROPS[crop]["stages"]])
        rainfall_recent = st.number_input("Rainfall (last 24h, mm)", 0.0, 200.0, 0.0, 1.0)
        rainfall_expected = st.number_input("Expected rainfall (next 24h, mm)", 0.0, 200.0, 0.0, 1.0)
        canopy_cover = st.slider("Canopy cover (%)", 0, 100, 60)
        mm_base, tip = irrigation_reco(crop, temp, stage, soil_type)
        # Simple water balance and canopy factor
        cover_factor = 0.7 + 0.003 * canopy_cover  # 0.7–1.0 approx
        mm_net = max(0.0, round(mm_base * cover_factor - (rainfall_recent*0.8 + rainfall_expected*0.5), 1))
    with colR:
        st.markdown(f"<div class='soft-card'><b>Recommendation</b><br/><span class='heading' style='font-size:28px'>{mm_net} mm/day</span><br/><span class='subtle'>(Base {mm_base} − rain adj + canopy)</span><br/><br/>{tip}</div>", unsafe_allow_html=True)
        st.info("Rule-of-thumb: 1 mm = 1 L/m². Reduce irrigation if substantial rainfall is forecast.")
    # expose chosen values to Records tab
    mm = mm_net

# ---- Calendar ----
with Tabs[3]:
    st.subheader("🗓️ Crop Calendar")
    cal_df = build_calendar(crop, sow_date)
    st.dataframe(cal_df, use_container_width=True)

# ---- Tools ----
with Tabs[4]:
    st.subheader("🧮 Field Tools")
    tool = st.radio("Select a tool", ["Drip Runtime Scheduler", "Water Budget & Area"])

    if tool == "Drip Runtime Scheduler":
        t1, t2 = st.columns(2)
        with t1:
            target_mm = st.number_input("Target irrigation (mm)", 0.0, 50.0, value=float(mm if 'mm' in locals() else 5.0))
            area_m2 = st.number_input("Irrigated area (m²)", 1.0, 100000.0, 1000.0, 1.0)
            emitter_flow_lph = st.number_input("Emitter flow (L/h)", 0.1, 20.0, 4.0, 0.1)
        with t2:
            emitters_per_plant = st.number_input("Emitters per plant", 1, 8, 2)
            plant_spacing_m = st.number_input("Plant spacing (m)", 0.1, 5.0, 0.6, 0.1)
            row_spacing_m = st.number_input("Row spacing (m)", 0.1, 5.0, 1.2, 0.1)
        plants = max(1, int(area_m2 / (plant_spacing_m * row_spacing_m)))
        total_flow_lph = plants * emitters_per_plant * emitter_flow_lph
        mm_per_hour = total_flow_lph / area_m2  # since 1 L/m² = 1 mm
        runtime_min = 0 if mm_per_hour == 0 else round(target_mm / mm_per_hour * 60, 1)
        st.markdown(f"<div class='soft-card'><b>Result</b><br/>Plants ≈ <b>{plants}</b> • Flow ≈ <b>{total_flow_lph:.1f} L/h</b><br/>Application rate ≈ <b>{mm_per_hour:.2f} mm/h</b><br/><span class='heading' style='font-size:24px'>Run for {runtime_min} minutes</span></div>", unsafe_allow_html=True)

    else:  # Water Budget & Area
        w1, w2 = st.columns(2)
        with w1:
            field_len = st.number_input("Field length (m)", 1.0, 10000.0, 50.0, 1.0)
            field_wid = st.number_input("Field width (m)", 1.0, 10000.0, 20.0, 1.0)
            target_mm = st.number_input("Target depth (mm)", 0.0, 100.0, 5.0, 0.5)
        with w2:
            efficiency = st.slider("System efficiency (%)", 50, 100, 85)
        area_m2 = field_len * field_wid
        gross_L = area_m2 * target_mm / (efficiency/100)
        st.markdown(f"<div class='soft-card'><b>Area:</b> {area_m2:.0f} m²<br/><b>Water required:</b> {gross_L:,.0f} L (at {efficiency}% efficiency)</div>", unsafe_allow_html=True)

# ---- Records ----
with Tabs[5]:
    st.subheader("📒 Save a record & Export report")
    if st.button("Save current inputs as a record"):
        save_record(
            timestamp=datetime.now().isoformat(timespec='seconds'),
            farmer=farmer,
            field=field,
            crop=crop,
            sow_date=str(sow_date),
            N=N, P=P, K=K, pH=pH,
            temp=temp,
            soil=soil_type,
            stage=stage,
            irrigation_mm=mm,
        )
        st.success("Saved. Check the table below and data/records.csv.")

    st.markdown("**Saved records**")
    rec_df = pd.read_csv(ensure_store())
    st.dataframe(rec_df, use_container_width=True)
    st.download_button("⬇️ Download records (CSV)", data=rec_df.to_csv(index=False).encode('utf-8'), file_name="AgriEase_records.csv", mime="text/csv")

    st.markdown("**Export current plan as HTML report**")
    meta = {"crop": crop, "soil": soil_type, "temp": temp}
    report_bytes = make_report_html(meta, fert_reco(N,P,K,crop), mm, tip, cal_df)
    st.download_button(
        label="⬇️ Download report (HTML)",
        data=report_bytes,
        file_name=f"AgriEase_{crop}_{date.today().isoformat()}.html",
        mime="text/html",
    )


st.markdown("<p class='footer-note'>© AgriEase demo • Built with Streamlit • For learning purposes</p>", unsafe_allow_html=True)
