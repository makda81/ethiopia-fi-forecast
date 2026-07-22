#!/usr/bin/env python
# forecast.py
# Generates forecasts for Access (Account Ownership) and Usage (Digital Payments)
# for 2025-2027 using trend + event impact model with prediction intervals.

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from statsmodels.regression.linear_model import OLS
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('forecast.log'),
        logging.StreamHandler()
    ]
)

def load_data():
    """Load the enriched dataset."""
    try:
        df = pd.read_excel('data/processed/ethiopia_fi_unified_data_enriched.xlsx')
        df['observation_date'] = pd.to_datetime(df['observation_date'])
        logging.info(f"Loaded {len(df)} records.")
        return df
    except FileNotFoundError:
        logging.error("Enriched dataset not found. Run enrich_data.py first.")
        raise
    except Exception as e:
        logging.error(f"Error loading data: {e}")
        raise

def prepare_trend_data(obs, indicator_code):
    """
    Prepare data for trend fitting: filter by indicator, sort by date,
    create numeric time variable (years since first observation).
    """
    data = obs[obs['indicator_code'] == indicator_code].copy()
    if data.empty:
        raise ValueError(f"No data found for indicator: {indicator_code}")
    data = data.sort_values('observation_date')
    # Use log of years since first observation for log-linear trend
    # but if we want linear, we can use t directly.
    # We'll try log-linear for rates (saturation) and fallback to linear.
    data['t'] = (data['observation_date'] - data['observation_date'].min()).dt.days / 365.25
    # Add log(t) for log-linear, but avoid log(0)
    data['log_t'] = np.log(data['t'] + 1e-6)  # small offset to avoid log(0)
    return data

def fit_trend(data, target_col='value_numeric', use_log=True):
    """
    Fit a trend model. If use_log=True, use log(t) as predictor (log-linear).
    Otherwise use t (linear).
    """
    if use_log:
        X = sm.add_constant(data['log_t'])
    else:
        X = sm.add_constant(data['t'])
    y = data[target_col]
    model = OLS(y, X).fit()
    return model

