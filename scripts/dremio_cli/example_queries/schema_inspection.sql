-- Schema Inspection Queries

-- List all schemas
SHOW SCHEMAS;

-- List all tables in a specific schema (note: schema name is required)
SHOW TABLES IN Productie;

-- Show table details
DESCRIBE TABLE Productie.producten;

-- Show table columns
SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM 
    INFORMATION_SCHEMA.COLUMNS
WHERE 
    table_schema = 'Productie' 
    AND table_name = 'producten'
ORDER BY 
    ordinal_position;


-- Show table statistics
SELECT 
    'Productie' AS table_schema,
    'producten' AS table_name,
    COUNT(*) AS row_count
FROM 
    Productie.producten;
