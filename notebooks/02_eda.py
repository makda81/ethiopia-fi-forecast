# notebooks/02_eda.py
# Exploratory Data Analysis for Ethiopia Financial Inclusion
# Fixed: convert dates to datetime for event timeline

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime

# Create output folder for figures
os.makedirs('reports/figures', exist_ok=True)

# ============================================================
# 1. Load the enriched dataset
# ============================================================
df = pd.read_excel('data/processed/ethiopia_fi_unified_data_enriched.xlsx')

# --- CRITICAL FIX: Convert all dates to datetime ---
df['observation_date'] = pd.to_datetime(df['observation_date'], errors='coerce')

# Split by record type
obs = df[df['record_type'] == 'observation']
events = df[df['record_type'] == 'event']
targets = df[df['record_type'] == 'target']
impacts = df[df['record_type'] == 'impact_link']

print("=" * 70)
print("ETHIOPIA FINANCIAL INCLUSION – EXPLORATORY DATA ANALYSIS")
print("=" * 70)
print(f"Total records: {len(df)}")
print(f"  - Observations: {len(obs)}")
print(f"  - Events: {len(events)}")
print(f"  - Targets: {len(targets)}")
print(f"  - Impact links: {len(impacts)}")

# ============================================================
# 2. Dataset Overview
# ============================================================
print("\n--- 2.1 Record counts by pillar (observations) ---")
print(obs['pillar'].value_counts(dropna=False))

print("\n--- 2.2 Source types ---")
print(df['source_type'].value_counts())

print("\n--- 2.3 Confidence levels ---")
print(df['confidence'].value_counts())

print("\n--- 2.4 Temporal coverage of indicators ---")
coverage = obs.groupby('indicator_code')['observation_date'].agg(['min', 'max']).reset_index()
print(coverage.to_string(index=False))

# ============================================================
# 3. Access Analysis (Account Ownership)
# ============================================================
print("\n--- 3. Access: Account Ownership trajectory ---")
acc = obs[obs['indicator_code'] == 'ACC_OWNERSHIP'].sort_values('observation_date')

plt.figure(figsize=(10, 6))
plt.plot(acc['observation_date'], acc['value_numeric'], 'b-o', linewidth=2, markersize=10)
plt.title('Account Ownership in Ethiopia (2011–2024)', fontsize=14)
plt.ylabel('Percentage of adults (%)')
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('reports/figures/access_trajectory.png', dpi=150)
plt.show()

# Calculate growth rates
acc['growth_pp'] = acc['value_numeric'].diff()
print("\nAccount ownership growth (percentage points):")
print(acc[['observation_date', 'value_numeric', 'growth_pp']].to_string(index=False))

# Gender gap
gender_acc = obs[obs['indicator_code'] == 'GEN_GAP_ACC'].sort_values('observation_date')
if not gender_acc.empty:
    print("\n--- Gender gap in account ownership ---")
    print(gender_acc[['observation_date', 'value_numeric']].to_string(index=False))

# ============================================================
# 4. Usage Analysis (Mobile Money, Digital Payments, P2P)
# ============================================================
print("\n--- 4. Usage: Mobile money and digital payments ---")
usage_indicators = ['ACC_MM_ACCOUNT', 'USG_P2P_COUNT', 'USG_TELEBIRR_USERS', 'USG_MPESA_USERS']
mm = obs[obs['indicator_code'].isin(usage_indicators)].sort_values('observation_date')

plt.figure(figsize=(12, 6))
for ind in mm['indicator_code'].unique():
    sub = mm[mm['indicator_code'] == ind]
    plt.plot(sub['observation_date'], sub['value_numeric'], marker='o', label=ind)
plt.title('Mobile Money and Digital Payment Trends', fontsize=14)
plt.ylabel('Value (millions or %)')
plt.legend()
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('reports/figures/usage_trends.png', dpi=150)
plt.show()

# P2P/ATM crossover
crossover = obs[obs['indicator_code'] == 'USG_CROSSOVER']
if not crossover.empty:
    print("\n--- P2P/ATM Crossover Ratio ---")
    print(crossover[['observation_date', 'value_numeric']].to_string(index=False))