def get_event_impacts(df, indicator_code, forecast_years):
    """
    Sum impacts from impact_links that affect the given indicator,
    considering the event date and lag.
    Returns an array of cumulative impacts for each forecast year.
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

def generate_forecast(df, indicator_code, forecast_years, use_log=True):
    """
    Generate forecast for a given indicator.
    Returns a dictionary with baseline, impacts, forecast, and prediction intervals.
    """
    obs = df[df['record_type'] == 'observation']
    data = prepare_trend_data(obs, indicator_code)
    model = fit_trend(data, use_log=use_log)
    
    # Prepare forecast time values
    base_year = data['observation_date'].min()
    if use_log:
        t_values = np.array([(pd.Timestamp(f'{y}-12-31') - base_year).days / 365.25 for y in forecast_years])
        log_t_values = np.log(t_values + 1e-6)
        X_forecast = sm.add_constant(log_t_values)
    else:
        t_values = np.array([(pd.Timestamp(f'{y}-12-31') - base_year).days / 365.25 for y in forecast_years])
        X_forecast = sm.add_constant(t_values)
    
    # Prediction with intervals (using get_prediction for prediction intervals)
    pred = model.get_prediction(X_forecast)
    pred_summary = pred.summary_frame(alpha=0.05)  # 95% prediction interval
    
    baseline = pred_summary['mean'].values
    lower = pred_summary['obs_ci_lower'].values   # prediction interval (wider)
    upper = pred_summary['obs_ci_upper'].values
    
    # Event impacts
    impact = get_event_impacts(df, indicator_code, forecast_years)
    forecast = baseline + impact
    lower_f = lower + impact
    upper_f = upper + impact
    
    # Cap at 0-100 if percentage (optional)
    # forecast = np.clip(forecast, 0, 100)
    # lower_f = np.clip(lower_f, 0, 100)
    # upper_f = np.clip(upper_f, 0, 100)
    
    return {
        'indicator': indicator_code,
        'years': forecast_years,
        'baseline': baseline,
        'impact': impact,
        'forecast': forecast,
        'lower': lower_f,
        'upper': upper_f,
        'model': model,
        'use_log': use_log
    }

def plot_forecast(obs, result, save_path):
    """Plot historical data, baseline, forecast, and prediction intervals."""
    indicator = result['indicator']
    years = result['years']
    forecast_vals = result['forecast']
    baseline_vals = result['baseline']
    lower = result['lower']
    upper = result['upper']
    
    hist = obs[obs['indicator_code'] == indicator].sort_values('observation_date')
    
    plt.figure(figsize=(10,6))
    # Historical
    plt.plot(hist['observation_date'], hist['value_numeric'], 'bo-', label='Historical')
    
    # Forecast dates
    forecast_dates = [pd.Timestamp(f'{y}-12-31') for y in years]
    
    # Baseline
    plt.plot(forecast_dates, baseline_vals, 'g--', label='Baseline (trend)')
    
    # Forecast with events
    plt.plot(forecast_dates, forecast_vals, 'ro-', label='Forecast (with events)')
    
    # Prediction interval
    plt.fill_between(forecast_dates, lower, upper, color='red', alpha=0.2, label='95% Prediction Interval')
    
    plt.title(f'Forecast for {indicator} (2025-2027)')
    plt.ylabel('Value (%)')
    plt.legend()
    plt.grid(True)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=150)
    plt.close()
    logging.info(f"Saved forecast plot to {save_path}")

def main():
    """Main forecasting workflow."""
    try:
        df = load_data()
        obs = df[df['record_type'] == 'observation']
        
        forecast_years = [2025, 2026, 2027]
        indicators = ['ACC_OWNERSHIP', 'USG_DIGITAL_PAYMENT']
        
        # Check availability; if USG_DIGITAL_PAYMENT missing, use ACC_MM_ACCOUNT as proxy
        available = obs['indicator_code'].unique()
        if 'USG_DIGITAL_PAYMENT' not in available:
            logging.warning("USG_DIGITAL_PAYMENT not found; using ACC_MM_ACCOUNT as usage proxy.")
            indicators = ['ACC_OWNERSHIP', 'ACC_MM_ACCOUNT']
        
        results = {}
        for ind in indicators:
            if ind not in available:
                logging.warning(f"Indicator {ind} not available; skipping.")
                continue
            # Try log-linear, fallback to linear if model fails
            try:
                result = generate_forecast(df, ind, forecast_years, use_log=True)
            except Exception as e:
                logging.warning(f"Log-linear failed for {ind}: {e}. Falling back to linear.")
                result = generate_forecast(df, ind, forecast_years, use_log=False)
            results[ind] = result
            # Plot
            plot_forecast(obs, result, f'reports/figures/forecast_{ind}.png')
        
        # Build forecast table with uncertainty
        table_data = []
        for ind, res in results.items():
            for i, y in enumerate(forecast_years):
                table_data.append({
                    'Indicator': ind,
                    'Year': y,
                    'Baseline': round(res['baseline'][i], 1),
                    'Event_Impact': round(res['impact'][i], 1),
                    'Forecast': round(res['forecast'][i], 1),
                    'Lower_95%': round(res['lower'][i], 1),
                    'Upper_95%': round(res['upper'][i], 1)
                })
        forecast_table = pd.DataFrame(table_data)
        
        os.makedirs('reports/forecasts', exist_ok=True)
        forecast_table.to_csv('reports/forecasts/forecast_table_with_uncertainty.csv', index=False)
        logging.info("Forecast table saved to reports/forecasts/forecast_table_with_uncertainty.csv")
        
        print("\n" + "=" * 60)
        print("FORECAST TABLE 2025-2027 (with 95% Prediction Intervals)")
        print("=" * 60)
        print(forecast_table.to_string(index=False))
        
        logging.info("Forecasting completed successfully.")
        
    except Exception as e:
        logging.error(f"Forecasting failed: {e}")
        raise

if __name__ == '__main__':
    main()