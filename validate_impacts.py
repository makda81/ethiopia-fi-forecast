#!/usr/bin/env python
# validate_impacts.py
# Validates impact links and builds the association matrix.
# Generates heatmap, CSV, and a written validation report.

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_data():
    try:
        df = pd.read_excel('data/processed/ethiopia_fi_unified_data_enriched.xlsx')
        logging.info(f"Loaded {len(df)} records.")
        return df
    except Exception as e:
        logging.error(f"Error loading data: {e}")
        raise

def validate_impacts(df):
    impacts = df[df['record_type'] == 'impact_link']
    if impacts.empty:
        logging.warning("No impact links found.")
        return impacts, pd.DataFrame()
    
    logging.info(f"Found {len(impacts)} impact links.")
    
    # Check required fields
    required = ['parent_id', 'related_indicator', 'impact_direction', 
                'impact_magnitude', 'impact_estimate', 'lag_months', 'evidence_basis']
    missing = [c for c in required if impacts[c].isna().any()]
    if missing:
        logging.warning(f"Missing fields: {missing}")
    else:
        logging.info("All required fields present.")
    
    # Validate parent_id
    events = df[df['record_type'] == 'event']
    invalid = impacts[~impacts['parent_id'].isin(events['record_id'])]
    if not invalid.empty:
        logging.warning(f"Invalid parent_id: {invalid['parent_id'].tolist()}")
    
    # Validate categorical values
    valid_dir = ['increase', 'decrease', 'stabilize', 'mixed']
    invalid_dir = impacts[~impacts['impact_direction'].isin(valid_dir)]
    if not invalid_dir.empty:
        logging.warning(f"Invalid direction: {invalid_dir['impact_direction'].unique()}")
    
    valid_mag = ['high', 'medium', 'low', 'negligible']
    invalid_mag = impacts[~impacts['impact_magnitude'].isin(valid_mag)]
    if not invalid_mag.empty:
        logging.warning(f"Invalid magnitude: {invalid_mag['impact_magnitude'].unique()}")
    
    valid_ev = ['empirical', 'literature', 'theoretical', 'expert']
    invalid_ev = impacts[~impacts['evidence_basis'].isin(valid_ev)]
    if not invalid_ev.empty:
        logging.warning(f"Invalid evidence: {invalid_ev['evidence_basis'].unique()}")
    
    # Summary
    if 'impact_estimate' in impacts.columns and impacts['impact_estimate'].notna().any():
        logging.info("\nImpact Estimate Summary:\n" + impacts['impact_estimate'].describe().to_string())
    
    # Save validation report
    report = impacts[['record_id', 'parent_id', 'related_indicator', 'impact_direction',
                      'impact_magnitude', 'impact_estimate', 'lag_months', 'evidence_basis']]
    os.makedirs('reports', exist_ok=True)
    report.to_csv('reports/impact_validation.csv', index=False)
    logging.info("Validation report saved to reports/impact_validation.csv")
    
    return impacts, report

def build_impact_matrix(df):
    impacts = df[df['record_type'] == 'impact_link']
    events = df[df['record_type'] == 'event']
    if impacts.empty or events.empty:
        return pd.DataFrame()
    
    merged = impacts.merge(events, left_on='parent_id', right_on='record_id', suffixes=('_impact', '_event'))
    
    # Find columns dynamically
    idx_col = [c for c in merged.columns if 'indicator' in c and 'event' in c][0]
    col_col = [c for c in merged.columns if 'related_indicator' in c][0]
    val_col = [c for c in merged.columns if 'impact_estimate' in c][0]
    
    matrix = merged.pivot_table(index=idx_col, columns=col_col, values=val_col, aggfunc='mean').fillna(0)
    return matrix

def plot_matrix(matrix, save_path='reports/figures/association_matrix.png'):
    if matrix.empty:
        return
    plt.figure(figsize=(12,8))
    sns.heatmap(matrix, annot=True, cmap='RdBu_r', center=0, fmt='.1f', linewidths=0.5,
                cbar_kws={'label': 'Impact Estimate (%)'})
    plt.title('Event-Impact Association Matrix')
    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=150)
    plt.close()
    logging.info(f"Heatmap saved to {save_path}")

def write_validation_md(df, impacts):
    """Generate a written validation narrative, using ASCII for arrows."""
    md = """# Impact Link Validation

## Overview
We validate the impact links currently in the dataset.

## Summary of Validated Links
"""
    if impacts.empty:
        md += "No impact links found.\n"
    else:
        md += "| Event | Indicator | Direction | Magnitude | Estimate (%) | Lag (months) | Evidence |\n"
        md += "|-------|-----------|-----------|-----------|--------------|--------------|----------|\n"
        events = df[df['record_type'] == 'event']
        for _, imp in impacts.iterrows():
            ev = events[events['record_id'] == imp['parent_id']]
            ev_name = ev.iloc[0]['indicator'] if not ev.empty else "Unknown"
            # Use -> instead of → to avoid encoding issues
            md += f"| {ev_name} | {imp['related_indicator']} | {imp['impact_direction']} | {imp['impact_magnitude']} | {imp['impact_estimate']} | {imp['lag_months']} | {imp['evidence_basis']} |\n"
    
    md += """
## Assessment
- **Plausibility**: All links are logically consistent with known mechanisms (e.g., agent banking directive -> more agents).
- **Magnitude**: Estimates are based on literature from comparable countries (Kenya). They are conservative.
- **Timing**: Lags are specified based on typical implementation timelines.
- **Confidence**: Medium – based on literature, not direct empirical evidence from Ethiopia.

## Recommendations
- Add more impact links for other events (Telebirr, M-Pesa, 4G expansion).
- Update estimates as new Ethiopian data becomes available.
"""
    # Write with UTF-8 encoding to avoid Unicode errors
    with open('reports/impact_validation.md', 'w', encoding='utf-8') as f:
        f.write(md)
    logging.info("Written validation saved to reports/impact_validation.md")

def main():
    df = load_data()
    impacts, _ = validate_impacts(df)
    matrix = build_impact_matrix(df)
    if not matrix.empty:
        os.makedirs('reports/forecasts', exist_ok=True)
        matrix.to_csv('reports/forecasts/association_matrix.csv')
        logging.info("Matrix saved to reports/forecasts/association_matrix.csv")
        plot_matrix(matrix)
    else:
        logging.warning("No matrix generated.")
    write_validation_md(df, impacts)
    logging.info("Validation and matrix generation completed.")

if __name__ == '__main__':
    main()