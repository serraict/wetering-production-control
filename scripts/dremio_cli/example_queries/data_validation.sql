-- Data Validation Queries

-- Check for null values in specific columns
SELECT 
    COUNT(*) AS total_rows,
    SUM(CASE WHEN code IS NULL THEN 1 ELSE 0 END) AS code_nulls,
    SUM(CASE WHEN naam IS NULL THEN 1 ELSE 0 END) AS naam_nulls,
    SUM(CASE WHEN actief IS NULL THEN 1 ELSE 0 END) AS actief_nulls
FROM 
    Productie.producten;

-- Check for duplicate values in a column
SELECT 
    code, 
    COUNT(*) AS occurrences
FROM 
    Productie.producten
GROUP BY 
    code
HAVING 
    COUNT(*) > 1
ORDER BY 
    occurrences DESC;

-- Check for data outside expected range
SELECT 
    *
FROM 
    Productie.producten
WHERE 
    code < 0
    OR code > 10000;

-- Check for referential integrity (if applicable)
-- This is a hypothetical example - adjust based on actual schema
SELECT 
    p.*
FROM 
    Productie.producten p
LEFT JOIN 
    Productie.productgroepen pg
    ON p.productgroep_code = pg.code
WHERE 
    p.productgroep_code IS NOT NULL
    AND pg.code IS NULL;

-- Check for data consistency
-- This is a hypothetical example - adjust based on actual schema
SELECT 
    p.code,
    p.productgroep_code,
    p.productgroep_naam,
    pg.naam AS expected_productgroep_naam
FROM 
    Productie.producten p
JOIN 
    Productie.productgroepen pg
    ON p.productgroep_code = pg.code
WHERE 
    p.productgroep_naam <> pg.naam;

-- Check for inactive products
SELECT 
    *
FROM 
    Productie.producten
WHERE 
    actief = 0;
