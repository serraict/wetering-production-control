#!/usr/bin/env python3
"""Rich-based GitHub workflow status checker.

A Python implementation of the check_workflow.sh script using Rich for improved UI.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    Progress,
    BarColumn,
)
from rich.table import Table

console = Console()


@dataclass
class WorkflowRun:
    """Represents a GitHub workflow run."""

    status: str
    conclusion: Optional[str]
    head_branch: str
    display_title: str
    created_at: str
    updated_at: str

    @classmethod
    def from_json(cls, data: dict) -> "WorkflowRun":
        """Create WorkflowRun instance from GitHub CLI JSON output."""
        return cls(
            status=data["status"],
            conclusion=data["conclusion"],
            head_branch=data["headBranch"],
            display_title=data["displayTitle"],
            created_at=data["createdAt"],
            updated_at=data["updatedAt"],
        )

    def get_runtime(self, additional_seconds: int = 0) -> str:
        """Calculate the total runtime including additional waiting time."""
        start = datetime.strptime(self.created_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        end = datetime.strptime(self.updated_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        runtime = end - start
        total_seconds = runtime.total_seconds() + additional_seconds
        minutes, seconds = divmod(int(total_seconds), 60)
        return f"{minutes}m {seconds}s"


def get_workflow_run(workflow_name: str) -> WorkflowRun:
    """Fetch latest workflow run information using GitHub CLI."""
    try:
        result = subprocess.run(
            [
                "gh",
                "run",
                "list",
                f"--workflow={workflow_name}",
                "--limit=1",
                "--json",
                "status,conclusion,createdAt,updatedAt,headBranch,displayTitle",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(result.stdout)
        if not data:
            console.print(f"[red]No runs found for workflow: {workflow_name}")
            sys.exit(1)
        return WorkflowRun.from_json(data[0])
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error fetching workflow: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        console.print(f"[red]Error parsing GitHub CLI output: {e}")
        sys.exit(1)


def create_status_table(run: WorkflowRun, total_wait_time: int = 0) -> Table:
    """Create a Rich table displaying workflow run information."""
    table = Table(show_header=False, box=None)
    table.add_row("Status", f"[bold]{run.status}[/bold]")
    table.add_row("Conclusion", f"[bold]{run.conclusion or 'N/A'}[/bold]")
    table.add_row("Branch", f"[bold]{run.head_branch}[/bold]")
    table.add_row("Title", f"[bold]{run.display_title}[/bold]")
    table.add_row("Created", f"[bold]{run.created_at}[/bold]")
    table.add_row("Last Update", f"[bold]{run.updated_at}[/bold]")
    table.add_row("Total Runtime", f"[bold]{run.get_runtime(total_wait_time)}[/bold]")
    return table


def watch_workflow(workflow_name: str, interval: int = 10) -> None:
    """Watch workflow progress with live updates."""
    total_wait_time = 0
    update_interval = 0.5  # Update progress every 500ms
    
    while True:
        run = get_workflow_run(workflow_name)
        
        # Clear any previous output
        console.clear()
        
        # Show current status
        console.print(
            Panel(
                create_status_table(run, total_wait_time),
                title=f"Workflow: {workflow_name}",
                border_style="blue",
            )
        )

        if run.status == "completed":
            conclusion_color = "green" if run.conclusion == "success" else "red"
            console.print(
                f"\nWorkflow completed with conclusion: [{conclusion_color}]{run.conclusion}[/]"
            )
            break

        # Show countdown progress
        with Progress(
            BarColumn(),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("", total=interval)
            steps = int(interval / update_interval)
            for step in range(steps):
                progress.update(task, completed=interval - (step * update_interval))
                time.sleep(update_interval)
                total_wait_time += update_interval


def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Check GitHub workflow status with Rich UI"
    )
    parser.add_argument("workflow_name", help="Name of the workflow to check")
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch workflow progress until completion",
    )
    args = parser.parse_args()

    if args.watch:
        watch_workflow(args.workflow_name)
    else:
        run = get_workflow_run(args.workflow_name)
        table = create_status_table(run)
        console.print(
            Panel(
                table,
                title=f"Workflow: {args.workflow_name}",
                border_style="blue",
            )
        )


if __name__ == "__main__":
    main()
