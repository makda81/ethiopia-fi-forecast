#!/usr/bin/env python
# validate_impacts.py
# Validates impact links and builds the association matrix (events × indicators).
# Generates a heatmap and saves the matrix as CSV.

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('validation.log'),
        logging.StreamHandler()
    ]
)

def load_data():
    """Load the enriched dataset."""
    try:
        df = pd.read_excel('data/processed/ethiopia_fi_unified_data_enriched.xlsx')
        logging.info(f"Loaded {len(df)} records.")
        return df
    except FileNotFoundError:
        logging.error("Enriched dataset not found. Run enrich_data.py first.")
        raise
    except Exception as e:
        logging.error(f"Error loading data: {e}")
        raise

def validate_impacts(df):
    """
    Validate impact links for completeness and correctness.
    Returns the impacts DataFrame and a validation report.
    """
    impacts = df[df['record_type'] == 'impact_link']
    if impacts.empty:
        logging.warning("No impact links found.")
        return impacts, pd.DataFrame()
    
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
        logging.info("\nImpact Estimate Summary:")
        logging.info(impacts['impact_estimate'].describe().to_string())
    else:
        logging.warning("No impact_estimate values found.")
    
    # 7. Save validation report
    report = impacts[['record_id', 'parent_id', 'related_indicator', 'impact_direction',
                     'impact_magnitude', 'impact_estimate', 'lag_months', 'evidence_basis']]
    os.makedirs('reports', exist_ok=True)
    report.to_csv('reports/impact_validation.csv', index=False)
    logging.info("Validation report saved to reports/impact_validation.csv")
    
    return impacts, report

def build_impact_matrix(df):
    """
    Build the association matrix: events as rows, indicators as columns,
    impact_estimate as values.
    Handles column suffixes from merge.
    """
    impacts = df[df['record_type'] == 'impact_link']
    events = df[df['record_type'] == 'event']
    
    if impacts.empty or events.empty:
        logging.warning("No impacts or events to build matrix.")
        return pd.DataFrame()
    
    # Merge to get event names and categories
    merged = impacts.merge(
        events,
        left_on='parent_id',
        right_on='record_id',
        suffixes=('_impact', '_event')
    )
    
    # Dynamically find the correct columns
    # 1. Find index column (event name) – should contain 'indicator' and 'event'
    possible_index = [c for c in merged.columns if 'indicator' in c and 'event' in c]
    if possible_index:
        index_col = possible_index[0]
    else:
        raise KeyError("No column for event indicator found")
    
    # 2. Find columns column (related indicator) – should contain 'related_indicator'
    possible_columns = [c for c in merged.columns if 'related_indicator' in c]
    if possible_columns:
        columns_col = possible_columns[0]
    else:
        raise KeyError("No column for related indicator found")
    
    # 3. Find values column (impact estimate) – should contain 'impact_estimate'
    possible_values = [c for c in merged.columns if 'impact_estimate' in c]
    if possible_values:
        values_col = possible_values[0]
    else:
        raise KeyError("No column for impact estimate found")
    
    logging.info(f"Using index='{index_col}', columns='{columns_col}', values='{values_col}'")
    
    # Create matrix
    matrix = merged.pivot_table(
        index=index_col,
        columns=columns_col,
        values=values_col,
        aggfunc='mean'
    ).fillna(0)
    
    return matrix

def plot_impact_matrix(matrix, save_path='reports/figures/association_matrix.png'):
    """Plot a heatmap of the association matrix."""
    if matrix.empty:
        logging.warning("Matrix is empty; skipping plot.")
        return
    
    plt.figure(figsize=(12, 8))
    sns.heatmap(
        matrix,
        annot=True,
        cmap='RdBu_r',
        center=0,
        fmt='.1f',
        linewidths=0.5,
        cbar_kws={'label': 'Impact Estimate (%)'}
    )
    plt.title('Event-Impact Association Matrix', fontsize=14)
    plt.xlabel('Indicator')
    plt.ylabel('Event')
    plt.tight_layout()
    
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=150)
    plt.close()
    logging.info(f"Association matrix heatmap saved to {save_path}")

def main():
    """Main validation and matrix building workflow."""
    try:
        # 1. Load data
        df = load_data()
        
        # 2. Validate impact links
        impacts, report = validate_impacts(df)
        
        # 3. Build association matrix
        matrix = build_impact_matrix(df)
        if not matrix.empty:
            # Save matrix as CSV
            os.makedirs('reports/forecasts', exist_ok=True)
            matrix.to_csv('reports/forecasts/association_matrix.csv')
            logging.info("Association matrix saved to reports/forecasts/association_matrix.csv")
            
            # Print matrix summary
            print("\n" + "=" * 60)
            print("ASSOCIATION MATRIX (Events → Indicators)")
            print("=" * 60)
            print(f"Events (rows): {len(matrix)}")
            print(f"Indicators (columns): {len(matrix.columns)}")
            print("\nMatrix preview:")
            print(matrix.head())
            
            # Plot heatmap
            plot_impact_matrix(matrix)
        else:
            logging.warning("No matrix generated (empty).")
        
        logging.info("Validation and matrix generation completed successfully.")
        
    except Exception as e:
        logging.error(f"Process failed: {e}")
        raise

if __name__ == '__main__':
    main()