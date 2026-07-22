#!/usr/bin/env python
# forecast.py
# Generates forecasts for Access (Account Ownership) and Usage (Digital Payments) for 2025-2027.

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_data():
    df = pd.read_excel('data/processed/ethiopia_fi_unified_data_enriched.xlsx')
    df['observation_date'] = pd.to_datetime(df['observation_date'])
    return df

def prepare_trend_data(obs, indicator_code):
    data = obs[obs['indicator_code'] == indicator_code].copy()
    data = data.sort_values('observation_date')
    # Use numeric time: years since first observation
    data['t'] = (data['observation_date'] - data['observation_date'].min()).dt.days / 365.25
    return data

def fit_trend(data, target_col='value_numeric', time_col='t'):
    X = sm.add_constant(data[time_col])
    y = data[target_col]
    model = sm.OLS(y, X).fit()
    return model

def get_event_impacts(df, indicator_code, forecast_years):
    """
    Sum impacts from impact_links that affect the given indicator,
    considering the lag and event date.
    """
    impacts = df[df['record_type'] == 'impact_link']
    events = df[df['record_type'] == 'event']
    total_impact = np.zeros(len(forecast_years))
    
    for _, imp in impacts.iterrows():
        if imp['related_indicator'] != indicator_code:
            continue
        # Find the event
        event = events[events['record_id'] == imp['parent_id']]
        if event.empty:
            continue
        event = event.iloc[0]
        event_date = event['observation_date']
        lag_months = imp.get('lag_months', 0)
        if pd.isna(lag_months):
            lag_months = 0
        effect_date = event_date + pd.DateOffset(months=int(lag_months))
        for i, y in enumerate(forecast_years):
            if effect_date <= pd.Timestamp(f'{y}-12-31'):
                total_impact[i] += imp.get('impact_estimate', 0.0)
    return total_impact

def generate_forecast(df, indicator_code, forecast_years):
    obs = df[df['record_type'] == 'observation']
    data = prepare_trend_data(obs, indicator_code)
    model = fit_trend(data)
    
    # Baseline forecast
    base_year = data['observation_date'].min()
    t_values = np.array([(pd.Timestamp(f'{y}-12-31') - base_year).days / 365.25 for y in forecast_years])
    X_forecast = sm.add_constant(t_values)
    baseline = model.predict(X_forecast)
    
    # Event impacts
    impact = get_event_impacts(df, indicator_code, forecast_years)
    forecast = baseline + impact
    
    return {
        'indicator': indicator_code,
        'years': forecast_years,
        'baseline': baseline,
        'impact': impact,
        'forecast': forecast,
        'model': model
    }

def plot_forecast(obs, forecast_result, save_path):
    indicator = forecast_result['indicator']
    years = forecast_result['years']
    forecast_vals = forecast_result['forecast']
    baseline_vals = forecast_result['baseline']
    
    # Historical data
    hist = obs[obs['indicator_code'] == indicator].sort_values('observation_date')
    
    plt.figure(figsize=(10,6))
    plt.plot(hist['observation_date'], hist['value_numeric'], 'bo-', label='Historical')
    forecast_dates = [pd.Timestamp(f'{y}-12-31') for y in years]
    plt.plot(forecast_dates, baseline_vals, 'g--', label='Baseline')
    plt.plot(forecast_dates, forecast_vals, 'ro-', label='Forecast (with events)')
    plt.title(f'Forecast for {indicator} (2025-2027)')
    plt.ylabel('Value (%)')
    plt.legend()
    plt.grid(True)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=150)
    plt.close()
    logging.info(f"Saved forecast plot to {save_path}")

def main():
    df = load_data()
    obs = df[df['record_type'] == 'observation']
    
    forecast_years = [2025, 2026, 2027]
    indicators = ['ACC_OWNERSHIP', 'USG_DIGITAL_PAYMENT']  # if data exists
    
    # Fallback: if USG_DIGITAL_PAYMENT missing, use ACC_MM_ACCOUNT as proxy
    available = obs['indicator_code'].unique()
    if 'USG_DIGITAL_PAYMENT' not in available:
        logging.warning("USG_DIGITAL_PAYMENT not found; using ACC_MM_ACCOUNT as usage proxy.")
        indicators = ['ACC_OWNERSHIP', 'ACC_MM_ACCOUNT']
    
    results = {}
    for ind in indicators:
        if ind not in available:
            logging.warning(f"Indicator {ind} not available; skipping.")
            continue
        result = generate_forecast(df, ind, forecast_years)
        results[ind] = result
        # Plot
        plot_forecast(obs, result, f'reports/figures/forecast_{ind}.png')
    
    # Combine forecasts into a table
    table_data = []
    for ind, res in results.items():
        for i, y in enumerate(forecast_years):
            table_data.append({
                'Indicator': ind,
                'Year': y,
                'Baseline': round(res['baseline'][i], 1),
                'Event_Impact': round(res['impact'][i], 1),
                'Forecast': round(res['forecast'][i], 1)
            })
    forecast_table = pd.DataFrame(table_data)
    
    os.makedirs('reports/forecasts', exist_ok=True)
    forecast_table.to_csv('reports/forecasts/forecast_table.csv', index=False)
    print("\nForecast Table:")
    print(forecast_table)
    logging.info("Forecast table saved to reports/forecasts/forecast_table.csv")

if __name__ == '__main__':
    main()