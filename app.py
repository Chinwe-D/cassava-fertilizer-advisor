"""
Cassava Fertilizer Decision Support -- Nigeria
================================================
A simple dashboard for extension agents and advisors, translating the
climate-trend-adjusted, QUEFTS-based nutrient model into a plain-language
recommendation, with no statistics jargon required to use it.

Run locally:    streamlit run app.py
Data required:  state_summary.csv, nigeria_states.geojson (same folder)
"""

import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Cassava Fertilizer Advisor -- Nigeria", layout="wide")

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("state_summary.csv")
    with open("nigeria_states.geojson") as f:
        geo = json.load(f)
    return df, geo

df, geo = load_data()
all_state_names = sorted([f["properties"]["name"] for f in geo["features"]])
covered_states = set(df["State"])

# States outside the cassava-favourable belt sampled in this study (climate makes
# cassava a minor crop there) -- shown, but with an honest explanation, not a number.
OUTSIDE_BELT = {"Jigawa", "Kano", "Katsina", "Sokoto", "Yobe", "Zamfara"}
# Lagos sits inside the belt but is too small for the 0.5-degree sampling grid to
# have caught directly -- reasonable to borrow its immediate neighbour, Ogun.
LAGOS_PROXY_STATE = "Ogun"

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("Cassava Fertilizer Advisor")
st.markdown(
    "Pick a state to see what your cassava crop most likely needs, based on "
    "**real soil data** and **45 years of climate records** for that area, "
    "not guesswork."
)

# ---------------------------------------------------------------------------
# Sidebar: state picker
# ---------------------------------------------------------------------------
st.sidebar.header("1. Choose your state")
selectable_states = all_state_names
default_idx = selectable_states.index("Edo") if "Edo" in selectable_states else 0
state = st.sidebar.selectbox("State", selectable_states, index=default_idx)

if state in OUTSIDE_BELT:
    st.warning(
        f"**{state}** sits outside the cassava-growing belt this tool covers -- "
        "cassava is not commonly grown at scale here because of the drier climate. "
        "This tool does not have a reliable recommendation for this state. Please "
        "pick a state further south for a real estimate."
    )
    st.stop()

lookup_state = LAGOS_PROXY_STATE if state == "Lagos" else state
row = df[df["State"] == lookup_state].iloc[0]

if state == "Lagos":
    st.info(
        f"Lagos was too small for this tool's sampling grid to cover directly. "
        f"The estimate below is borrowed from neighbouring **{LAGOS_PROXY_STATE}** "
        "state, which has very similar soil and climate conditions."
    )

st.sidebar.markdown("---")
st.sidebar.header("2. Your soil condition")
rooting_choice = st.sidebar.radio(
    "Does your farmland allow roots to grow deep (more than 2 metres), "
    "or is there a hard or clayey layer that blocks deep roots?",
    ["I'm not sure", "Roots can go deep (sandy/loose soil, good drainage)", "Roots are blocked (hard/clayey layer, waterlogging)"],
    index=0,
)
if rooting_choice.startswith("Roots can go deep"):
    profile = "deep"
elif rooting_choice.startswith("Roots are blocked"):
    profile = "restricted"
else:
    profile = "both"

st.sidebar.markdown("---")
st.sidebar.caption(
    "This tool is a prototype decision-support aid. It is not yet a substitute "
    "for a soil test or an extension officer's on-site judgement. See "
    "'How trustworthy is this?' below for details."
)

# ---------------------------------------------------------------------------
# Main panel: map + recommendation side by side
# ---------------------------------------------------------------------------
col_map, col_rec = st.columns([1, 1.3])

with col_map:
    st.subheader("Where you are")
    state_values = {f["properties"]["name"]: (1 if f["properties"]["name"] == state else 0)
                     for f in geo["features"]}
    fig = go.Figure(go.Choropleth(
        geojson=geo,
        locations=list(state_values.keys()),
        z=list(state_values.values()),
        featureidkey="properties.name",
        colorscale=[[0, "#e8e8e8"], [1, "#1baf7a"]],
        showscale=False,
        marker_line_color="black",
        marker_line_width=0.6,
    ))
    fig.update_geos(
        visible=False, fitbounds="locations",
        projection_type="mercator",
    )
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=420)
    st.plotly_chart(fig, width="stretch")
    if state == "Lagos":
        st.caption(f"Estimate borrowed from {lookup_state} -- {int(row['n_points'])} sample point(s) used there.")
    else:
        st.caption(f"{state} -- {int(row['n_points'])} sample point(s) used to build this estimate.")
    if row["n_points"] <= 2:
        st.warning(
            f"Only {int(row['n_points'])} sample point(s) cover {lookup_state}. "
            "Treat this recommendation as a rough guide only, and a soil test "
            "is especially recommended here."
        )

