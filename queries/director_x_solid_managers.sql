-- Run in the workday_hr_demo Lakehouse Spark SQL editor, not its read-only SQL endpoint.
-- Rebuild the derived lookup after replacing director_x_solid_org, then refresh the semantic model.
CREATE OR REPLACE TABLE dbo.director_x_solid_managers
USING DELTA
AS
SELECT DISTINCT
    direct_manager_id AS manager_id,
    direct_manager_name AS manager_name
FROM dbo.director_x_solid_org;

-- Expected baseline: 88 employees, 15 managers, 15 unique keys, and zero integrity defects.
SELECT
    (SELECT COUNT(*) FROM dbo.director_x_solid_org) AS employees,
    (SELECT COUNT(*) FROM dbo.director_x_solid_managers) AS managers,
    (SELECT COUNT(DISTINCT manager_id) FROM dbo.director_x_solid_managers) AS unique_manager_keys,
    (SELECT COUNT(*) FROM dbo.director_x_solid_org e
        LEFT ANTI JOIN dbo.director_x_solid_managers m
        ON e.direct_manager_id = m.manager_id) AS orphan_keys,
    (SELECT COUNT(*) FROM dbo.director_x_solid_managers
        WHERE manager_id IS NULL OR TRIM(manager_id) = '') AS blank_manager_keys;
