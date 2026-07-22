#!/usr/bin/env python
# enrich_data.py
# Enriches the Ethiopia financial inclusion dataset with new observations, events, and impact links.
# Includes logging, error handling, and modular functions.

import pandas as pd
from datetime import datetime
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enrichment.log'),
        logging.StreamHandler()
    ]
)

def load_data(filepath, sheet_name='ethiopia_fi_unified_data'):
    """Load the unified dataset from an Excel file."""
    try:
        df = pd.read_excel(filepath, sheet_name=sheet_name)
        logging.info(f"Loaded {len(df)} records from {filepath}")
        return df
    except FileNotFoundError:
        logging.error(f"File not found: {filepath}")
        raise
    except Exception as e:
        logging.error(f"Error loading data: {e}")
        raise

def get_next_id(df, record_type, prefix):
    """Generate the next record_id for a given record_type."""
    sub = df[df['record_type'] == record_type]
    if sub.empty:
        return f"{prefix}0001"
    try:
        max_id = sub['record_id'].max()
        num = int(max_id.split('_')[1]) + 1
        return f"{prefix}{num:04d}"
    except (IndexError, ValueError, AttributeError) as e:
        logging.error(f"Error generating ID for {record_type}: {e}")
        raise

def add_observation(df, new_record):
    """Add a new observation record to the DataFrame."""
    try:
        required = ['record_type', 'pillar', 'indicator_code', 'value_numeric', 'observation_date']
        for col in required:
            if col not in new_record or pd.isna(new_record[col]):
                raise ValueError(f"Missing required field: {col}")
        new_row = pd.DataFrame([new_record])
        return pd.concat([df, new_row], ignore_index=True)
    except Exception as e:
        logging.error(f"Failed to add observation: {e}")
        raise

def add_event(df, new_record):
    """Add a new event record to the DataFrame."""
    try:
        required = ['record_type', 'category', 'indicator', 'observation_date']
        for col in required:
            if col not in new_record or pd.isna(new_record[col]):
                raise ValueError(f"Missing required field: {col}")
        # Ensure pillar is empty for events
        new_record['pillar'] = ''
        new_row = pd.DataFrame([new_record])
        return pd.concat([df, new_row], ignore_index=True)
    except Exception as e:
        logging.error(f"Failed to add event: {e}")
        raise

def add_impact_link(df, new_record):
    """Add a new impact link record to the DataFrame."""
    try:
        required = ['record_type', 'parent_id', 'related_indicator', 'impact_direction']
        for col in required:
            if col not in new_record or pd.isna(new_record[col]):
                raise ValueError(f"Missing required field: {col}")
        new_row = pd.DataFrame([new_record])
        return pd.concat([df, new_row], ignore_index=True)
    except Exception as e:
        logging.error(f"Failed to add impact link: {e}")
        raise

def save_data(df, filepath):
    """Save the DataFrame to an Excel file."""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        df.to_excel(filepath, index=False)
        logging.info(f"Saved {len(df)} records to {filepath}")
    except Exception as e:
        logging.error(f"Failed to save data: {e}")
        raise