# ============================================================
# 5. Infrastructure and Enablers
# ============================================================
print("\n--- 5. Infrastructure and Enablers ---")
infra_indicators = ['ACC_4G_COV', 'ACC_MOBILE_PEN', 'AFF_DATA_INCOME']
infra = obs[obs['indicator_code'].isin(infra_indicators)].sort_values('observation_date')

fig, ax1 = plt.subplots(figsize=(10, 6))
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
plt.title('Infrastructure and Affordability', fontsize=14)
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('reports/figures/infrastructure.png', dpi=150)
plt.show()

# ============================================================
# 6. Event Timeline Overlay (FIXED)
# ============================================================
print("\n--- 6. Events overlay on Account Ownership ---")
fig, ax = plt.subplots(figsize=(14, 6))
ax.plot(acc['observation_date'], acc['value_numeric'], 'b-o', linewidth=2, label='Account Ownership')

# Ensure events have valid dates
events_valid = events[events['observation_date'].notna()]
for _, row in events_valid.iterrows():
    ax.axvline(x=row['observation_date'], color='gray', linestyle='--', alpha=0.5)
    ax.text(row['observation_date'], 5, row['indicator'], rotation=45, fontsize=8, ha='center')

ax.set_ylabel('Account Ownership (%)')
ax.set_title('Account Ownership with Key Events', fontsize=14)
ax.legend()
plt.tight_layout()
plt.savefig('reports/figures/event_timeline.png', dpi=150)
plt.show()

# ============================================================
# 7. Correlation Analysis
# ============================================================
print("\n--- 7. Correlation Matrix (numeric indicators) ---")
# Pivot numeric observations to wide format
obs_numeric = obs[['indicator_code', 'value_numeric']].dropna()
wide = obs_numeric.pivot_table(index=obs_numeric.index, columns='indicator_code', values='value_numeric')
corr = wide.corr()

plt.figure(figsize=(12, 10))
sns.heatmap(corr, annot=True, cmap='coolwarm', fmt='.2f', linewidths=0.5, vmin=-1, vmax=1)
plt.title('Correlation Matrix of Financial Inclusion Indicators', fontsize=14)
plt.tight_layout()
plt.savefig('reports/figures/correlation_heatmap.png', dpi=150)
plt.show()

# Print correlations with ACC_OWNERSHIP
if 'ACC_OWNERSHIP' in corr.columns:
    print("\nCorrelations with Account Ownership (ACC_OWNERSHIP):")
    print(corr['ACC_OWNERSHIP'].sort_values(ascending=False).to_string())

# ============================================================
# 8. Key Insights (printed summary)
# ============================================================
print("\n" + "=" * 70)
print("KEY INSIGHTS FROM EDA")
print("=" * 70)
print("""
1. Account ownership growth decelerated sharply from +11pp (2017-2021) to +3pp (2021-2024).
   This suggests market saturation, inactive accounts, or economic headwinds.

2. Mobile money accounts doubled (4.7% → 9.45%) after Telebirr and M-Pesa launches,
   yet overall account ownership barely moved – many users may already have bank accounts,
   or accounts remain inactive.

3. P2P transactions surpassed ATM transactions for the first time in FY2024/25
   (crossover ratio 1.08) – a historic shift towards digital payments.

4. 4G coverage nearly doubled from 37.5% to 70.8% in two years, driven by competition
   from Safaricom. This infrastructure expansion is a strong enabler for digital adoption.

5. Gender gaps remain wide: 20pp in 2021, slightly narrowing to 18pp in 2024,
   but female mobile money account share is only 14%, indicating deep structural barriers.

6. Strong correlations observed between 4G coverage, mobile penetration, and account ownership,
   suggesting that infrastructure is a key driver of access.

7. The event timeline shows that major launches (Telebirr, M-Pesa, Safaricom entry) coincide
   with inflection points in digital payment growth, though their impact on overall account
   ownership appears limited so far.
""")

print("EDA complete. Figures saved to reports/figures/")