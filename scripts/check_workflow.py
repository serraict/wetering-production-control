#!/usr/bin/env python3
"""Rich-based GitHub workflow status checker.

A Python implementation of the check_workflow.sh script using Rich for improved UI.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict

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

# Field mapping from GitHub CLI to display labels
FIELDS = [
    ("databaseId", "Run ID"),
    ("status", "Status"),
    ("conclusion", "Conclusion"),
    ("headBranch", "Branch"),
    ("displayTitle", "Title"),
    ("createdAt", "Created"),
    ("updatedAt", "Last Update"),
]


def calculate_runtime(created_at: str, updated_at: str, is_completed: bool) -> str:
    """Calculate runtime from timestamps."""
    start = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    if is_completed:
        end = datetime.strptime(updated_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    else:
        end = datetime.now(timezone.utc)
    runtime = end - start
    total_seconds = runtime.total_seconds()
    minutes, seconds = divmod(int(total_seconds), 60)
    return f"{minutes}m {seconds}s"


def get_workflow_run(workflow_name: str) -> Dict[str, Any]:
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
                ",".join(field for field, _ in FIELDS),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(result.stdout)
        if not data:
            console.print(f"[red]No runs found for workflow: {workflow_name}")
            raise typer.Exit(code=1)
        return data[0]
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error fetching workflow: {e}")
        raise typer.Exit(code=1)
    except json.JSONDecodeError as e:
        console.print(f"[red]Error parsing GitHub CLI output: {e}")
        raise typer.Exit(code=1)


def get_workflow_jobs(run_id: str) -> list[Dict[str, Any]]:
    """Fetch job information for a workflow run."""
    try:
        result = subprocess.run(
            [
                "gh",
                "run",
                "view",
                run_id,
                "--json",
                "jobs",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(result.stdout)
        return data.get("jobs", [])
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error fetching jobs: {e}")
        return []
    except json.JSONDecodeError as e:
        console.print(f"[red]Error parsing job data: {e}")
        return []


def create_status_table(
    run: Dict[str, Any], runtime: str | None = None, jobs: list[Dict[str, Any]] | None = None
) -> Table:
    """Create a Rich table displaying workflow run information."""
    table = Table(show_header=False, box=None)

    # Add standard fields
    for gh_field, display_label in FIELDS:
        value = run.get(gh_field, "N/A")
        table.add_row(display_label, f"[bold]{value}[/bold]")

    # Add runtime
    if runtime is None:
        is_completed = run["status"] == "completed"
        runtime = calculate_runtime(run["createdAt"], run["updatedAt"], is_completed)
    table.add_row("Total Runtime", f"[bold]{runtime}[/bold]")

    # Add job information if available
    if jobs:
        table.add_row("", "")  # Empty row for spacing
        table.add_row("[bold]Jobs:", "")
        for job in jobs:
            job_name = job.get("name", "Unknown")
            job_id = job.get("databaseId", "N/A")
            job_status = job.get("status", "unknown")
            job_conclusion = job.get("conclusion", "N/A")

            # Color-code the status
            if job_status == "completed":
                if job_conclusion == "success":
                    status_display = "[green]✓ completed (success)[/green]"
                elif job_conclusion == "failure":
                    status_display = "[red]✗ completed (failure)[/red]"
                else:
                    status_display = f"[yellow]completed ({job_conclusion})[/yellow]"
            elif job_status == "in_progress":
                status_display = "[blue]⚙ in progress[/blue]"
            else:
                status_display = f"[dim]{job_status}[/dim]"

            table.add_row(f"  • {job_name}", f"ID: {job_id} | {status_display}")

    return table


def display_status(workflow_name: str, run: Dict[str, Any], runtime: str | None = None) -> None:
    """Display current workflow status."""
    console.clear()

    # Fetch job information
    run_id = str(run.get("databaseId", ""))
    jobs = get_workflow_jobs(run_id) if run_id else []

    console.print(
        Panel(
            create_status_table(run, runtime, jobs),
            title=f"Workflow: {workflow_name}",
            border_style="blue",
        )
    )

    # Show troubleshooting tip for failed workflows
    if run.get("status") == "completed" and run.get("conclusion") == "failure":
        console.print()
        console.print("[dim]💡 Troubleshooting tip:[/dim]")
        console.print(
            f"[dim]   Get detailed logs: [bold]gh run view {run_id} --log-failed[/bold][/dim]"
        )
        if jobs:
            failed_jobs = [job for job in jobs if job.get("conclusion") == "failure"]
            if failed_jobs:
                for job in failed_jobs:
                    job_id = job.get("databaseId")
                    console.print(
                        f"[dim]   Job-specific logs: [bold]gh run view {job_id} --log-failed[/bold][/dim]"
                    )


def watch_workflow(workflow_name: str, interval: int = 10) -> None:
    """Watch workflow progress with live updates."""
    update_interval = 5

    while True:
        run = get_workflow_run(workflow_name)
        is_completed = run["status"] == "completed"

        if is_completed:
            display_status(workflow_name, run)
            conclusion = run["conclusion"]
            conclusion_color = "green" if conclusion == "success" else "red"
            console.print(
                f"\nWorkflow completed with conclusion: [{conclusion_color}]{conclusion}[/]"
            )
            # Exit with non-zero status if workflow failed
            if conclusion != "success":
                sys.exit(1)
            break

        # Show countdown progress with live runtime updates
        with Progress(
            BarColumn(),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("", total=interval)
            steps = int(interval / update_interval)
            for step in range(steps):
                # Calculate current runtime
                runtime = calculate_runtime(run["createdAt"], run["updatedAt"], False)

                # Update display
                display_status(workflow_name, run, runtime)

                # Update progress bar
                progress.update(task, completed=interval - (step * update_interval))
                time.sleep(update_interval)


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
        display_status(workflow_name, run)
        # Exit with non-zero status if workflow failed
        if run["status"] == "completed" and run["conclusion"] != "success":
            sys.exit(1)


if __name__ == "__main__":
    app()
