# dashboard/app.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

st.set_page_config(page_title="Ethiopia FI Dashboard", layout="wide")
st.title("🇪🇹 Ethiopia Financial Inclusion Dashboard")

# Load data
@st.cache_data
def load_data():
    df = pd.read_excel('data/processed/ethiopia_fi_unified_data_enriched.xlsx')
    df['observation_date'] = pd.to_datetime(df['observation_date'])
    return df

df = load_data()
obs = df[df['record_type'] == 'observation']
events = df[df['record_type'] == 'event']
targets = df[df['record_type'] == 'target']
impacts = df[df['record_type'] == 'impact_link']

# Sidebar
st.sidebar.header("Filters")
indicator_list = obs['indicator_code'].unique()
selected_indicator = st.sidebar.selectbox("Select Indicator", indicator_list)
show_events = st.sidebar.checkbox("Show Event Markers", value=True)

# Main area
col1, col2, col3 = st.columns(3)
ind_data = obs[obs['indicator_code'] == selected_indicator].sort_values('observation_date')
if not ind_data.empty:
    latest = ind_data.iloc[-1]
    earliest = ind_data.iloc[0]
    col1.metric("Latest Value", f"{latest['value_numeric']:.1f}%")
    col2.metric("Earliest Value", f"{earliest['value_numeric']:.1f}%")
    if len(ind_data) > 1:
        change = latest['value_numeric'] - earliest['value_numeric']
        col3.metric("Change", f"{change:+.1f} pp")
else:
    col1.write("No data")

# Plot
fig, ax = plt.subplots(figsize=(12,6))
ax.plot(ind_data['observation_date'], ind_data['value_numeric'], 'bo-', linewidth=2, label=selected_indicator)

# Add event markers
if show_events:
    for _, ev in events.iterrows():
        if pd.notna(ev['observation_date']):
            ax.axvline(x=ev['observation_date'], color='gray', linestyle='--', alpha=0.5)
            ax.text(ev['observation_date'], ax.get_ylim()[0] + 0.05 * (ax.get_ylim()[1] - ax.get_ylim()[0]),
                    ev['indicator'], rotation=45, fontsize=7, ha='center')

ax.set_title(f"{selected_indicator} over time")
ax.grid(True)
st.pyplot(fig)

# Show forecasts if available
if os.path.exists('reports/forecasts/forecast_table.csv'):
    st.subheader("📈 Forecasts (2025-2027)")
    forecast = pd.read_csv('reports/forecasts/forecast_table.csv')
    # Filter for selected indicator
    f = forecast[forecast['Indicator'] == selected_indicator]
    if not f.empty:
        st.dataframe(f)
    else:
        st.write("No forecast for this indicator.")
else:
    st.info("Run forecast.py to generate forecasts.")

# Events table
with st.expander("📅 Events Timeline"):
    st.dataframe(events[['indicator', 'category', 'observation_date', 'source_name']])

# Impact links
with st.expander("🔗 Impact Links"):
    st.dataframe(impacts[['parent_id', 'related_indicator', 'impact_direction', 'impact_estimate', 'lag_months']])

# Data sources
with st.expander("📊 Data Sources"):
    source_counts = df['source_type'].value_counts().reset_index()
    source_counts.columns = ['Source Type', 'Count']
    st.bar_chart(source_counts.set_index('Source Type'))

st.sidebar.info("Dashboard built with Streamlit. Data enriched from multiple sources.")