#!/usr/bin/env python
# notebooks/02_eda.py
# Exploratory Data Analysis with error handling and modular functions.

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_dirs():
    os.makedirs('reports/figures', exist_ok=True)

def load_enriched_data(filepath):
    try:
        df = pd.read_excel(filepath)
        df['observation_date'] = pd.to_datetime(df['observation_date'], errors='coerce')
        logging.info(f"Loaded {len(df)} records from {filepath}")
        return df
    except Exception as e:
        logging.error(f"Failed to load data: {e}")
        raise

def plot_access_trajectory(obs, save_path):
    acc = obs[obs['indicator_code'] == 'ACC_OWNERSHIP'].sort_values('observation_date')
    if acc.empty:
        logging.warning("No ACC_OWNERSHIP data found.")
        return
    plt.figure(figsize=(10,6))
    plt.plot(acc['observation_date'], acc['value_numeric'], 'b-o', linewidth=2, markersize=10)
    plt.title('Account Ownership in Ethiopia (2011–2024)')
    plt.ylabel('Percentage of adults (%)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
    logging.info(f"Saved access trajectory to {save_path}")
    return acc

def plot_usage_trends(obs, save_path):
    usage_indicators = ['ACC_MM_ACCOUNT', 'USG_P2P_COUNT', 'USG_TELEBIRR_USERS', 'USG_MPESA_USERS']
    mm = obs[obs['indicator_code'].isin(usage_indicators)].sort_values('observation_date')
    if mm.empty:
        logging.warning("No usage data found.")
        return
    plt.figure(figsize=(12,6))
    for ind in mm['indicator_code'].unique():
        sub = mm[mm['indicator_code'] == ind]
        plt.plot(sub['observation_date'], sub['value_numeric'], marker='o', label=ind)
    plt.title('Mobile Money and Digital Payment Trends')
    plt.ylabel('Value (millions or %)')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
    logging.info(f"Saved usage trends to {save_path}")

def plot_infrastructure(obs, save_path):
    infra_indicators = ['ACC_4G_COV', 'ACC_MOBILE_PEN', 'AFF_DATA_INCOME']
    infra = obs[obs['indicator_code'].isin(infra_indicators)].sort_values('observation_date')
    if infra.empty:
        logging.warning("No infrastructure data found.")
        return
    fig, ax1 = plt.subplots(figsize=(10,6))
    ax2 = ax1.twinx()
    for ind in infra['indicator_code'].unique():
        sub = infra[infra['indicator_code'] == ind]
        if ind == 'AFF_DATA_INCOME':
            ax2.plot(sub['observation_date'], sub['value_numeric'], 'r-o', label=ind)
        else:
            ax1.plot(sub['observation_date'], sub['value_numeric'], marker='o', label=ind)
    ax1.set_ylabel('Coverage / Penetration (%)')
    ax2.set_ylabel('Data cost (% of GNI)')
    ax1.legend(loc='upper left')
    ax2.legend(loc='upper right')
    plt.title('Infrastructure and Affordability')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
    logging.info(f"Saved infrastructure plot to {save_path}")

def plot_event_timeline(obs, events, save_path):
    acc = obs[obs['indicator_code'] == 'ACC_OWNERSHIP'].sort_values('observation_date')
    if acc.empty:
        logging.warning("No ACC_OWNERSHIP data for event timeline.")
        return
    fig, ax = plt.subplots(figsize=(14,6))
    ax.plot(acc['observation_date'], acc['value_numeric'], 'b-o', linewidth=2, label='Account Ownership')
    for _, row in events.iterrows():
        if pd.notna(row['observation_date']):
            ax.axvline(x=row['observation_date'], color='gray', linestyle='--', alpha=0.5)
            ax.text(row['observation_date'], 5, row['indicator'], rotation=45, fontsize=8, ha='center')
    ax.set_ylabel('Account Ownership (%)')
    ax.set_title('Account Ownership with Key Events')
    ax.legend()
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
    logging.info(f"Saved event timeline to {save_path}")

def plot_correlation_heatmap(obs, save_path):
    obs_numeric = obs[['indicator_code', 'value_numeric']].dropna()
    if obs_numeric.empty:
        logging.warning("No numeric data for correlation.")
        return
    wide = obs_numeric.pivot_table(index=obs_numeric.index, columns='indicator_code', values='value_numeric')
    corr = wide.corr()
    plt.figure(figsize=(12,10))
    sns.heatmap(corr, annot=True, cmap='coolwarm', fmt='.2f', linewidths=0.5, vmin=-1, vmax=1)
    plt.title('Correlation Matrix of Financial Inclusion Indicators')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
    logging.info(f"Saved correlation heatmap to {save_path}")

def main():
    setup_dirs()
    df = load_enriched_data('data/processed/ethiopia_fi_unified_data_enriched.xlsx')
    obs = df[df['record_type'] == 'observation']
    events = df[df['record_type'] == 'event']

    # Generate all plots
    plot_access_trajectory(obs, 'reports/figures/access_trajectory.png')
    plot_usage_trends(obs, 'reports/figures/usage_trends.png')
    plot_infrastructure(obs, 'reports/figures/infrastructure.png')
    plot_event_timeline(obs, events, 'reports/figures/event_timeline.png')
    plot_correlation_heatmap(obs, 'reports/figures/correlation_heatmap.png')

    logging.info("EDA completed successfully.")

if __name__ == "__main__":
    main()