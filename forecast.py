#!/usr/bin/env python
# forecast.py
# Generates forecasts for 2025-2027 with scenarios and prediction intervals.

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_data():
    df = pd.read_excel('data/processed/ethiopia_fi_unified_data_enriched.xlsx')
    df['observation_date'] = pd.to_datetime(df['observation_date'])
    return df

def prepare_trend_data(obs, indicator):
    data = obs[obs['indicator_code'] == indicator].copy().sort_values('observation_date')
    data['t'] = (data['observation_date'] - data['observation_date'].min()).dt.days / 365.25
    data['log_t'] = np.log(data['t'] + 1e-6)
    return data

def fit_trend(data, use_log=True):
    X = sm.add_constant(data['log_t'] if use_log else data['t'])
    y = data['value_numeric']
    return sm.OLS(y, X).fit()

def get_event_impacts(df, indicator, forecast_years):
    impacts = df[df['record_type'] == 'impact_link']
    events = df[df['record_type'] == 'event']
    total = np.zeros(len(forecast_years))
    for _, imp in impacts.iterrows():
        if imp['related_indicator'] != indicator:
            continue
        ev = events[events['record_id'] == imp['parent_id']]
        if ev.empty:
            continue
        ev_date = ev.iloc[0]['observation_date']
        lag = imp.get('lag_months', 0) or 0
        effect_date = ev_date + pd.DateOffset(months=int(lag))
        for i, y in enumerate(forecast_years):
            if effect_date <= pd.Timestamp(f'{y}-12-31'):
                total[i] += imp.get('impact_estimate', 0.0)
    return total

def generate_forecast(df, indicator, forecast_years, use_log=True):
    obs = df[df['record_type'] == 'observation']
    data = prepare_trend_data(obs, indicator)
    model = fit_trend(data, use_log)
    
    base_year = data['observation_date'].min()
    t_vals = np.array([(pd.Timestamp(f'{y}-12-31') - base_year).days / 365.25 for y in forecast_years])
    if use_log:
        X_forecast = sm.add_constant(np.log(t_vals + 1e-6))
    else:
        X_forecast = sm.add_constant(t_vals)
    
    pred = model.get_prediction(X_forecast)
    pred_summary = pred.summary_frame(alpha=0.05)  # 95% PI
    baseline = pred_summary['mean'].values
    lower = pred_summary['obs_ci_lower'].values
    upper = pred_summary['obs_ci_upper'].values
    
    impact = get_event_impacts(df, indicator, forecast_years)
    forecast = baseline + impact
    lower_f = lower + impact
    upper_f = upper + impact
    
    # Scenarios
    scenario_mult = {'Optimistic': 1.3, 'Base': 1.0, 'Pessimistic': 0.6}
    scenarios = {}
    for name, mult in scenario_mult.items():
        scenarios[name] = baseline + impact * mult
    
    return {
        'indicator': indicator,
        'years': forecast_years,
        'baseline': baseline,
        'impact': impact,
        'forecast': forecast,
        'lower': lower_f,
        'upper': upper_f,
        'scenarios': scenarios,
        'model': model
    }

def plot_forecast(obs, result, save_path):
    indicator = result['indicator']
    years = result['years']
    forecast_dates = [pd.Timestamp(f'{y}-12-31') for y in years]
    
    hist = obs[obs['indicator_code'] == indicator].sort_values('observation_date')
    
    plt.figure(figsize=(10,6))
    plt.plot(hist['observation_date'], hist['value_numeric'], 'bo-', label='Historical')
    plt.plot(forecast_dates, result['baseline'], 'g--', label='Baseline')
    plt.plot(forecast_dates, result['forecast'], 'ro-', label='Forecast (Base)')
    plt.fill_between(forecast_dates, result['lower'], result['upper'], color='red', alpha=0.2, label='95% PI')
    
    # Scenarios
    for name, vals in result['scenarios'].items():
        if name == 'Base':
            continue
        plt.plot(forecast_dates, vals, '--', label=f'Scenario: {name}')
    
    plt.title(f'Forecast for {indicator} (2025-2027)')
    plt.ylabel('Value (%)')
    plt.legend()
    plt.grid(True)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=150)
    plt.close()
    logging.info(f"Plot saved to {save_path}")

def main():
    df = load_data()
    obs = df[df['record_type'] == 'observation']
    forecast_years = [2025, 2026, 2027]
    indicators = ['ACC_OWNERSHIP', 'ACC_MM_ACCOUNT']
    
    # Use USG_DIGITAL_PAYMENT if available, else ACC_MM_ACCOUNT
    if 'USG_DIGITAL_PAYMENT' in obs['indicator_code'].unique():
        indicators = ['ACC_OWNERSHIP', 'USG_DIGITAL_PAYMENT']
    
    results = {}
    for ind in indicators:
        if ind not in obs['indicator_code'].unique():
            logging.warning(f"{ind} not available; skipping.")
            continue
        try:
            res = generate_forecast(df, ind, forecast_years, use_log=True)
        except:
            res = generate_forecast(df, ind, forecast_years, use_log=False)
        results[ind] = res
        plot_forecast(obs, res, f'reports/figures/forecast_{ind}.png')
    
    # Build table
    table_data = []
    for ind, res in results.items():
        for i, y in enumerate(forecast_years):
            row = {
                'Indicator': ind,
                'Year': y,
                'Baseline': round(res['baseline'][i], 1),
                'Event_Impact': round(res['impact'][i], 1),
                'Forecast': round(res['forecast'][i], 1),
                'Lower_95%': round(res['lower'][i], 1),
                'Upper_95%': round(res['upper'][i], 1)
            }
            for name, vals in res['scenarios'].items():
                row[f'Scenario_{name}'] = round(vals[i], 1)
            table_data.append(row)
    
    table = pd.DataFrame(table_data)
    os.makedirs('reports/forecasts', exist_ok=True)
    table.to_csv('reports/forecasts/forecast_table_with_uncertainty.csv', index=False)
    print("\n" + "=" * 70)
    print("FORECAST TABLE 2025-2027 with Scenarios and 95% PI")
    print("=" * 70)
    print(table.to_string(index=False))
    logging.info("Forecasting completed.")

if __name__ == '__main__':
    main()