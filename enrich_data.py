# enrich_data.py
# Enriches the Ethiopia financial inclusion dataset with new observations, events, and impact links.

import pandas as pd
from datetime import datetime
import os

# ============================================
# 1. Load the existing unified dataset
# ============================================
df = pd.read_excel('data/raw/ethiopia_fi_unified_data.xlsx', sheet_name='ethiopia_fi_unified_data')

print("Loaded dataset with {} records.".format(len(df)))
print("Existing record types:", df['record_type'].value_counts().to_dict())

# ============================================
# 2. Helper function to generate new record IDs
# ============================================
def get_next_id(df, record_type, prefix):
    """
    Generate the next record_id for a given record_type.
    If no records of that type exist, start with prefix + '0001'.
    """
    sub = df[df['record_type'] == record_type]
    if sub.empty:
        return f"{prefix}0001"
    else:
        max_id = sub['record_id'].max()
        # max_id should be a string like 'IMP_0014'
        num = int(max_id.split('_')[1]) + 1
        return f"{prefix}{num:04d}"

# ============================================
# 3. Add a new OBSERVATION: Agent Density
# ============================================
new_id = get_next_id(df, 'observation', 'REC_')
new_obs = pd.DataFrame([{
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
    'observation_date': '2024-06-30',
    'source_name': 'NBE / Operator reports (estimated)',
    'source_type': 'regulator',
    'source_url': 'https://nbe.gov.et',
    'confidence': 'medium',
    'collected_by': 'YourName',
    'collection_date': datetime.today().strftime('%Y-%m-%d'),
    'notes': 'Rough estimate based on ~80,000 agents and ~154M adults.'
}])
df = pd.concat([df, new_obs], ignore_index=True)
print("Added observation: Agent Density")

# ============================================
# 4. Add a new OBSERVATION: Smartphone Penetration
# ============================================
new_id = get_next_id(df, 'observation', 'REC_')
new_obs2 = pd.DataFrame([{
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
    'observation_date': '2024-12-31',
    'source_name': 'ITU / GSMA (estimated)',
    'source_type': 'research',
    'source_url': 'https://www.itu.int',
    'confidence': 'high',
    'collected_by': 'YourName',
    'collection_date': datetime.today().strftime('%Y-%m-%d'),
    'notes': 'Approximate smartphone penetration in Ethiopia.'
}])
df = pd.concat([df, new_obs2], ignore_index=True)
print("Added observation: Smartphone Penetration")

# ============================================
# 5. Add a new EVENT: NBE Agent Banking Directive
# ============================================
new_event_id = get_next_id(df, 'event', 'EVT_')
new_event = pd.DataFrame([{
    'record_id': new_event_id,
    'record_type': 'event',
    'category': 'regulation',
    'pillar': '',
    'indicator': 'NBE Agent Banking Directive',
    'observation_date': '2023-12-01',
    'source_name': 'NBE',
    'source_type': 'regulator',
    'source_url': 'https://nbe.gov.et',
    'confidence': 'high',
    'collected_by': 'YourName',
    'collection_date': datetime.today().strftime('%Y-%m-%d'),
    'notes': 'Allowed banks to use agents for account opening and cash services.'
}])
df = pd.concat([df, new_event], ignore_index=True)
print("Added event: NBE Agent Banking Directive")

# ============================================
# 6. Add an IMPACT LINK: Agent Directive → Agent Density
# ============================================
new_impact_id = get_next_id(df, 'impact_link', 'IMP_')
new_impact = pd.DataFrame([{
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
}])
df = pd.concat([df, new_impact], ignore_index=True)
print("Added impact link: Agent Directive → Agent Density")

# ============================================
# 7. Add another EVENT: Ethio Telecom 4G Network Expansion
# ============================================
new_event_id2 = get_next_id(df, 'event', 'EVT_')
new_event2 = pd.DataFrame([{
    'record_id': new_event_id2,
    'record_type': 'event',
    'category': 'infrastructure',
    'pillar': '',
    'indicator': 'Ethio Telecom 4G Network Expansion',
    'observation_date': '2024-06-30',
    'source_name': 'Ethio Telecom LEAD Report',
    'source_type': 'operator',
    'source_url': 'https://www.ethiotelecom.et',
    'confidence': 'high',
    'collected_by': 'YourName',
    'collection_date': datetime.today().strftime('%Y-%m-%d'),
    'notes': '4G coverage reached 70.8% by FY2024/25, up from 37.5% in FY2022/23.'
}])
df = pd.concat([df, new_event2], ignore_index=True)
print("Added event: Ethio Telecom 4G Expansion")

# ============================================
# 8. Save the enriched dataset
# ============================================
os.makedirs('data/processed', exist_ok=True)
df.to_excel('data/processed/ethiopia_fi_unified_data_enriched.xlsx', index=False)
print(f"\nEnriched dataset saved with {len(df)} total records.")
print("Final record types:", df['record_type'].value_counts().to_dict())