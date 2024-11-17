# Check Workflow Script Specification

## Overview
A Python implementation of the workflow status checker using Rich for improved UI. The script monitors GitHub workflow status with a clean, informative display and countdown progress bar.

## Features
- Monitor GitHub workflow status with real-time updates
- Display workflow information in a formatted panel
- Show countdown progress bar for next check
- Calculate and display total runtime
- Support both one-time check and continuous watch mode

## Implementation Details

### Command Line Interface
- Required argument: workflow_name (name of the workflow to check)
- Optional flag: --watch (enable continuous monitoring)

### Display Components
1. Status Panel
   - Workflow status
   - Conclusion (if available)
   - Branch name
   - Workflow title
   - Creation timestamp
   - Last update timestamp
   - Total runtime (including wait time)

2. Progress Display
   - Visual countdown bar
   - Bar fills from right to left (countdown)
   - No text labels on progress bar

### Data Source
- Uses GitHub CLI (gh) for workflow data retrieval
- JSON-based data parsing
- Error handling for CLI and parsing failures

### Dependencies
- Rich library for terminal UI
- GitHub CLI for workflow data

## Usage
```bash
# One-time status check
python check_workflow.py workflow_name

# Watch mode with continuous updates
python check_workflow.py workflow_name --watch
