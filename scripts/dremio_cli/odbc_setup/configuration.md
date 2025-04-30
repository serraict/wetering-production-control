# ODBC Configuration for Dremio

This guide explains how to configure the ODBC connection to Dremio using the installed Arrow Flight SQL ODBC driver.

## Current Setup

The Arrow Flight SQL ODBC driver is already installed and appears in the ODBC Manager as "Arrow Flight SQL ODBC DSN".

## Known Issues

We've encountered some issues with the ODBC driver:

1. The driver file exists at `/Library/Dremio/ODBC/lib/libarrow-flight-sql-odbc.dylib` but has a dependency on `@rpath/libarrow-odbc..dylib` which is missing.
2. When trying to connect using isql, we get the error: `[01000][unixODBC][Driver Manager]Can't open lib '/Library/Dremio/ODBC/lib/libarrow-flight-sql-odbc.dylib' : file not found`

These issues need to be resolved before the ODBC connection can be used. In the meantime, we recommend using the Flight SQL connection directly as described in the project's README.

## Creating a Data Source Name (DSN)

### Using ODBC Manager (macOS)

1. Open ODBC Manager
2. Go to the "User DSN" or "System DSN" tab
3. Click "Add..."
4. Select "Arrow Flight SQL ODBC Driver" from the list
5. Configure the connection with the following parameters:
   - **Name**: `Dremio` (or any name you prefer)
   - **Description**: `Dremio ODBC Connection for Production Control`
   - **Host**: `localhost`
   - **Port**: `32010`
   - **AuthenticationType**: `Basic Authentication`
   - **UID**: `username`
   - **PWD**: `password`
   - **UseEncryption**: Unchecked
6. Click "OK" to save the DSN

### Manual Configuration (macOS)

Alternatively, you can manually edit the odbc.ini file:

```bash
# Edit user-specific configuration
nano ~/.odbc.ini
```

Add the following configuration:

```ini
[Dremio]
Description=Dremio ODBC Connection for Production Control
Driver=Arrow Flight SQL ODBC Driver
HOST=localhost
PORT=32010
AuthenticationType=Basic Authentication
UID=username
PWD=password
UseEncryption=false
```

## Testing the Connection

Test the connection using isql:

```bash
isql -v Dremio
```

If successful, you should see:

```
+---------------------------------------+
| Connected!                            |
|                                       |
| sql-statement                         |
| help [tablename]                      |
| quit                                  |
|                                       |
+---------------------------------------+
```

## Connection Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| Driver | Name of the ODBC driver | Arrow Flight SQL ODBC Driver |
| HOST | Hostname or IP address of the Dremio server | localhost |
| PORT | Port number for the Dremio server | 32010 |
| AuthenticationType | Authentication method | Basic Authentication |
| UID | Username for Dremio | username |
| PWD | Password for Dremio | password |
| UseEncryption | Whether to use encryption | false |

These parameters should match the Flight SQL connection string used in the project's .env file:
`dremio+flight://username:password@localhost:32010/dremio?UseEncryption=false`

**Note:** Use the actual username and password from your .env file when configuring the DSN.

## Troubleshooting

### Connection Failed

If you see "Connection Failed" when testing with isql:

1. Verify the Dremio server is running
2. Check that the HOST and PORT are correct
3. Ensure the username and password are valid
4. Check firewall settings

### Driver Not Found

If you see "Driver not found" or similar:

1. Verify the driver name in odbc.ini matches exactly what's shown in ODBC Manager
2. Try using the full path to the driver in the configuration

### Permission Issues

If you encounter permission issues:

1. Try using user-specific configuration files (~/.odbc.ini) instead of system-wide ones
2. Check file permissions on the ODBC configuration files

## References

- [Dremio ODBC Driver Documentation](https://docs.dremio.com/software/drivers/odbc-driver/)
- [unixODBC Documentation](http://www.unixodbc.org/doc/)
