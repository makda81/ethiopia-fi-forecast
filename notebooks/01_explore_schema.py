import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Load main dataset
df = pd.read_excel('data/raw/ethiopia_fi_unified_data.xlsx', sheet_name='ethiopia_fi_unified_data')
ref = pd.read_excel('data/raw/reference_codes.xlsx', sheet_name='reference_codes')

# Basic info
print("=" * 60)
print("Record types and counts:")
print(df['record_type'].value_counts())
print("\nPillars (non‑null):")
print(df[df['pillar'].notna()]['pillar'].value_counts())
print("\nIndicators in observations:")
print(df[df['record_type']=='observation']['indicator_code'].unique())
print("\nEvent categories:")
print(df[df['record_type']=='event']['category'].value_counts())
print("\nDate range of observations:")
obs = df[df['record_type']=='observation']
print(obs['observation_date'].min(), "to", obs['observation_date'].max())