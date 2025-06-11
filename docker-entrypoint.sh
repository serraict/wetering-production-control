#!/bin/bash
set -x  # Print commands as they are executed

# Print version info
production_control version
echo "Started Production Control container."

echo "Starting web server..."
python -m production_control.__web__ 2>&1 | tee -a /var/log/webapp.log &

# Keep container running and show logs
tail -f /var/log/webapp.log
