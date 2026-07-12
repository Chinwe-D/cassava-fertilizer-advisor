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
selectable_states = sorted(covered_states)
state = st.sidebar.selectbox("State", selectable_states, index=selectable_states.index("Edo") if "Edo" in selectable_states else 0)

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

row = df[df["State"] == state].iloc[0]

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
    st.caption(f"{state} -- {int(row['n_points'])} sample point(s) used to build this estimate.")
    if row["n_points"] <= 2:
        st.warning(
            f"Only {int(row['n_points'])} sample point(s) cover {state}. "
            "Treat this recommendation as a rough guide only, and a soil test "
            "is especially recommended here."
        )

with col_rec:
    st.subheader("What your cassava likely needs")

    def show_profile(p, label):
        st.markdown(f"**{label}**")
        c1, c2, c3 = st.columns(3)
        c1.metric("Urea (bags/ha)", f"{row[f'Urea_bags_ha_{p}']:.1f}")
        c2.metric("TSP (bags/ha)", f"{row[f'TSP_bags_ha_{p}']:.1f}")
        c3.metric("MOP (bags/ha)", f"{row[f'MOP_bags_ha_{p}']:.1f}")

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

    k_gap = row[f"K_gap_{profile if profile != 'both' else 'restricted'}"]
    n_gap = row[f"N_gap_{profile if profile != 'both' else 'restricted'}"]
    p_gap = row[f"P_gap_{profile if profile != 'both' else 'restricted'}"]

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
under-estimated how well cassava grows without fertilizer, by 36-71%,
because cassava's roots go far deeper than most crop models assume (over 3
metres deep at one real farm we checked against). We fixed this, and the
corrected version matched the real farm results to within 2.5-8.8%.

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
