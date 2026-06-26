CREATE OR REPLACE VIEW v_malpractice_payment_trends AS
SELECT
    origyear,
    COUNT(*) AS payment_report_count,
    CASE WHEN COUNT(*) < {{threshold}} THEN NULL ELSE AVG(payment) END AS avg_payment,
    CASE WHEN COUNT(*) < {{threshold}} THEN NULL ELSE MEDIAN(payment) END AS median_payment,
    CASE WHEN COUNT(*) < {{threshold}} THEN NULL ELSE SUM(payment) END AS total_payment
FROM npdb_reports
WHERE rectype IN ('M', 'P')
  AND payment IS NOT NULL
  AND origyear IS NOT NULL
GROUP BY origyear
HAVING COUNT(*) >= {{threshold}};
