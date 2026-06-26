CREATE OR REPLACE VIEW v_reports_by_state AS
SELECT
    workstat,
    rectype,
    COUNT(*) AS report_count
FROM npdb_reports
WHERE workstat IS NOT NULL AND TRIM(workstat) <> ''
GROUP BY workstat, rectype
HAVING COUNT(*) >= {{threshold}};
