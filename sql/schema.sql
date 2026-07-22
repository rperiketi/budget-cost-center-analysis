-- schema.sql
-- Defines the core table for budget vs. actual analysis by agency/cost center.

CREATE TABLE IF NOT EXISTS budget_vs_actual (
    agency_name      TEXT NOT NULL,
    fiscal_year      INTEGER NOT NULL,
    budget_amount    REAL,
    actual_amount    REAL,
    variance_amount  REAL,   -- actual - budget (positive = overspend)
    variance_pct     REAL,   -- variance_amount / budget_amount * 100
    PRIMARY KEY (agency_name, fiscal_year)
);
