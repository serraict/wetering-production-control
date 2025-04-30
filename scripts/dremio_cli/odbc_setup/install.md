# Installing Dremio ODBC Driver

This guide provides instructions for installing the Dremio ODBC driver on different operating systems.

## Prerequisites

- Dremio server running and accessible
- Administrative privileges on your machine
- unixODBC (for Linux/macOS) or ODBC Data Source Administrator (for Windows)

## Download Dremio ODBC Driver

Download the appropriate driver for your platform from the [Dremio download page](https://www.dremio.com/drivers/):

- Windows: `Dremio-ODBC-Driver-Windows-<version>.msi`
- macOS: `Dremio-ODBC-Driver-macOS-<version>.pkg`
- Linux: `Dremio-ODBC-Driver-Linux-<version>.tar.gz`

## Installation Instructions

### macOS

1. Install unixODBC if not already installed:

   ```bash
   brew install unixodbc
   ```

2. Install the Dremio ODBC driver:

   ```bash
   # Navigate to the download location
   cd ~/Downloads
   
   # Install the package
   sudo installer -pkg Dremio-ODBC-Driver-macOS-<version>.pkg -target /
   ```

3. Verify the installation:

   ```bash
   odbcinst -j
   ```

   This should show the ODBC driver locations and installed drivers.

### Linux (Ubuntu/Debian)

NB: use on Linux is not verified yet.

1. Install unixODBC:

   ```bash
   sudo apt-get update
   sudo apt-get install unixodbc unixodbc-dev
   ```

2. Extract and install the Dremio ODBC driver:

   ```bash
   # Navigate to the download location
   cd ~/Downloads
   
   # Extract the archive
   tar -xzf Dremio-ODBC-Driver-Linux-<version>.tar.gz
   
   # Install the driver
   cd Dremio-ODBC-Driver-Linux-<version>
   sudo ./install.sh
   ```

3. Verify the installation:

   ```bash
   odbcinst -j
   ```

### Windows

NB: use on Windows is not verified yet.

1. Run the MSI installer:
   - Double-click the downloaded `Dremio-ODBC-Driver-Windows-<version>.msi` file
   - Follow the installation wizard

2. Verify the installation:
   - Open the ODBC Data Source Administrator
   - Go to the "Drivers" tab
   - Confirm that "Dremio ODBC Driver" is listed

## Next Steps

After installing the ODBC driver, you need to configure it to connect to your Dremio instance. See [ODBC Configuration](./configuration.md) for details.

## Troubleshooting

### Driver Not Found

If the driver is not found after installation:

1. Check if the driver files exist in the expected location:
   - macOS: `/opt/dremio-odbc/`
   - Linux: `/opt/dremio-odbc/`
   - Windows: `C:\Program Files\Dremio\ODBC Driver\`

2. Ensure the driver is registered in the ODBC configuration:
   - macOS/Linux: Check `/etc/odbcinst.ini`
   - Windows: Check ODBC Data Source Administrator

### Connection Issues

If you can't connect to Dremio:

1. Verify that the Dremio server is running and accessible
2. Check your network configuration and firewall settings
3. Ensure the connection parameters are correct

For more detailed troubleshooting, see the [Dremio ODBC Driver Documentation](https://docs.dremio.com/software/drivers/odbc-driver/).
