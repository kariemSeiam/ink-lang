"""
CLI entry point for the ink command.
Provides validate, compile, viz, debug, and repl subcommands.
"""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.tree import Tree

console = Console()


def _version():
    from ink import __version__
    return __version__


# ─── Main Group ───────────────────────────────────────────────────────────────

@click.group()
@click.version_option(version=_version(), prog_name="ink-lang")
def main():
    """🐙 INK — The Intelligence Notation for Kinetics.

    A language for specifying how intelligence feels, not what it does.
    """
    pass


# ─── Validate ─────────────────────────────────────────────────────────────────

@main.command()
@click.argument("files", nargs=-1, type=click.Path(exists=True))
@click.option("--all", "all_dir", type=click.Path(exists=True), help="Validate all .ink files in directory")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed results")
def validate(files, all_dir, verbose):
    """Validate .ink files against the specification."""
    from ink.parser import InkParser
    from ink.validator import InkValidator

    parser = InkParser()
    validator = InkValidator()

    # Collect files
    ink_files = list(files)
    if all_dir:
        ink_files.extend(str(p) for p in Path(all_dir).rglob("*.ink"))

    if not ink_files:
        console.print("[yellow]No .ink files specified.[/yellow]")
        return

    total = 0
    passed = 0
    failed = 0

    for filepath in ink_files:
        total += 1
        filepath = str(filepath)

        try:
            ast = parser.parse_file(filepath)
            result = validator.validate(ast)

            if result.valid:
                passed += 1
                console.print(f"[green]✓[/green] {filepath}")
                if verbose:
                    _print_ast_summary(ast)
            else:
                failed += 1
                console.print(f"[red]✗[/red] {filepath}")
                for issue in result.errors:
                    loc = f" (line {issue.line})" if issue.line else ""
                    console.print(f"  [red]Rule {issue.rule}:[/red] {issue.message}{loc}")
                if verbose:
                    for issue in result.warnings:
                        loc = f" (line {issue.line})" if issue.line else ""
                        console.print(f"  [yellow]Rule {issue.rule}:[/yellow] {issue.message}{loc}")

        except Exception as e:
            failed += 1
            console.print(f"[red]✗[/red] {filepath}")
            console.print(f"  [red]Parse error:[/red] {e}")

    console.print()
    if failed == 0:
        console.print(f"[green]All {total} files valid ✓[/green]")
    else:
        console.print(f"[red]{failed}/{total} files failed validation[/red]")
        sys.exit(1)


def _print_ast_summary(ast):
    """Print a summary of the parsed AST."""
    tree = Tree(f"📄 [bold]{ast.header.system or 'INK File'}[/bold] v{ast.header.version}")
    tree.label += f" — {len(ast.minds)} mind(s)"

    for name, mind in ast.minds.items():
        mind_branch = tree.add(f"🧠 [cyan]{name}[/cyan]")
        mind_branch.add(f"Sensations: {len(mind.sensations)}")
        mind_branch.add(f"Triggers: {len(mind.triggers)}")
        mind_branch.add(f"States: {len(mind.states)}")
        mind_branch.add(f"Questions: {len(mind.questions)}")
        if mind.overrun:
            mind_branch.add("[yellow]Overrun: yes[/yellow]")
        if mind.crystallization:
            mind_branch.add("[yellow]Crystallization: yes[/yellow]")

    if ast.pressure_field:
        pf_branch = tree.add("⚡ [magenta]Pressure Field[/magenta]")
        for axis in ast.pressure_field.axes:
            vec = ", ".join(f"{v:+.1f}" for v in axis.vector)
            pf_branch.add(f"@{axis.mind_name} [{vec}]")

    console.print(tree)


# ─── Compile ──────────────────────────────────────────────────────────────────

@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--target", "-t", type=click.Choice(["openai", "anthropic", "generic", "json"]), default="generic")
@click.option("--mind", "-m", default=None, help="Compile only a specific mind")
@click.option("--output", "-o", type=click.Path(), default=None, help="Output file path")
def compile(file, target, mind, output):
    """Compile .ink file to a system prompt."""
    from ink.parser import InkParser
    from ink.compiler import InkCompiler

    parser = InkParser()
    compiler = InkCompiler()

    try:
        ast = parser.parse_file(file)
        result = compiler.compile(ast, target=target, mind_name=mind)

        if output:
            Path(output).write_text(result, encoding="utf-8")
            console.print(f"[green]✓[/green] Compiled to {output} ({target})")
        else:
            console.print(Panel(result, title=f"Compiled: {target}", border_style="cyan"))

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


