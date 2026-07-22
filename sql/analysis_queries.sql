-- analysis_queries.sql
-- Core variance analysis for the Budget Forecasting & Cost Center Analysis project.
-- Run these against budget_analysis.db (e.g. via `sqlite3 budget_analysis.db` or DB Browser for SQLite).

-- ============================================================
-- 1. Latest-year variance by agency (the core "budget vs actual" view)
-- ============================================================
SELECT
    agency_name,
    fiscal_year,
    budget_amount,
    actual_amount,
    variance_amount,
    ROUND(variance_pct, 2) AS variance_pct
FROM budget_vs_actual
WHERE fiscal_year = (SELECT MAX(fiscal_year) FROM budget_vs_actual)
ORDER BY variance_pct DESC;


-- ============================================================
-- 2. At-risk department flagging
--    Risk tiers based on how far actual spend has strayed from budget.
--    Thresholds below are a starting point -- tune them once you see
--    the real distribution of variance_pct in your data.
-- ============================================================
SELECT
    agency_name,
    fiscal_year,
    budget_amount,
    actual_amount,
    ROUND(variance_pct, 2) AS variance_pct,
    CASE
        WHEN variance_pct >= 15 THEN 'HIGH RISK'
        WHEN variance_pct >= 5  THEN 'AT RISK'
        WHEN variance_pct <= -15 THEN 'SIGNIFICANT UNDERSPEND'
        ELSE 'ON TRACK'
    END AS risk_flag
FROM budget_vs_actual
WHERE fiscal_year = (SELECT MAX(fiscal_year) FROM budget_vs_actual)
ORDER BY variance_pct DESC;


-- ============================================================
-- 3. Count of at-risk departments (this is where your "12 at-risk,
--    4 high-risk" style number comes from -- computed, not assumed)
-- ============================================================
SELECT
    CASE
        WHEN variance_pct >= 15 THEN 'HIGH RISK'
        WHEN variance_pct >= 5  THEN 'AT RISK'
        WHEN variance_pct <= -15 THEN 'SIGNIFICANT UNDERSPEND'
        ELSE 'ON TRACK'
    END AS risk_flag,
    COUNT(*) AS num_departments
FROM budget_vs_actual
WHERE fiscal_year = (SELECT MAX(fiscal_year) FROM budget_vs_actual)
GROUP BY risk_flag
ORDER BY num_departments DESC;


-- ============================================================
-- 4. Multi-year trend per agency (feeds the "forecast vs actual" story --
--    shows whether an agency's variance is a one-off or a persistent pattern)
-- ============================================================
SELECT
    agency_name,
    fiscal_year,
    budget_amount,
    actual_amount,
    ROUND(variance_pct, 2) AS variance_pct
FROM budget_vs_actual
ORDER BY agency_name, fiscal_year;


-- ============================================================
-- 5. Agencies with CONSISTENT overspending (2+ years in a row over budget)
--    -- more compelling than a single bad year, good "insight" for your README
-- ============================================================
WITH overspend_flag AS (
    SELECT
        agency_name,
        fiscal_year,
        variance_pct,
        CASE WHEN variance_pct > 0 THEN 1 ELSE 0 END AS is_over
    FROM budget_vs_actual
)
SELECT
    agency_name,
    COUNT(*) AS years_tracked,
    SUM(is_over) AS years_over_budget,
    ROUND(AVG(variance_pct), 2) AS avg_variance_pct
FROM overspend_flag
GROUP BY agency_name
HAVING SUM(is_over) >= 2
ORDER BY avg_variance_pct DESC;
