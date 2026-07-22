#!/usr/bin/env python
# validate_impacts.py
# Validates impact links: checks completeness, direction, magnitude, lag, and evidence.

import pandas as pd
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_data():
    try:
        df = pd.read_excel('data/processed/ethiopia_fi_unified_data_enriched.xlsx')
        logging.info(f"Loaded {len(df)} records.")
        return df
    except FileNotFoundError:
        logging.error("Enriched dataset not found. Run enrich_data.py first.")
        raise

def validate_impacts(df):
    impacts = df[df['record_type'] == 'impact_link']
    if impacts.empty:
        logging.warning("No impact links found.")
        return
    
    logging.info(f"Found {len(impacts)} impact links.")
    
    # 1. Check required fields
    required_fields = ['parent_id', 'related_indicator', 'impact_direction', 
                       'impact_magnitude', 'impact_estimate', 'lag_months', 
                       'evidence_basis']
    missing = []
    for col in required_fields:
        missing_count = impacts[col].isna().sum()
        if missing_count > 0:
            missing.append(f"{col}: {missing_count} missing")
    if missing:
        logging.warning("Missing fields: " + "; ".join(missing))
    else:
        logging.info("All required fields are present.")
    
    # 2. Check that parent_id exists in events
    events = df[df['record_type'] == 'event']
    valid_parents = impacts['parent_id'].isin(events['record_id'])
    invalid = impacts[~valid_parents]
    if not invalid.empty:
        logging.warning(f"{len(invalid)} impact links have invalid parent_id: {invalid['parent_id'].tolist()}")
    else:
        logging.info("All parent_id references are valid.")
    
    # 3. Check impact_direction values
    valid_directions = ['increase', 'decrease', 'stabilize', 'mixed']
    invalid_dir = impacts[~impacts['impact_direction'].isin(valid_directions)]
    if not invalid_dir.empty:
        logging.warning(f"Invalid impact_direction values: {invalid_dir['impact_direction'].unique()}")
    
    # 4. Check impact_magnitude values
    valid_magnitudes = ['high', 'medium', 'low', 'negligible']
    invalid_mag = impacts[~impacts['impact_magnitude'].isin(valid_magnitudes)]
    if not invalid_mag.empty:
        logging.warning(f"Invalid impact_magnitude values: {invalid_mag['impact_magnitude'].unique()}")
    
    # 5. Check evidence_basis
    valid_evidence = ['empirical', 'literature', 'theoretical', 'expert']
    invalid_ev = impacts[~impacts['evidence_basis'].isin(valid_evidence)]
    if not invalid_ev.empty:
        logging.warning(f"Invalid evidence_basis values: {invalid_ev['evidence_basis'].unique()}")
    
    # 6. Summary statistics of impact_estimate
    if 'impact_estimate' in impacts.columns and impacts['impact_estimate'].notna().any():
        print("\nImpact Estimate Summary:")
        print(impacts['impact_estimate'].describe())
    
    # 7. Save validation report
    report = impacts[['record_id', 'parent_id', 'related_indicator', 'impact_direction',
                     'impact_magnitude', 'impact_estimate', 'lag_months', 'evidence_basis']]
    os.makedirs('reports', exist_ok=True)
    report.to_csv('reports/impact_validation.csv', index=False)
    logging.info("Validation report saved to reports/impact_validation.csv")
    
    return impacts

def main():
    df = load_data()
    validate_impacts(df)

if __name__ == '__main__':
    main()