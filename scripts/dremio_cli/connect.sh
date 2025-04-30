#!/bin/bash
# Connect to Dremio using isql

# Default DSN name
DSN="Dremio"

# Allow custom DSN to be specified
if [ "$1" != "" ]; then
    DSN="$1"
fi

# Connect to Dremio using isql
isql -v "$DSN"
