"""
Command-line interface for running tests with PyDesktop Test.

This module provides a command-line interface for discovering and running tests,
with options for reporting and configuration.
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import typer
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    HAS_TYPER = True
except ImportError:
    HAS_TYPER = False
    # Fall back to argparse if typer is not available
    import argparse

from .core import run_tests, collect_tests
from .config import TestConfig
from .reporting import TestReportGenerator
from .dashboard import launch_dashboard


def main_cli():
    """
    Main entry point for the command-line interface.
    """
    if HAS_TYPER:
        _typer_cli()
    else:
        _argparse_cli()


def _typer_cli():
    """
    Command-line interface implementation using Typer.
    """
    app = typer.Typer(
        name="pydesktop-test",
        help="Test runner for Python desktop applications",
        add_completion=False
    )
    console = Console()
    
    @app.command("run")
    def run_cmd(
        test_paths: List[str] = typer.Argument(
            None, 
            help="Paths to test files or directories"
        ),
        report_dir: str = typer.Option(
            "test_reports", 
            "--report-dir", "-r", 
            help="Directory to store test reports"
        ),
        html: bool = typer.Option(
            True, 
            "--html/--no-html", 
            help="Generate HTML report"
        ),
        coverage: bool = typer.Option(
            True, 
            "--coverage/--no-coverage", 
            help="Generate coverage report"
        ),
        verbose: bool = typer.Option(
            True, 
            "--verbose/--quiet", "-v/-q", 
            help="Verbose output"
        ),
        markers: Optional[List[str]] = typer.Option(
            None, 
            "--marker", "-m", 
            help="Run tests with specific markers"
        ),
        parallel: bool = typer.Option(
            False, 
            "--parallel/--sequential", "-p/-s", 
            help="Run tests in parallel"
        ),
        workers: Optional[int] = typer.Option(
            None, 
            "--workers", "-w", 
            help="Number of parallel workers"
        ),
        config_file: Optional[str] = typer.Option(
            None, 
            "--config", "-c", 
            help="Path to configuration file"
        )
    ):
        """Run tests in the specified paths"""
        # Default to current directory if no paths provided
        if not test_paths:
            test_paths = ["tests"]
        
        # Load configuration if specified
        config = TestConfig()
        if config_file:
            try:
                config.load_from_file(config_file)
                console.print(f"[green]Loaded configuration from [bold]{config_file}[/bold][/green]")
            except Exception as e:
                console.print(f"[red]Error loading configuration: {str(e)}[/red]")
                raise typer.Exit(code=1)
        
        # Update config with CLI options
        config.update({
            "report_dir": report_dir,
            "generate_html": html,
            "generate_coverage": coverage,
            "verbose": verbose,
            "parallel": parallel,
            "workers": workers
        })
        
        # Create progress spinner
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Running tests..."),
            transient=True
        ) as progress:
            progress.add_task("run")
            
            # Run tests with configuration
            start_time = time.time()
            result = run_tests(
                test_paths=test_paths,
                config=config,
                markers=markers,
                capture_output=not verbose,
                generate_html=html,
                generate_coverage=coverage,
                verbose=verbose,
                parallel=parallel,
                max_workers=workers
            )
            duration = time.time() - start_time
        
        # Show results
        success = result.get("success", False)
        color = "green" if success else "red"
        status = "PASSED" if success else "FAILED"
        
        console.print(Panel.fit(
            f"[bold {color}]{status}[/bold {color}]",
            title="Test Run Complete", 
            subtitle=f"Duration: {duration:.2f} seconds"
        ))
        
        # Show report paths
        if html and "html_report" in result:
            console.print(f"[blue]HTML report:[/blue] [yellow]{result['html_report']}[/yellow]")
        
        if coverage and "coverage_report" in result:
            console.print(f"[blue]Coverage report:[/blue] [yellow]{result['coverage_report']}[/yellow]")
        
        # Exit with appropriate code
        if not success:
            raise typer.Exit(code=1)
    
    @app.command("dashboard")
    def dashboard_cmd(
        data_dir: str = typer.Option(
            "test_reports",
            "--data-dir", "-d",
            help="Directory containing test reports"
        ),
        port: int = typer.Option(
            5500,
            "--port", "-p",
            help="Port to run dashboard on"
        ),
        open_browser: bool = typer.Option(
            True,
            "--open/--no-open",
            help="Automatically open browser"
        )
    ):
        """Launch the interactive test dashboard"""
        console.print(Panel.fit(
            "Launching interactive dashboard",
            title="PyDesktop Test Dashboard"
        ))
        
        # Launch the dashboard
        dashboard = launch_dashboard(
            port=port,
            data_dir=data_dir,
            open_browser=open_browser
        )
        
        # Show info
        console.print(f"[green]Dashboard running at:[/green] [bold blue]http://localhost:{port}[/bold blue]")
        console.print(f"[green]Loading reports from:[/green] [yellow]{data_dir}[/yellow]")
        console.print("\nPress Ctrl+C to stop the dashboard")
        
        # Keep the process running until interrupted
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("\n[yellow]Dashboard stopped[/yellow]")
    
    @app.command("list")
    def list_cmd(
        test_paths: List[str] = typer.Argument(
            None, 
            help="Paths to test files or directories"
        ),
        markers: Optional[List[str]] = typer.Option(
            None, 
            "--marker", "-m", 
            help="Filter tests by markers"
        ),
        json_output: bool = typer.Option(
            False, 
            "--json", 
            help="Output as JSON"
        ),
        config_file: Optional[str] = typer.Option(
            None, 
            "--config", "-c", 
            help="Path to configuration file"
        )
    ):
        """List available tests without running them"""
        # Default to current directory if no paths provided
        if not test_paths:
            test_paths = ["tests"]
        
        # Load configuration if specified
        config = TestConfig()
        if config_file:
            try:
                config.load_from_file(config_file)
            except Exception as e:
                console.print(f"[red]Error loading configuration: {str(e)}[/red]")
                raise typer.Exit(code=1)
        
        # Collect tests
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Collecting tests..."),
            transient=True
        ) as progress:
            progress.add_task("collect")
            collected_tests = collect_tests(test_paths, config, markers)
        
        # Output results
        if json_output:
            # JSON output
            print(json.dumps(collected_tests, indent=2))
        else:
            # Pretty output with rich
            if not collected_tests:
                console.print("[yellow]No tests found[/yellow]")
                return
            
            console.print(f"[green]Found [bold]{len(collected_tests)}[/bold] tests:[/green]")
            
            # Group by module
            tests_by_module = {}
            for test in collected_tests:
                module = test.get("module", "unknown")
                if module not in tests_by_module:
                    tests_by_module[module] = []
                tests_by_module[module].append(test)
            
            # Print grouped tests
            for module, tests in tests_by_module.items():
                console.print(f"[blue][bold]{module}[/bold][/blue]")
                for test in tests:
                    marker_str = ""
                    if test.get("markers"):
                        marker_str = f" [cyan]({', '.join(test['markers'])})[/cyan]"
                    console.print(f"  [yellow]{test['name']}[/yellow]{marker_str}")
    
    # Run the CLI
    app()


def _argparse_cli():
    """
    Command-line interface implementation using argparse (fallback).
    """
    parser = argparse.ArgumentParser(description="Test runner for Python desktop applications")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run tests")
    run_parser.add_argument("test_paths", nargs="*", help="Paths to test files or directories")
    run_parser.add_argument("--report-dir", "-r", default="test_reports", help="Directory to store test reports")
    run_parser.add_argument("--no-html", action="store_true", help="Disable HTML report generation")
    run_parser.add_argument("--no-coverage", action="store_true", help="Disable coverage report generation")
    run_parser.add_argument("--quiet", "-q", action="store_true", help="Quiet output")
    run_parser.add_argument("--marker", "-m", action="append", help="Run tests with specific markers")
    run_parser.add_argument("--parallel", "-p", action="store_true", help="Run tests in parallel")
    run_parser.add_argument("--workers", "-w", type=int, help="Number of parallel workers")
    run_parser.add_argument("--config", "-c", help="Path to configuration file")
    
    # Dashboard command
    dashboard_parser = subparsers.add_parser("dashboard", help="Launch the interactive test dashboard")
    dashboard_parser.add_argument("--data-dir", "-d", default="test_reports", help="Directory containing test reports")
    dashboard_parser.add_argument("--port", "-p", type=int, default=5500, help="Port to run dashboard on")
    dashboard_parser.add_argument("--no-open", action="store_true", help="Don't automatically open browser")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List available tests")
    list_parser.add_argument("test_paths", nargs="*", help="Paths to test files or directories")
    list_parser.add_argument("--marker", "-m", action="append", help="Filter tests by markers")
    list_parser.add_argument("--json", action="store_true", help="Output as JSON")
    list_parser.add_argument("--config", "-c", help="Path to configuration file")
    
    args = parser.parse_args()
    
    if args.command == "run":
        # Default to current directory if no paths provided
        test_paths = args.test_paths or ["tests"]
        
        # Load configuration if specified
        config = TestConfig()
        if args.config:
            try:
                config.load_from_file(args.config)
                print(f"Loaded configuration from {args.config}")
            except Exception as e:
                print(f"Error loading configuration: {str(e)}")
                sys.exit(1)
        
        # Update config with CLI options
        config.update({
            "report_dir": args.report_dir,
            "generate_html": not args.no_html,
            "generate_coverage": not args.no_coverage,
            "verbose": not args.quiet,
            "parallel": args.parallel,
            "workers": args.workers
        })
        
        # Run tests with configuration
        print("Running tests...")
        start_time = time.time()
        result = run_tests(
            test_paths=test_paths,
            config=config,
            markers=args.marker,
            capture_output=args.quiet,
            generate_html=not args.no_html,
            generate_coverage=not args.no_coverage,
            verbose=not args.quiet,
            parallel=args.parallel,
            max_workers=args.workers
        )
        duration = time.time() - start_time
        
        # Show results
        success = result.get("success", False)
        status = "PASSED" if success else "FAILED"
        
        print(f"\nTest Run Complete - {status}")
        print(f"Duration: {duration:.2f} seconds")
        
        # Show report paths
        if not args.no_html and "html_report" in result:
            print(f"HTML report: {result['html_report']}")
        
        if not args.no_coverage and "coverage_report" in result:
            print(f"Coverage report: {result['coverage_report']}")
        
        # Exit with appropriate code
        if not success:
            sys.exit(1)
    
    elif args.command == "list":
        # Default to current directory if no paths provided
        test_paths = args.test_paths or ["tests"]
        
        # Load configuration if specified
        config = TestConfig()
        if args.config:
            try:
                config.load_from_file(args.config)
            except Exception as e:
                print(f"Error loading configuration: {str(e)}")
                sys.exit(1)
        
        # Collect tests
        print("Collecting tests...")
        collected_tests = collect_tests(test_paths, config, args.marker)
        
        # Output results
        if args.json:
            # JSON output
            print(json.dumps(collected_tests, indent=2))
        else:
            # Simple output
            if not collected_tests:
                print("No tests found")
                return
            
            print(f"Found {len(collected_tests)} tests:")
            
            # Group by module
            tests_by_module = {}
            for test in collected_tests:
                module = test.get("module", "unknown")
                if module not in tests_by_module:
                    tests_by_module[module] = []
                tests_by_module[module].append(test)
            
            # Print grouped tests
            for module, tests in tests_by_module.items():
                print(f"\n{module}")
                for test in tests:
                    marker_str = ""
                    if test.get("markers"):
                        marker_str = f" ({', '.join(test['markers'])})"
                    print(f"  {test['name']}{marker_str}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main_cli()
