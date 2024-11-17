#!/usr/bin/env python3
"""Rich-based GitHub workflow status checker.

A Python implementation of the check_workflow.sh script using Rich for improved UI.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    Progress,
    BarColumn,
)
from rich.table import Table

app = typer.Typer(help="Check GitHub workflow status with Rich UI")
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

    def get_runtime(self) -> str:
        """Calculate the total runtime using current time or last update for completed runs."""
        start = datetime.strptime(self.created_at, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
        if self.status == "completed":
            end = datetime.strptime(self.updated_at, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc
            )
        else:
            end = datetime.now(timezone.utc)
        runtime = end - start
        total_seconds = runtime.total_seconds()
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
            raise typer.Exit(code=1)
        return WorkflowRun.from_json(data[0])
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error fetching workflow: {e}")
        raise typer.Exit(code=1)
    except json.JSONDecodeError as e:
        console.print(f"[red]Error parsing GitHub CLI output: {e}")
        raise typer.Exit(code=1)


def create_status_table(run: WorkflowRun) -> Table:
    """Create a Rich table displaying workflow run information."""
    table = Table(show_header=False, box=None)
    table.add_row("Status", f"[bold]{run.status}[/bold]")
    table.add_row("Conclusion", f"[bold]{run.conclusion or 'N/A'}[/bold]")
    table.add_row("Branch", f"[bold]{run.head_branch}[/bold]")
    table.add_row("Title", f"[bold]{run.display_title}[/bold]")
    table.add_row("Created", f"[bold]{run.created_at}[/bold]")
    table.add_row("Last Update", f"[bold]{run.updated_at}[/bold]")
    table.add_row("Total Runtime", f"[bold]{run.get_runtime()}[/bold]")
    return table


def watch_workflow(workflow_name: str, interval: int = 10) -> None:
    """Watch workflow progress with live updates."""
    update_interval = 0.5  # Update progress every 500ms

    while True:
        run = get_workflow_run(workflow_name)

        # Clear any previous output
        console.clear()

        # Show current status
        console.print(
            Panel(
                create_status_table(run),
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
                typer.sleep(update_interval)


@app.command()
def check(
    workflow_name: str = typer.Argument(..., help="Name of the workflow to check"),
    watch: bool = typer.Option(
        False,
        "--watch",
        "-w",
        help="Watch workflow progress until completion",
    ),
    interval: int = typer.Option(
        10,
        "--interval",
        "-i",
        help="Interval in seconds between status checks (only used with --watch)",
    ),
) -> None:
    """Check GitHub workflow status with Rich UI."""
    if watch:
        watch_workflow(workflow_name, interval)
    else:
        run = get_workflow_run(workflow_name)
        table = create_status_table(run)
        console.print(
            Panel(
                table,
                title=f"Workflow: {workflow_name}",
                border_style="blue",
            )
        )


if __name__ == "__main__":
    app()
