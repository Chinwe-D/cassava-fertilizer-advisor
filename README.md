# Cassava Fertilizer Advisor -- Nigeria

A simple, non-technical dashboard for extension agents and advisors,
translating the climate-trend-adjusted, QUEFTS-based nutrient model into a
plain-language fertilizer recommendation.

## What it does

- Pick a Nigerian state from a dropdown
- Tell it whether your soil allows deep rooting (or "I'm not sure")
- Get a recommendation in bags of Urea, TSP, and MOP per hectare (the
  fertilizer products actually sold at Nigerian agro-dealers), not raw kg/ha
  of elemental nutrients
- See it on a real state-boundary map
- Expand "How trustworthy is this?" for the honest validation story in plain
  language -- including that the first version was wrong and was corrected

## How to run it

```bash
pip install streamlit plotly pandas
streamlit run app.py
```

Then open the local URL it prints (usually `http://localhost:8501`).

## Files needed together in the same folder

- `app.py` -- the dashboard itself
- `state_summary.csv` -- state-level fertilizer recommendations, pre-computed
  from the full analysis (see the manuscript / Colab notebook for how this
  was derived)
- `nigeria_states.geojson` -- real Nigerian state boundaries, for the map
- `requirements.txt` -- tells Streamlit Cloud which Python packages to install

## Deploying to Streamlit Community Cloud (free, public link)

This needs your own GitHub account and your own Streamlit Community Cloud
account -- I can't create either on your behalf, but every step below is
exact and copy-paste ready.

**Step 1 -- Create a GitHub repository**
1. Go to github.com and sign in (or create a free account if you don't have one).
2. Click the "+" in the top-right corner, then "New repository."
3. Name it something like `cassava-fertilizer-advisor`. Set it to **Public**
   (Community Cloud's free tier deploys public repos most simply; private
   repos work too but need an extra permission step later).
4. Click "Create repository."

**Step 2 -- Upload the four files**
1. On your new repository's page, click "Add file" -> "Upload files."
2. Drag in all four files: `app.py`, `state_summary.csv`,
   `nigeria_states.geojson`, `requirements.txt`.
3. Scroll down and click "Commit changes."

**Step 3 -- Create your Streamlit Community Cloud account**
1. Go to share.streamlit.io.
2. Click to sign in/sign up -- it will ask you to authenticate with GitHub.
3. Follow GitHub's authorization prompts and accept Streamlit's terms.

**Step 4 -- Connect GitHub (if not done automatically in Step 3)**
1. In the upper-left corner of your Streamlit Cloud workspace, click your
   GitHub username / the connection warning icon if shown.
2. Click "Connect GitHub account" and follow the prompts.

**Step 5 -- Deploy**
1. In your workspace, click "Create app" in the upper-right corner.
2. Choose "Deploy a public app from GitHub."
3. Fill in: your repository (`your-username/cassava-fertilizer-advisor`),
   branch (`main`), and main file path (`app.py`). Or just paste the GitHub
   URL of `app.py` directly if that option is offered.
4. Optional: set a custom subdomain, e.g. `cassava-advisor`, so the link
   reads `https://cassava-advisor.streamlit.app` instead of a random one.
5. Click "Deploy." It usually takes a few minutes the first time.

**After that:** any time you edit and re-upload the files on GitHub, the
live app updates automatically within a minute or two -- no redeployment
needed.

## A note on testing

This app was tested three ways before being handed over:

1. **Syntax check** -- passed.
2. **Streamlit's official headless test framework** (`AppTest`) -- the
   initial load passes cleanly with no exceptions. Simulating a *second*
   interaction (changing the dropdown) inside that same automated test
   process caused a segmentation fault. This was tracked down to pandas
   operations re-executing inside Streamlit's "bare mode" test harness --
   which Streamlit's own warning message states is an incomplete simulation
   of real server behaviour -- not a bug in the app's logic. The underlying
   data lookup was independently verified correct for every state, each in
   a fresh Python process, with no error.
3. **The real server** -- launched with `streamlit run`, confirmed healthy
   and serving pages correctly via its health-check endpoint.

In plain terms: the automated multi-click test tool crashed in a way that
looks like an environment quirk, not an app bug, but a real live click-through
in an actual browser has not been directly observed by me. **Please click
through all three sidebar options (the "I'm not sure" / "deep" / "blocked"
choices) and a few different states yourself the first time you run it**,
before showing it to anyone else. If anything breaks, the error will appear
directly in the browser page, which will make it easy to fix.
