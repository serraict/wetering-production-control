# Check Workflow Script Specification

## Overview
A Python implementation of the workflow status checker using Typer for CLI and Rich for improved UI. The script monitors GitHub workflow status with a clean, informative display and countdown progress bar.

## Features
- Monitor GitHub workflow status with real-time updates
- Display workflow information in a formatted panel
- Show smooth countdown progress bar for next check
- Calculate and display total runtime
- Support both one-time check and continuous watch mode
- Live monitoring of running workflows

## Implementation Details

### Command Line Interface (Typer)
- Required argument: workflow_name (name of the workflow to check)
- Optional flags:
  * --watch, -w: Enable continuous monitoring
  * --interval, -i: Set interval between checks (default: 10s)
- Built-in help with `--help`
- Shell completion support

### Display Components
1. Status Panel
   - Workflow status (in_progress/completed)
   - Conclusion (success/failure/N/A)
   - Branch name
   - Workflow title
   - Creation timestamp
   - Last update timestamp
   - Total runtime (calculated from timestamps)

2. Progress Display
   - Visual countdown bar
   - Bar fills from right to left (countdown)
   - 10-second default interval between status checks
   - Smooth updates every 500ms
   - No text labels on progress bar

### Data Source
- Uses GitHub CLI (gh) for workflow data retrieval
- JSON-based data parsing
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
