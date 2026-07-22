# Data Enrichment Log

## Rationale

The starter dataset lacked key drivers of financial inclusion. We added observations, events, and impact links based on the Additional Data Points Guide (Sheets B and C). Each addition is justified by its relevance to **Access** or **Usage**.

---

## New Observations

| Record ID | Indicator | Value | Date | Source | Confidence | Relevance to Access/Usage |
|-----------|-----------|-------|------|--------|------------|---------------------------|
| REC_0034 | Agent Density per 10,000 adults | 5.2 | 2024-06-30 | NBE / operator reports (estimate) | Medium | **Access**: More agents → easier to open accounts and use mobile money. |
| REC_0035 | Smartphone Penetration | 28.0% | 2024-12-31 | ITU / GSMA | High | **Usage**: Smartphones are required for digital payments and mobile money. |

---

## New Events

| Record ID | Event | Date | Category | Source | Confidence | Relevance to Access/Usage |
|-----------|-------|------|----------|--------|------------|---------------------------|
| EVT_0011 | NBE Agent Banking Directive | 2023-12-01 | regulation | NBE | High | **Access**: Enables agent network expansion → more points of access. |
| EVT_0012 | Ethio Telecom 4G Network Expansion | 2024-06-30 | infrastructure | Ethio Telecom | High | **Usage**: Better connectivity enables digital payments. |

---

## New Impact Links

| Record ID | Parent Event | Related Indicator | Impact Direction | Magnitude | Estimate | Lag (months) | Evidence Basis | Comparable Country |
|-----------|--------------|-------------------|------------------|-----------|----------|--------------|----------------|---------------------|
| IMP_0015 | EVT_0011 | ACC_AGENT_DENSITY | increase | medium | +15% | 6 | literature | Kenya |

**Evidence details:** Kenya experienced ~20% agent growth after a similar directive. We conservatively estimate +15% for Ethiopia.