def main():
    """Main enrichment workflow."""
    try:
        # 1. Load data
        df = load_data('data/raw/ethiopia_fi_unified_data.xlsx')
        logging.info(f"Initial record types: {df['record_type'].value_counts().to_dict()}")

        # 2. Add new observation: Agent Density
        new_id = get_next_id(df, 'observation', 'REC_')
        new_obs = {
            'record_id': new_id,
            'record_type': 'observation',
            'category': '',
            'pillar': 'ACCESS',
            'indicator': 'Agent Density per 10,000 adults',
            'indicator_code': 'ACC_AGENT_DENSITY',
            'indicator_direction': 'higher_better',
            'value_numeric': 5.2,
            'value_type': 'rate',
            'unit': 'agents_per_10k',
            'observation_date': pd.to_datetime('2024-06-30'),
            'source_name': 'NBE / Operator reports (estimated)',
            'source_type': 'regulator',
            'source_url': 'https://nbe.gov.et',
            'confidence': 'medium',
            'collected_by': 'YourName',
            'collection_date': datetime.today().strftime('%Y-%m-%d'),
            'notes': 'Rough estimate based on ~80,000 agents and ~154M adults.'
        }
        df = add_observation(df, new_obs)
        logging.info(f"Added observation: {new_id} (Agent Density)")

        # 3. Add new observation: Smartphone Penetration
        new_id = get_next_id(df, 'observation', 'REC_')
        new_obs2 = {
            'record_id': new_id,
            'record_type': 'observation',
            'category': '',
            'pillar': 'USAGE',
            'indicator': 'Smartphone Penetration',
            'indicator_code': 'USG_SMARTPHONE_PEN',
            'indicator_direction': 'higher_better',
            'value_numeric': 28.0,
            'value_type': 'percentage',
            'unit': '%',
            'observation_date': pd.to_datetime('2024-12-31'),
            'source_name': 'ITU / GSMA (estimated)',
            'source_type': 'research',
            'source_url': 'https://www.itu.int',
            'confidence': 'high',
            'collected_by': 'YourName',
            'collection_date': datetime.today().strftime('%Y-%m-%d'),
            'notes': 'Approximate smartphone penetration in Ethiopia.'
        }
        df = add_observation(df, new_obs2)
        logging.info(f"Added observation: {new_id} (Smartphone Penetration)")

        # 4. Add new event: NBE Agent Banking Directive
        new_event_id = get_next_id(df, 'event', 'EVT_')
        new_event = {
            'record_id': new_event_id,
            'record_type': 'event',
            'category': 'regulation',
            'pillar': '',
            'indicator': 'NBE Agent Banking Directive',
            'observation_date': pd.to_datetime('2023-12-01'),
            'source_name': 'NBE',
            'source_type': 'regulator',
            'source_url': 'https://nbe.gov.et',
            'confidence': 'high',
            'collected_by': 'YourName',
            'collection_date': datetime.today().strftime('%Y-%m-%d'),
            'notes': 'Allowed banks to use agents for account opening and cash services.'
        }
        df = add_event(df, new_event)
        logging.info(f"Added event: {new_event_id} (NBE Agent Banking Directive)")

        # 5. Add impact link: Agent Directive → Agent Density
        new_impact_id = get_next_id(df, 'impact_link', 'IMP_')
        new_impact = {
            'record_id': new_impact_id,
            'parent_id': new_event_id,
            'record_type': 'impact_link',
            'pillar': 'ACCESS',
            'related_indicator': 'ACC_AGENT_DENSITY',
            'impact_direction': 'increase',
            'impact_magnitude': 'medium',
            'impact_estimate': 15.0,
            'lag_months': 6,
            'evidence_basis': 'literature',
            'comparable_country': 'Kenya',
            'collected_by': 'YourName',
            'collection_date': datetime.today().strftime('%Y-%m-%d'),
            'notes': 'Kenya experienced ~20% agent growth after similar directive.'
        }
        df = add_impact_link(df, new_impact)
        logging.info(f"Added impact link: {new_impact_id} (Agent Directive → Agent Density)")

        # 6. Add another event: Ethio Telecom 4G Network Expansion
        new_event_id2 = get_next_id(df, 'event', 'EVT_')
        new_event2 = {
            'record_id': new_event_id2,
            'record_type': 'event',
            'category': 'infrastructure',
            'pillar': '',
            'indicator': 'Ethio Telecom 4G Network Expansion',
            'observation_date': pd.to_datetime('2024-06-30'),
            'source_name': 'Ethio Telecom LEAD Report',
            'source_type': 'operator',
            'source_url': 'https://www.ethiotelecom.et',
            'confidence': 'high',
            'collected_by': 'YourName',
            'collection_date': datetime.today().strftime('%Y-%m-%d'),
            'notes': '4G coverage reached 70.8% by FY2024/25, up from 37.5% in FY2022/23.'
        }
        df = add_event(df, new_event2)
        logging.info(f"Added event: {new_event_id2} (Ethio Telecom 4G Expansion)")

        # 7. Save the enriched dataset
        save_data(df, 'data/processed/ethiopia_fi_unified_data_enriched.xlsx')

        # 8. Print summary
        logging.info(f"Final record types: {df['record_type'].value_counts().to_dict()}")
        logging.info("Enrichment completed successfully.")

    except Exception as e:
        logging.error(f"Enrichment failed: {e}")
        raise

if __name__ == "__main__":
    main()