# ─── Visualize ────────────────────────────────────────────────────────────────

@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--type", "viz_type", type=click.Choice(["graph", "interaction", "pressure-field"]), default="graph")
@click.option("--output", "-o", type=click.Path(), default=None, help="Output file (Mermaid .mmd)")
def viz(file, viz_type, output):
    """Visualize .ink file structure."""
    from ink.parser import InkParser
    from ink.visualizer import InkVisualizer

    parser = InkParser()
    visualizer = InkVisualizer()

    try:
        ast = parser.parse_file(file)

        if viz_type == "graph":
            result = visualizer.mind_graph(ast)
        elif viz_type == "interaction":
            result = visualizer.interaction_diagram(ast)
        elif viz_type == "pressure-field":
            result = visualizer.pressure_field_diagram(ast)
        else:
            result = visualizer.mind_graph(ast)

        if output:
            Path(output).write_text(result, encoding="utf-8")
            console.print(f"[green]✓[/green] Diagram saved to {output}")
        else:
            console.print(Panel(result, title=f"Diagram: {viz_type}", border_style="magenta"))

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


# ─── Debug ────────────────────────────────────────────────────────────────────

@main.command()
@click.argument("file", type=click.Path(exists=True))
def debug(file):
    """Show parsed AST for debugging."""
    from ink.parser import InkParser

    parser = InkParser()

    try:
        ast = parser.parse_file(file)

        console.print(Panel(f"[bold]{ast.header.system or 'INK File'}[/bold] v{ast.header.version}"))
        console.print(f"Minds: {list(ast.minds.keys())}")

        for name, mind in ast.minds.items():
            console.print(f"\n[bold cyan]@MIND:{name}[/bold cyan]")

            for s_name, s in mind.sensations.items():
                console.print(f"  SENSATION:{s_name}")
                console.print(f"    FEELS_LIKE: \"{s.feels_like}\"")
                console.print(f"    COMPLETION_SIGNAL: \"{s.completion_signal}\"")

            for t_name, t in mind.triggers.items():
                console.print(f"  TRIGGER:{t_name}")
                console.print(f"    WHEN: {t.when}")
                console.print(f"    ACTIVATES: {t.activates}")
                console.print(f"    FALSE_POSITIVE_CHECK: {t.false_positive_check}")

            if mind.satisfaction:
                console.print(f"  SATISFACTION:")
                for req in mind.satisfaction.requires:
                    console.print(f"    REQUIRES: {req}")
                console.print(f"    HALT_ON_INCOMPLETE: {mind.satisfaction.halt_on_incomplete}")

            if mind.overrun:
                console.print(f"  OVERRUN:")
                console.print(f"    DETECTION: {mind.overrun.detection}")
                console.print(f"    CORRECTION: {mind.overrun.correction_action}({mind.overrun.correction_reason})")

            if mind.crystallization:
                console.print(f"  CRYSTALLIZATION:")
                console.print(f"    WARNING: {mind.crystallization.warning}")
                console.print(f"    THRESHOLD: {mind.crystallization.threshold}")
                console.print(f"    ACTION: {mind.crystallization.action}")

            for st_name, st in mind.states.items():
                console.print(f"  STATE:{st_name} = {st.default}")
                for tr in st.transitions:
                    console.print(f"    -> {tr.target} WHEN {tr.condition}")

            for q_name, q in mind.questions.items():
                console.print(f"  QUESTION:{q_name}")
                console.print(f"    EVALUATES: {q.evaluates}")
                console.print(f"    SATISFACTION_CONDITION: {q.satisfaction_condition}")

        if ast.pressure_field:
            console.print(f"\n[bold magenta]@PRESSURE_FIELD[/bold magenta]")
            for axis in ast.pressure_field.axes:
                vec = ", ".join(f"{v:+.1f}" for v in axis.vector)
                console.print(f"  @{axis.mind_name} AXIS: [{vec}]")
            console.print(f"  DISSENT_THRESHOLD: {ast.pressure_field.dissent_threshold}")
            console.print(f"  MAGNITUDE_THRESHOLD: {ast.pressure_field.magnitude_threshold}")

        if ast.collapse:
            console.print(f"\n[bold yellow]@COLLAPSE[/bold yellow]")
            console.print(f"  METHOD: {ast.collapse.method}")
            console.print(f"  THRESHOLD: {ast.collapse.threshold}")

    except Exception as e:
        console.print(f"[red]Parse error:[/red] {e}")
        sys.exit(1)


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    main()
