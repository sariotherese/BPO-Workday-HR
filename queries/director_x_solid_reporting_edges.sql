-- Run in the workday_hr_demo Lakehouse Spark SQL editor, not its read-only SQL endpoint.
-- Rebuild after replacing director_x_solid_org, then refresh ReportingEdges in the semantic model.
CREATE OR REPLACE TABLE dbo.director_x_solid_reporting_edges
USING DELTA
AS
SELECT worker_id, direct_manager_id
FROM dbo.director_x_solid_org
WHERE reporting_depth_from_director > 0;

-- Expected baseline: 87 unique edges, with no missing endpoints or blank keys.
SELECT
    (SELECT COUNT(*) FROM dbo.director_x_solid_reporting_edges) AS reporting_edges,
    (SELECT COUNT(DISTINCT worker_id) FROM dbo.director_x_solid_reporting_edges) AS unique_workers,
    (SELECT COUNT(*) FROM dbo.director_x_solid_reporting_edges r
        LEFT ANTI JOIN dbo.director_x_solid_org e
        ON r.worker_id = e.worker_id) AS missing_workers,
    (SELECT COUNT(*) FROM dbo.director_x_solid_reporting_edges r
        LEFT ANTI JOIN dbo.director_x_solid_org e
        ON r.direct_manager_id = e.worker_id) AS missing_managers,
    (SELECT COUNT(*) FROM dbo.director_x_solid_reporting_edges
        WHERE worker_id IS NULL OR TRIM(worker_id) = ''
           OR direct_manager_id IS NULL OR TRIM(direct_manager_id) = '') AS blank_keys;
