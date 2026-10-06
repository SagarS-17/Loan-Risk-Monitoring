# Retail Loan Portfolio Underwriting & Risk Analysis 

An end-to-end data analytics project profiling risk, policy leakage, and capital allocation 
across 110,000+ retail loan applications.
This repository contains the complete pipeline: 
from raw data generation and SQL cleaning pipelines, to custom DAX risk measures 
and an interactive Power BI executive dashboard.

## Table of Contents 
- [Business Problem]
- [Project Architecture]
- [Key Business Insights]
- [Repository Structure]
- [Setup & Reproduction Guide]
- [Data Dictionary & Cleaning Pipeline]
- [Dashboard Showcase]
- [Author & Contact]

## Business Problem 
A retail banking institution identified rising portfolio delinquency and inconsistent approval 
decisions across its branch network.

The objective of this analysis is to: 
1. **Detect Underwriting Policy Leakage:** Audit manual branch overrides that bypass 
automated scorecards. 
2. **Quantify Toxic Risk Concentrations:** Measure exposure in high-DTI (> 43%) and 
subprime (< 580 Credit score) cohorts. 
3. **Optimize Capital Allocation:** Evaluate leverage risks (Loan-to-Income ratios) across 
products like Debt Consolidation. 

## Project Architecture 

A --> [Raw Data Generation - Python / NumPy] --> 110k Messy Records 
[SQL Staging & Cleansing | SQL CTE Pipeline]

B --> [Cleaned Dimension Model] [Power BI Semantic Layer | DAX Measures] 

C --> [Executive Dashboard | Risk Heatmap & Funnel Analysis]

1. Generation: Python script synthesizes 110,000 rows with deliberate data defects 
(missing data, date anomalies, impossible ages, string casing issues).


3. Cleansing & Transformation: Multi-step SQL CTE pipeline manages deduplication, 
boundary validation, cohort-level median imputation via PERCENTILE_CONT, and 
underwriting metric engineering (DTI, LTI).


5. Analytics & BI: Star schema semantic layer in Power BI using custom DAX for credit 
tiering, risk index benchmarks, and dynamic heatmap matrix visualizations.

##Key Business Insights 

● $88M in Mispriced Risk: Despite automated hard-stop policies, 18.4% of subprime applicants 
with DTI > 43% received loan approvals due to manual branch exceptions.

● Over-leveraged Debt Consolidation: Represents 40.2% of gross requested capital ($1.37B), 
carrying an average LTI of 3.82×—surpassing the institution’s 3.50× risk threshold.

● Mortgage Buffer: Applicants holding active residential mortgages experienced a 14% 
higher approval rate within identical credit score brackets (670–739 Credit score) compared to 
renters, driven by asset collateral.
