CREATE OR REPLACE VIEW v_reports_by_year AS
SELECT
    origyear,
    rectype,
    COUNT(*) AS report_count,
    CASE WHEN COUNT(*) < {{threshold}} THEN NULL ELSE AVG(payment) END AS avg_payment,
    CASE WHEN COUNT(*) < {{threshold}} THEN NULL ELSE SUM(payment) END AS total_payment
FROM npdb_reports
WHERE origyear IS NOT NULL
GROUP BY origyear, rectype
HAVING COUNT(*) >= {{threshold}};
