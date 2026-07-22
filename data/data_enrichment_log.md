# Data Enrichment Log

## Rationale

The starter dataset lacked several key drivers of financial inclusion. Based on the Additional Data Points Guide (Sheets B and C), we added observations, events, and impact links to improve forecasting.

---

## New Observations

| Record ID | Indicator | Value | Date | Source | Confidence | Rationale |
|-----------|-----------|-------|------|--------|------------|-----------|
| REC_0034 | Agent Density per 10,000 adults | 5.2 | 2024-06-30 | NBE / operator reports (estimate) | Medium | Direct correlate of access; higher agent density → greater access. |
| REC_0035 | Smartphone Penetration | 28.0% | 2024-12-31 | ITU / GSMA | High | Key enabler for digital payments and mobile money usage. |

---

## New Events

| Record ID | Event | Date | Category | Source | Confidence | Rationale |
|-----------|-------|------|----------|--------|------------|-----------|
| EVT_0011 | NBE Agent Banking Directive | 2023-12-01 | regulation | NBE | High | Allows banks to use agents for onboarding and cash services; likely to boost agent density. |
| EVT_0012 | Ethio Telecom 4G Network Expansion | 2024-06-30 | infrastructure | Ethio Telecom | High | Major network upgrade; 4G coverage rose from 37.5% to 70.8%, enabling digital services. |

---

## New Impact Links

| Record ID | Parent Event | Related Indicator | Impact Direction | Magnitude | Estimate | Lag (months) | Evidence Basis | Comparable Country |
|-----------|--------------|-------------------|------------------|-----------|----------|--------------|----------------|---------------------|
| IMP_0015 | EVT_0011 | ACC_AGENT_DENSITY | increase | medium | +15% | 6 | literature | Kenya |

**Evidence details:** Kenya experienced ~20% agent growth after a similar agent banking directive. We conservatively estimate +15% for Ethiopia due to different market conditions.

---

## Data Integrity Checks

- All new records follow the unified schema.
- No duplicates in `record_id`.
- Events have empty `pillar` to avoid bias.
- Impact links have a valid `parent_id` referencing an existing event.

## Next Steps

- More impact links will be added in Task 3 based on model results and literature.
- Additional observations (e.g., merchant acceptance, gender‑disaggregated data) may be added later.
