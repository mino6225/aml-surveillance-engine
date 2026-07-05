# aml-surveillance-engine

# AML Transaction Surveillance Engine
A Python-based anti-money laundering (AML) surveillance system that generates synthetic transaction data, detects suspicious behavioral patterns using a five-rule engine, scores accounts by risk level, maps transaction networks, and produces structured Suspicious Activity Reports (SARs).
Built as a portfolio project targeting roles in financial crime, risk intelligence, and compliance technology.

# Overview
This project simulates a transaction monitoring system of the kind used by financial institutions to detect money laundering. It generates a dataset of 1,090 transactions with planted suspicious patterns, runs each transaction through five AML detection rules, assigns weighted risk scores to flagged accounts, visualizes the transaction network, and outputs SAR narratives for the highest-risk accounts.

# Modules
1 — Synthetic Data GenerationGenerates 1,000 random transactions plus planted structuring, rapid movement, and round-trip patterns across known suspect accounts

2 — Data Ingestion and CleaningLoads and validates the dataset, checks for nulls and duplicate IDs, enforces correct data types

3 — AML Rule EngineRuns five detection rules against the cleaned dataset and stores structured results for each rule

4 — Risk ScoringAssigns weighted scores to flagged accounts and classifies them into High, Medium, and Low risk tiers

5 — Network AnalysisBuilds a transaction graph using NetworkX, calculates account degree centrality, and generates an interactive PyVis visualization color-coded by risk tier

6 — SAR Report GeneratorProduces structured Suspicious Activity Reports for all High risk accounts, including triggered rules, associated counterparties, and a plain-English narrative

# AML Detection Rules
LogicHRJ-001: High Risk Jurisdiction. Flags transactions involving OFAC-designated or high-risk jurisdictions (Iran, North Korea, Syria, Myanmar, Cuba)

STR-001: Structuring. Detects repeated cash deposits between $9,000–$9,999 within a 30-day window — a pattern consistent with deliberate threshold avoidance.

RMV-001: Rapid Movement. Flags wire transfers from the same account occurring within 6 hours of each other, indicating potential layering.

RRT-001: Round Trip Transactions. Identifies account pairs sending money back and forth within 6 hours at near-identical amounts (within 6% tolerance).

VEL-001: Velocity Anomaly. Flags transactions where the amount exceeds the account's historical mean by more than 2 standard deviations

# Risk Scoring
Rules are weighted by severity and combined into a composite score per account:
RRT-001:5
VEL-001:4
STR-001:3
RMV-001:2
HRJ-001:1
Risk tiers: High (score ≥ 5) · Medium (score 3–4) · Low (score 1–2)

# Tech Stack

Python 3
pandas
NetworkX
PyVis
uuid, datetime, dataclasses


# Future Enhancements

RMV-001 channel expansion — Rapid movement currently detects wire-to-wire patterns only. Future versions would catch cross-channel movement (e.g. cash deposit → wire out within a short window)
Frequency-based velocity — VEL-001 currently flags amount anomalies only. Transaction frequency per account per time window would add a complementary signal
Live data integration — Replace synthetic generator with real transaction feed via API
SAR export — Output SAR reports to structured CSV or PDF for compliance workflow integration

