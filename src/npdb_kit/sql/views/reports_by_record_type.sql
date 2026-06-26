CREATE OR REPLACE VIEW v_reports_by_record_type AS
SELECT
    rectype,
    reptype,
    COUNT(*) AS report_count
FROM npdb_reports
WHERE rectype IS NOT NULL AND reptype IS NOT NULL
GROUP BY rectype, reptype
HAVING COUNT(*) >= {{threshold}};