with col_rec:
    st.subheader("What your cassava likely needs")

    # At-a-glance view: which nutrient matters most, before the detailed numbers.
    glance_profile = profile if profile != "both" else "restricted"
    nutrient_names = ["Nitrogen", "Phosphorus", "Potassium"]
    nutrient_values = [
        row[f"N_gap_{glance_profile}"],
        row[f"P_gap_{glance_profile}"],
        row[f"K_gap_{glance_profile}"],
    ]
    nutrient_colors = ["#2a78d6", "#eda100", "#1baf7a"]
    order = sorted(range(3), key=lambda i: nutrient_values[i], reverse=True)

    glance_fig = go.Figure(go.Bar(
        x=[nutrient_values[i] for i in order],
        y=[nutrient_names[i] for i in order],
        orientation="h",
        marker_color=[nutrient_colors[i] for i in order],
        text=[f"{'Most needed' if j == 0 else ''}" for j in range(3)],
        textposition="outside",
    ))
    glance_fig.update_layout(
        height=170,
        margin=dict(l=10, r=60, t=10, b=10),
        xaxis_title="How much is needed (kg/ha)",
        showlegend=False,
    )
    st.plotly_chart(glance_fig, width="stretch")

    def show_profile(p, label):
        st.markdown(f"**{label}**")
        c1, c2, c3 = st.columns(3)
        c1.metric("Urea -- nitrogen (bags/ha)", f"{row[f'Urea_bags_ha_{p}']:.1f}")
        c2.metric("TSP -- phosphorus (bags/ha)", f"{row[f'TSP_bags_ha_{p}']:.1f}")
        c3.metric("MOP -- potassium (bags/ha)", f"{row[f'MOP_bags_ha_{p}']:.1f}")

    if profile == "both":
        st.info(
            "You told us you're not sure about your soil's rooting depth, so "
            "here are both scenarios. Ask a soil scientist or extension "
            "officer to check, or dig a small pit (about 1.5-2m) to see if "
            "roots can pass a hard or clay layer."
        )
        show_profile("deep", "If your soil allows deep rooting")
        st.markdown("")
        show_profile("restricted", "If your soil blocks deep rooting")
    else:
        label = "Your soil (deep rooting)" if profile == "deep" else "Your soil (rooting blocked)"
        show_profile(profile, label)

    k_gap = row[f"K_gap_{glance_profile}"]
    n_gap = row[f"N_gap_{glance_profile}"]
    p_gap = row[f"P_gap_{glance_profile}"]

    st.markdown("---")
    st.subheader("In plain words")
    nutrients_needed = []
    if k_gap > 10:
        nutrients_needed.append("**potassium (MOP)**")
    if n_gap > 10:
        nutrients_needed.append("**nitrogen (Urea)**")
    if p_gap > 10:
        nutrients_needed.append("**phosphorus (TSP)**")

    if nutrients_needed:
        st.write(
            f"In {state}, the nutrient your cassava is most likely short of is "
            + " and ".join(nutrients_needed) +
            ". Potassium is the nutrient most Nigerian cassava farmers under-apply, "
            "and it is usually the one that limits yield the most, even more than nitrogen."
        )
    else:
        st.write(
            f"In {state}, your soil appears to already supply most of what cassava "
            "needs for a modest yield target. A soil test is still the safest way "
            "to confirm this before skipping fertilizer."
        )

# ---------------------------------------------------------------------------
# Trust / transparency section -- collapsed by default, plain language
# ---------------------------------------------------------------------------
st.markdown("---")
with st.expander("How trustworthy is this? (please read before using this for real decisions)"):
    st.markdown(
        """
This tool was checked against **real cassava field trials** conducted in Nigeria
(Adiele et al., 2020) -- actual crop planted, fertilized, and harvested at six
real farms -- not just computer estimates.

**What we found when we checked:** our first version was wrong. It
badly underestimated how well cassava grows without fertilizer,
because cassava's roots go far deeper than most crop models assume (over 3
metres deep at one real farm we checked against). We fixed this, and the
corrected version now closely matches what actually grew on those real farms.

**What we're still not sure about:** we cannot yet tell, from satellite data
alone, whether a given piece of land has the kind of soil that lets cassava
roots go deep, or whether there's a hidden hard/clay layer blocking them.
That's why this tool asks you directly, and why it shows two different
answers when you're not sure. Only physically digging a soil pit can
confirm this for certain, which is why we're not replacing a soil test yet,
only helping you decide where testing matters most.

**What the numbers are based on:**
- Real soil samples across the region (iSDAsoil, 30m resolution satellite-based soil map)
- 45 years of real temperature records and 44 years of real rainfall records for your area
- QUEFTS, a well-established international soil fertility model, not a private formula
- Fertilizer amounts assume a realistic target yield (25 tonnes of fresh roots per hectare), not a research-station record yield
        """
    )

with st.expander("About the fertilizer amounts shown"):
    st.markdown(
        """
- **Urea** supplies nitrogen (46% N)
- **TSP** (Triple Super Phosphate) supplies phosphorus (46% P2O5)
- **MOP** (Muriate of Potash) supplies potassium (60% K2O)
- Amounts are shown in standard 50kg bags per hectare, rounded to one decimal place
- These are commonly available fertilizer products in Nigeria; your local agro-dealer may also offer blended NPK products that combine these in one bag
        """
    )

st.caption(
    "Prototype decision-support tool, built on QUEFTS and validated against Adiele et al. (2020) field trial data. "
    "Not a replacement for a soil test or an extension officer's on-site assessment."
)
