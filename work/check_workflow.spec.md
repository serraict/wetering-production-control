# Check Workflow Script Specification

## Overview
A Python implementation of the workflow status checker using Typer for CLI and Rich for improved UI. The script monitors GitHub workflow status with a clean, informative display and countdown progress bar.

## Features
- Monitor GitHub workflow status with real-time updates
- Display workflow information in a formatted panel
- Show smooth countdown progress bar for next check
- Live runtime updates during monitoring
- Support both one-time check and continuous watch mode
- Live monitoring of running workflows

## Implementation Details

### Field Mapping
- Uses a list of tuples to map GitHub CLI fields to display labels
- Simplifies data handling and display formatting
- Easy to extend with new fields
```python
FIELDS = [
    ("status", "Status"),
    ("conclusion", "Conclusion"),
    ("headBranch", "Branch"),
    # ...
]
```

### Display Components
1. Status Panel
   - Dynamic fields based on field mapping
   - Live runtime updates every 500ms
   - Clean table layout without headers
   - Centralized display logic for consistency

2. Progress Display
   - Visual countdown bar
   - Bar fills from right to left (countdown)
   - 10-second default interval between status checks
   - Smooth updates every 500ms
   - Runtime updates synchronized with progress bar
   - No text labels on progress bar

### Runtime Calculation
- Accurate tracking for both completed and in-progress runs
- Uses workflow timestamps for completed runs
- Uses current time for in-progress runs
- Updates in real-time during monitoring
- Proper timezone handling with UTC

### Command Line Interface (Typer)
- Required argument: workflow_name (name of the workflow to check)
- Optional flags:
  * --watch, -w: Enable continuous monitoring
  * --interval, -i: Set interval between checks (default: 10s)
- Built-in help with `--help`
- Shell completion support

### Data Source
- Uses GitHub CLI (gh) for workflow data retrieval
- Dynamic JSON field selection based on mapping
- Error handling with Typer exit codes

### Dependencies
- Typer for CLI interface
- Rich library for terminal UI
- GitHub CLI for workflow data

## Usage
```bash
# Show help
python check_workflow.py --help

# One-time status check
python check_workflow.py workflow_name

# Watch mode with continuous updates
python check_workflow.py workflow_name --watch

# Watch with custom interval
python check_workflow.py workflow_name --watch --interval 15
