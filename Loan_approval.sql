use Loan;

-- Removing duplicate records --

WITH deduplicated_data AS (
SELECT application_id, application_date, applicant_age,applicant_income, coapplicant_income, loan_amount,
loan_term, loan_purpose, credit_score, debt_to_income_ratio, employment_length, home_ownership, bankruptcies_count, loan_status,
ROW_NUMBER() OVER (
PARTITION BY application_id
ORDER BY application_date ASC
) [row_num]
FROM raw_loans
),

-- Converting date to standardized form  --

parsed_dates AS (
SELECT application_id, application_date,
CASE

	WHEN application_date LIKE '__-__-____'
		THEN CAST(CONVERT(NVARCHAR(10), CONVERT(DATE, application_date, 105)) AS DATE)

	WHEN application_date LIKE '__/__/____' 
		THEN CAST(CONVERT(NVARCHAR(10), CONVERT(DATE, application_date), 111) AS DATE)

	ELSE CAST(CONVERT(NVARCHAR(10), CONVERT(DATE, SUBSTRING(application_date,1,10), 105)) AS DATE)
END 
AS clean_application_date,
applicant_age,applicant_income, coapplicant_income, loan_amount, loan_term, loan_purpose, credit_score, debt_to_income_ratio,
employment_length, home_ownership, bankruptcies_count, loan_status
FROM deduplicated_data
WHERE row_num = 1
),

-- Rectify negative financials, nullify impossible values, standardize text --

sanitized_stage AS (
SELECT
application_id,
clean_application_date AS application_date,

-- Bounded Age: Set impossible outliers (< 18 or > 100) to NULL for imputation

CASE
WHEN applicant_age BETWEEN 18 AND 100 THEN applicant_age
ELSE NULL
END AS applicant_age_sanitized,

-- Non-negative monetary values

ABS(applicant_income) AS applicant_income_sanitized,
COALESCE(ABS(coapplicant_income), 0.0) AS coapplicant_income,
ABS(loan_amount) AS loan_amount_sanitized,
loan_term,

-- Loan Purpose: Replace underscores/hyphens, trim whitespace, standardize to Title Case

UPPER(TRIM(REPLACE(REPLACE(loan_purpose, '_', ' '), '-', ' '))) AS loan_purpose_clean,

-- FICO Bounds (300 - 850): Convert corrupted scores (e.g., 0, 999) to NULL

CASE
WHEN credit_score BETWEEN 300 AND 850 THEN credit_score
ELSE NULL
END AS credit_score_sanitized,

-- DTI ratio validity

CASE
WHEN debt_to_income_ratio BETWEEN 0.00 AND 1.50 THEN debt_to_income_ratio
ELSE NULL
END AS dti_sanitized,

-- Explicit categorical handling for employment

COALESCE(TRIM(employment_length), 'Unknown') AS employment_length,

-- Home Ownership: Upper-cased and alias mapped

CASE
WHEN UPPER(TRIM(home_ownership)) IN ('MORTG', 'MORTGAGE') THEN 'MORTGAGE'
WHEN UPPER(TRIM(home_ownership)) = 'RENT' THEN 'RENT'
WHEN UPPER(TRIM(home_ownership)) = 'OWN' THEN 'OWN'
ELSE 'OTHER'
END AS home_ownership_clean,
COALESCE(bankruptcies_count, 0) AS bankruptcies_count,
TRIM(loan_status) AS loan_status
FROM parsed_dates
),

-- Calculate partition-level medians (using PERCENTILE_CONT) for missing metrics --

imputation_baselines AS (
SELECT
*,

-- Credit score median partitioned by loan_status

PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY credit_score_sanitized)
OVER (PARTITION BY loan_status) AS median_credit_by_status,

-- Income median partitioned by loan_purpose

PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY applicant_income_sanitized)
OVER (PARTITION BY loan_purpose_clean) AS median_income_by_purpose,

-- Global median backups

PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY applicant_age_sanitized)
OVER () AS median_applicant_age,
PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY dti_sanitized)
OVER () AS median_dti
FROM sanitized_stage
),

-- Replace NULLs with cohort statistics and compute underwriting financial ratios --

final_imputed_and_engineered AS (
SELECT
application_id, application_date,

-- Age Imputation

COALESCE(applicant_age_sanitized, median_applicant_age) AS applicant_age,

-- Income Imputation

COALESCE(applicant_income_sanitized, median_income_by_purpose) AS applicant_income, coapplicant_income,

-- Total Combined Household Income

COALESCE(applicant_income_sanitized, median_income_by_purpose) + coapplicant_income AS total_household_income,
loan_amount_sanitized AS loan_amount, loan_term, loan_purpose_clean AS loan_purpose,

-- Credit Score Imputation

COALESCE(credit_score_sanitized, median_credit_by_status) AS credit_score,

-- DTI Imputation

COALESCE(dti_sanitized, median_dti) AS debt_to_income_ratio, employment_length, home_ownership_clean AS home_ownership, bankruptcies_count, loan_status,

-- Loan-to-Income (LTI)

ROUND(loan_amount_sanitized / NULLIF(COALESCE(applicant_income_sanitized,
median_income_by_purpose) + coapplicant_income, 0), 4) AS loan_to_income_ratio
FROM imputation_baselines
)

-- Final Projection --

SELECT
application_id, application_date, applicant_age, applicant_income, coapplicant_income, total_household_income, loan_amount, 
loan_term, loan_purpose, credit_score, debt_to_income_ratio, employment_length, home_ownership, bankruptcies_count, loan_to_income_ratio, loan_status
INTO clean_data
FROM final_imputed_and_engineered;
