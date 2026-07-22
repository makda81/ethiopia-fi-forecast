import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

st.set_page_config(page_title="Ethiopia FI Dashboard", layout="wide")
st.title("🇪🇹 Ethiopia Financial Inclusion Dashboard")

@st.cache_data
def load_data():
    df = pd.read_excel('data/processed/ethiopia_fi_unified_data_enriched.xlsx')
    df['observation_date'] = pd.to_datetime(df['observation_date'])
    return df

df = load_data()
obs = df[df['record_type'] == 'observation']
events = df[df['record_type'] == 'event']
impacts = df[df['record_type'] == 'impact_link']

# Sidebar
st.sidebar.header("Filters")
indicators = sorted(obs['indicator_code'].unique())
selected = st.sidebar.selectbox("Select Indicator", indicators)
show_events = st.sidebar.checkbox("Show Event Markers", value=True)
scenario = st.sidebar.selectbox("Scenario", ["Base", "Optimistic", "Pessimistic"])

# Metrics
ind_data = obs[obs['indicator_code'] == selected].sort_values('observation_date')
if not ind_data.empty:
    col1, col2, col3 = st.columns(3)
    col1.metric("Latest Value", f"{ind_data.iloc[-1]['value_numeric']:.1f}%")
    col2.metric("Earliest Value", f"{ind_data.iloc[0]['value_numeric']:.1f}%")
    if len(ind_data) > 1:
        change = ind_data.iloc[-1]['value_numeric'] - ind_data.iloc[0]['value_numeric']
        col3.metric("Change", f"{change:+.1f} pp")

# Plot
fig, ax = plt.subplots(figsize=(12,6))
ax.plot(ind_data['observation_date'], ind_data['value_numeric'], 'bo-', linewidth=2, label=selected)
if show_events:
    for _, ev in events.iterrows():
        if pd.notna(ev['observation_date']):
            ax.axvline(x=ev['observation_date'], color='gray', linestyle='--', alpha=0.5)
            ax.text(ev['observation_date'], ax.get_ylim()[0] + 0.05*(ax.get_ylim()[1]-ax.get_ylim()[0]),
                    ev['indicator'], rotation=45, fontsize=7, ha='center')
ax.set_title(f"{selected} over time")
ax.grid(True)
st.pyplot(fig)

# Forecast table with scenario
forecast_file = 'reports/forecasts/forecast_table_with_uncertainty.csv'
if os.path.exists(forecast_file):
    st.subheader("📈 Forecasts 2025-2027")
    forecast = pd.read_csv(forecast_file)
    # Filter by selected indicator and scenario
    f = forecast[forecast['Indicator'] == selected]
    if not f.empty:
        cols = ['Year', 'Baseline', 'Event_Impact', f'Scenario_{scenario}', 'Lower_95%', 'Upper_95%']
        # rename scenario column
        f_display = f[cols].copy()
        f_display.rename(columns={f'Scenario_{scenario}': 'Forecast'}, inplace=True)
        st.dataframe(f_display)
    else:
        st.info("No forecast for this indicator.")
else:
    st.info("Run forecast.py to generate forecasts.")

# Impact Matrix
with st.expander("📊 Impact Matrix (Events → Indicators)"):
    mat_file = 'reports/forecasts/association_matrix.csv'
    if os.path.exists(mat_file):
        mat = pd.read_csv(mat_file, index_col=0)
        st.dataframe(mat)
        st.caption("Each cell shows the expected percentage change in the indicator due to the event, after the lag period.")
    else:
        st.info("Run validate_impacts.py to generate the impact matrix.")

# Assumptions
with st.expander("📝 Assumptions & Methodology"):
    st.markdown("""
    - **Trend model**: Log‑linear (slowing growth near saturation); falls back to linear.
    - **Event impacts**: Additive, fixed lag, permanent shift.
    - **Scenarios**: Optimistic (impact × 1.3), Base (× 1.0), Pessimistic (× 0.6).
    - **Uncertainty**: 95% prediction intervals from the trend model.
    - **Data gaps**: Interpolated for fitting.
    - **External evidence**: Impact magnitudes from comparable countries (Kenya).
    """)

# Event list
with st.expander("📅 Events Timeline"):
    st.dataframe(events[['indicator', 'category', 'observation_date', 'source_name']])

# Impact links
with st.expander("🔗 Impact Links"):
    st.dataframe(impacts[['parent_id', 'related_indicator', 'impact_direction', 'impact_estimate', 'lag_months']])

st.sidebar.info("Dashboard built with Streamlit. Data enriched from multiple sources.")