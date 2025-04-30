# Doing

## Goal: Allow AI agents to inspect the local Dremio instance on the command line

Enable quick development and testing of features by providing command-line access to Dremio.

### Analysis

After evaluating multiple approaches against key use cases, we've chosen to implement this using ISQL with local ODBC driver for Dremio.

Key Use Cases:

1. Schema Inspection
   - View available tables and views in Dremio
   - Examine column definitions and data types
   - Understand relationships between tables/views
   - Check for presence of specific columns or views before development

2. Data Validation
   - Verify data quality and consistency
   - Check for null values or unexpected patterns
   - Validate data transformations
   - Test assumptions about data structure

3. Query Testing
   - Test SQL queries before implementing them in code
   - Debug complex queries
   - Measure query performance
   - Verify query results match expectations

4. Development Support
   - Generate test data based on actual schema
   - Create data fixtures for tests
   - Verify changes haven't broken existing queries
   - Explore data patterns to inform feature development

5. Troubleshooting
   - Investigate production issues
   - Compare expected vs actual data
   - Track down data inconsistencies
   - Verify data updates

Approach Evaluation:

1. ISQL with ODBC (✅ Chosen):
   - Pros:
     - Standard SQL interface familiar to developers
     - Interactive command-line experience
     - No parameter injection limitations
     - Immediate feedback loop
   - Cons:
     - ODBC setup required
     - Platform-dependent
     - Additional system dependency

2. Dremio API (Considered):
   - Pros:
     - Platform independent
     - Direct integration
     - Could be wrapped in CLI tool
   - Cons:
     - Less interactive
     - More code required for simple queries
     - Authentication overhead

3. SQLAlchemy (Considered):
   - Pros:
     - Familiar to Python developers
     - Consistent with project
   - Cons:
     - Significant limitations with Dremio
     - Parameter injection issues
     - More complex than needed for CLI use

Decision:
ISQL with ODBC was chosen because it:

1. Best supports all use cases with native SQL
2. Provides immediate interactive feedback
3. No parameter injection limitations
4. Familiar SQL interface
5. Direct command-line experience aligns with goal of quick development and testing

The ODBC setup requirement is deemed an acceptable tradeoff given:

- One-time setup cost
- Better developer experience afterward
- Full SQL capabilities
- No artificial limitations

### Tasks

1. ODBC Driver Setup
   - Document ODBC driver installation steps for Dremio
   - Configure ODBC connection settings
   - Create connection test script
   - Document connection verification process

2. ISQL Integration
   - Install isql command-line tool
   - Configure isql to use Dremio ODBC connection
   - Create basic connection test
   - Document basic query examples

3. Helper Scripts
   - Create shell script to launch isql with correct parameters
   - Add common queries for schema inspection
   - Add example queries for each use case
   - Document helper script usage

4. Documentation
   - Update README with setup instructions
   - Add example queries for each use case
   - Document troubleshooting steps
   - Add section in architecture.md about Dremio CLI access

5. Testing & Validation
   - Test all use cases:
     - Schema inspection
     - Data validation
     - Query testing
     - Development support
     - Troubleshooting
   - Document any limitations or issues found
   - Add example queries that worked well
