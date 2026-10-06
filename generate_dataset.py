import numpy as np
import pandas as pd

# ---------------------------------------------------------
# Configuration & Seed Initialization
# ---------------------------------------------------------
np.random.seed(42)
TOTAL_TARGET_ROWS = 110_000
DUPLICATE_COUNT = 850
BASE_ROWS = TOTAL_TARGET_ROWS - DUPLICATE_COUNT

print(f"Generating {BASE_ROWS} unique base records...")

# ---------------------------------------------------------
# 1. Base Attributes Generation (Vectorized)
# ---------------------------------------------------------
# Application IDs
app_ids = np.array([f"APP-{i:07d}" for i in range(1000000, 1000000 + BASE_ROWS)])

# Application Dates (2021-01-01 to 2025-12-31)
start_date = np.datetime64("2021-01-01")
end_date = np.datetime64("2025-12-31")
date_range_days = (end_date - start_date).astype(int)
random_days = np.random.randint(0, date_range_days, size=BASE_ROWS)
app_dates_dt = start_date + random_days.astype("timedelta64[D]")
# Format mostly as ISO standard string
app_dates = pd.to_datetime(app_dates_dt).strftime("%Y-%m-%d").to_numpy(dtype=object)

# Applicant Age: Normal centered around 42, clipped 21-70
applicant_age = np.clip(np.random.normal(loc=42, scale=12, size=BASE_ROWS).astype(int), 21, 70)

# Applicant Income: Log-normal distribution (median ~$65k, right-skewed tail)
applicant_income = np.round(np.random.lognormal(mean=11.08, sigma=0.45, size=BASE_ROWS), 2)

# Co-applicant Income: ~45% zero, rest right-skewed up to ~$150k
coapplicant_present = np.random.binomial(1, 0.55, size=BASE_ROWS)
raw_coapplicant_income = np.random.lognormal(mean=10.4, sigma=0.5, size=BASE_ROWS)
coapplicant_income = np.round(coapplicant_present * np.clip(raw_coapplicant_income, 10000, 150000), 2)

# Loan Amount: Log-normal, mostly $5k to $500k
loan_amount = np.round(np.clip(np.random.lognormal(mean=11.5, sigma=0.75, size=BASE_ROWS), 5000, 500000), -2)

# Loan Term: Standard retail terms
loan_term = np.random.choice([36, 60, 180, 360], size=BASE_ROWS, p=[0.25, 0.35, 0.15, 0.25])

# Loan Purpose
purposes = ['Debt Consolidation', 'Home Purchase', 'Home Improvement', 'Auto', 'Small Business', 'Education']
loan_purpose = np.random.choice(purposes, size=BASE_ROWS, p=[0.40, 0.22, 0.14, 0.12, 0.08, 0.04])

# Credit Score: Beta distribution mapped across FICO range (300 to 850)
raw_score = np.random.beta(a=5, b=2.2, size=BASE_ROWS)
credit_score = np.round(300 + (raw_score * 550)).astype(int)

# Debt to Income (DTI): Beta distribution between ~0.05 and 0.65
debt_to_income = np.round(np.random.beta(a=2.5, b=5.0, size=BASE_ROWS) * 0.70 + 0.05, 4)

# Employment Length
emp_categories = ['< 1 year', '1-3 years', '4-7 years', '8+ years', 'Unemployed']
employment_length = np.random.choice(emp_categories, size=BASE_ROWS, p=[0.14, 0.28, 0.32, 0.22, 0.04]).astype(object)

# Home Ownership
ownership_categories = ['RENT', 'MORTGAGE', 'OWN', 'OTHER']
home_ownership = np.random.choice(ownership_categories, size=BASE_ROWS, p=[0.38, 0.48, 0.12, 0.02]).astype(object)

# Bankruptcies Count
bankruptcies_count = np.random.choice([0, 1, 2, 3], size=BASE_ROWS, p=[0.86, 0.10, 0.03, 0.01])

# ---------------------------------------------------------
# 2. Target Variable Generation (Underwriting Logic)
# ---------------------------------------------------------
# Construct a logistic risk score reflecting true lending decisions
log_odds = (
    -3.2
    + (credit_score - 580) * 0.015
    - (debt_to_income - 0.35) * 4.5
    + (np.log(np.maximum(applicant_income, 1000)) - 11.0) * 0.75
    - (loan_amount / np.maximum(applicant_income, 1000)) * 0.15
    - (bankruptcies_count * 0.85)
)
approval_prob = 1 / (1 + np.exp(-log_odds))
loan_status = np.where(np.random.uniform(0, 1, size=BASE_ROWS) < approval_prob, 'Approved', 'Rejected')

# ---------------------------------------------------------
# 3. Deliberate Data Quality Injections
# ---------------------------------------------------------
print("Injecting deliberate real-world data quality defects...")

# A. Outliers and Edge Cases
# Negative incomes (0.1%)
neg_income_idx = np.random.choice(BASE_ROWS, size=int(BASE_ROWS * 0.001), replace=False)
applicant_income[neg_income_idx] = -np.abs(applicant_income[neg_income_idx])

