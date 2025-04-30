-- Schema Inspection Queries

-- List all schemas
SHOW SCHEMAS;

-- List all tables in the current schema
SHOW TABLES;

-- List all tables in a specific schema
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

-- Show primary keys (if available in Dremio)
SELECT 
    tc.constraint_name, 
    kcu.column_name
FROM 
    INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
JOIN 
    INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
    ON tc.constraint_name = kcu.constraint_name
WHERE 
    tc.constraint_type = 'PRIMARY KEY'
    AND tc.table_schema = 'Productie'
    AND tc.table_name = 'producten';

-- Show table statistics
SELECT 
    'Productie' AS table_schema,
    'producten' AS table_name,
    COUNT(*) AS row_count
FROM 
    Productie.producten;
