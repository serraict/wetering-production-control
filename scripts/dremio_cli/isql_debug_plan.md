# ISQL Debug Plan

This plan outlines steps to debug and resolve the ODBC driver issues for connecting to Dremio using isql.

## Issue Summary

- The Arrow Flight SQL ODBC driver is installed at `/Library/Dremio/ODBC/lib/libarrow-flight-sql-odbc.dylib`
- When trying to connect, we get: `[01000][unixODBC][Driver Manager]Can't open lib '/Library/Dremio/ODBC/lib/libarrow-flight-sql-odbc.dylib' : file not found`
- The driver has a dependency on `@rpath/libarrow-odbc..dylib` which appears to be missing

## Debug Steps

### 1. Verify Driver Installation (10 min)

```bash
# Check if the driver file exists and has correct permissions
ls -la /Library/Dremio/ODBC/lib/libarrow-flight-sql-odbc.dylib

# Check if there are any other related libraries
ls -la /Library/Dremio/ODBC/lib/

# Check the driver's dependencies
otool -L /Library/Dremio/ODBC/lib/libarrow-flight-sql-odbc.dylib
```

### 2. Check RPATH Configuration (10 min)

```bash
# Check the RPATH settings in the driver
otool -l /Library/Dremio/ODBC/lib/libarrow-flight-sql-odbc.dylib | grep -A2 RPATH

# Check if the missing library exists elsewhere on the system
find /Library -name "libarrow-odbc*"
```

### 3. Fix Missing Dependency (15 min)

If the missing library is found elsewhere:

```bash
# Create a symbolic link in the expected location
sudo mkdir -p /Library/Dremio/ODBC/lib/rpath
sudo ln -s /path/to/found/libarrow-odbc..dylib /Library/Dremio/ODBC/lib/rpath/libarrow-odbc..dylib

# Or modify the RPATH using install_name_tool
sudo install_name_tool -add_rpath /path/to/directory/containing/lib /Library/Dremio/ODBC/lib/libarrow-flight-sql-odbc.dylib
```

If the library is not found:

```bash
# Check if it's included in the Dremio ODBC driver download package
# Look for additional installation steps in the Dremio documentation
```

### 4. Verify ODBC Configuration (10 min)

```bash
# Check the ODBC driver configuration
cat /opt/homebrew/etc/odbcinst.ini

# Check the ODBC data source configuration
cat ~/.odbc.ini

# Verify that the driver name matches exactly between the two files
```

### 5. Test Connection with Verbose Logging (5 min)

```bash
# Enable ODBC tracing
export ODBCDEBUG=1
export ODBCTRACEMODE=1

# Test the connection with verbose output
isql -v Dremio
```

### 6. Try Alternative Connection Methods (10 min)

```bash
# Try connecting with the full connection string
isql -v "Driver={Arrow Flight SQL ODBC Driver};HOST=localhost;PORT=32010;UID=bot;PWD=serra1bot"

# Try using a different ODBC driver manager
brew install iodbc
iodbctest "DSN=Dremio"
```

## Fallback Options

If we can't resolve the issues within the timeframe:

1. Check if there's a newer version of the Dremio ODBC driver
2. Contact Dremio support for assistance with the ODBC driver
3. Abandon the ISQL approach and use the Python script (dremio_query.py) as the primary solution

## Success Criteria

- Successfully connect to Dremio using isql
- Execute a simple query like "SELECT 1"
- Document the solution for future reference