# Negative loan amounts (0.05%)
neg_loan_idx = np.random.choice(BASE_ROWS, size=int(BASE_ROWS * 0.0005), replace=False)
loan_amount[neg_loan_idx] = -np.abs(loan_amount[neg_loan_idx])

# Out-of-bounds credit scores (999 or 0)
err_score_idx = np.random.choice(BASE_ROWS, size=int(BASE_ROWS * 0.002), replace=False)
credit_score[err_score_idx] = np.random.choice([0, 999], size=len(err_score_idx))

# Impossible applicant ages (14 or 120)
err_age_idx = np.random.choice(BASE_ROWS, size=45, replace=False)
applicant_age[err_age_idx] = np.random.choice([14, 15, 118, 120], size=len(err_age_idx))

# B. String Formatting & Inconsistencies
# home_ownership: Mix case variations and trailing whitespace
for i in np.random.choice(BASE_ROWS, size=int(BASE_ROWS * 0.12), replace=False):
    val = home_ownership[i]
    if val == 'RENT':
        home_ownership[i] = np.random.choice(['rent', 'Rent ', 'RENT  '])
    elif val == 'MORTGAGE':
        home_ownership[i] = np.random.choice(['Mortgage', 'mortgage', 'MORTG'])
    elif val == 'OWN':
        home_ownership[i] = 'own '

# loan_purpose: Mix snake_case and hyphenated representations
for i in np.random.choice(BASE_ROWS, size=int(BASE_ROWS * 0.10), replace=False):
    val = loan_purpose[i]
    if val == 'Debt Consolidation':
        loan_purpose[i] = np.random.choice(['debt_consolidation', 'debt-consolidation', 'DEBT CONSOLIDATION'])
    elif val == 'Home Purchase':
        loan_purpose[i] = 'home_purchase'

# application_date: Introduce non-standard string formats (~5%)
mixed_date_idx = np.random.choice(BASE_ROWS, size=int(BASE_ROWS * 0.05), replace=False)
pd_dates = pd.to_datetime(app_dates[mixed_date_idx])
format_choices = [
    pd_dates.strftime("%m/%d/%Y").to_numpy(),
    pd_dates.strftime("%d-%m-%Y").to_numpy(),
    pd_dates.strftime("%Y/%m/%d %H:%M:%S").to_numpy()
]
app_dates[mixed_date_idx] = np.choose(
    np.random.choice([0, 1, 2], size=len(mixed_date_idx)), 
    format_choices
)

# Convert numeric arrays with missing values to float to hold np.nan
applicant_income = applicant_income.astype(float)
debt_to_income = debt_to_income.astype(float)
credit_score = credit_score.astype(float)

# C. Missing / Null Values (NaNs)
applicant_income[np.random.choice(BASE_ROWS, size=int(BASE_ROWS * 0.04), replace=False)] = np.nan
debt_to_income[np.random.choice(BASE_ROWS, size=int(BASE_ROWS * 0.06), replace=False)] = np.nan
employment_length[np.random.choice(BASE_ROWS, size=int(BASE_ROWS * 0.07), replace=False)] = np.nan
credit_score[np.random.choice(BASE_ROWS, size=int(BASE_ROWS * 0.03), replace=False)] = np.nan

# ---------------------------------------------------------
# 4. DataFrame Assembly & Duplication
# ---------------------------------------------------------
df = pd.DataFrame({
    'application_id': app_ids,
    'application_date': app_dates,
    'applicant_age': applicant_age,
    'applicant_income': applicant_income,
    'coapplicant_income': coapplicant_income,
    'loan_amount': loan_amount,
    'loan_term': loan_term,
    'loan_purpose': loan_purpose,
    'credit_score': credit_score,
    'debt_to_income_ratio': debt_to_income,
    'employment_length': employment_length,
    'home_ownership': home_ownership,
    'bankruptcies_count': bankruptcies_count,
    'loan_status': loan_status
})

# Sample and append duplicate rows
duplicate_rows = df.sample(n=DUPLICATE_COUNT, replace=True, random_state=42)
df_final = pd.concat([df, duplicate_rows], ignore_index=True)

# Shuffle rows so duplicates and anomalies distribute throughout
df_final = df_final.sample(frac=1.0, random_state=42).reset_index(drop=True)

# ---------------------------------------------------------
# 5. Export and Validation
# ---------------------------------------------------------
output_filename = "synthetic_loan_approval_messy.csv"
df_final.to_csv(output_filename, index=False)

print("\n--- Generation Complete ---")
print(f"File exported successfully: {output_filename}")
print(f"Total Rows: {len(df_final):,}")
print(f"Total Columns: {df_final.shape[1]}")
print(f"Approval Distribution:\n{df_final['loan_status'].value_counts(normalize=True).round(3)}")
print(f"\nNull Count Summary:\n{df_final.isnull().sum()[df_final.isnull().sum() > 0]}")