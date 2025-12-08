from grader import discuss_feedback
from grader.generate_grade import (
    generate_mark_scheme,
    generate_feedback,
    has_mark_scheme,
    has_feedback,
)
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from concurrent.futures import ThreadPoolExecutor, as_completed


def select_mode(console: Console) -> str:
    """Display mode selection menu and return selected mode."""
    console.print("\n")
    console.print(
        Panel.fit(
            "[bold cyan]Past Paper Grading System[/bold cyan]\n\n"
            "Select operation mode:",
            border_style="cyan",
        )
    )

    table = Table(show_header=True, header_style="bold magenta", border_style="dim")
    table.add_column("#", style="cyan", width=6)
    table.add_column("Mode", style="white")
    table.add_column("Description", style="dim")

    table.add_row(
        "1", "Generate Mark Scheme", "Create marking criteria from a past paper"
    )
    table.add_row("2", "Generate Feedback", "Grade student answers using mark scheme")
    table.add_row("3", "Discuss Feedback", "Interactive chat to discuss grading")

    console.print(table)
    console.print("\n[bold green]Enter mode (1-3):[/bold green] ", end="")

    choice = input().strip()

    mode_map = {"1": "mark_scheme", "2": "feedback", "3": "discuss"}

    return mode_map.get(choice, "")


def select_file(
    console: Console, directory: Path, title: str, status_func=None
) -> Path | None:
    """Helper function to select a file from a directory."""
    files = sorted(list(directory.glob("**/*.pdf")))

    if not files:
        console.print(f"[red]No PDF files found in {directory} directory![/red]")
        return None

    console.print(f"\n[bold cyan]{title}[/bold cyan]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=6)
    table.add_column("File Path")
    if status_func:
        table.add_column("Status", style="green", width=8)

    for i, file in enumerate(files, 1):
        if status_func:
            status = "[green]✓[/green]" if status_func(file) else "[red]✗[/red]"
            table.add_row(str(i), str(file.relative_to(directory)), status)
        else:
            table.add_row(str(i), str(file.relative_to(directory)))

    console.print(table)
    console.print("\n[bold green]Enter number:[/bold green] ", end="")

    try:
        choice = int(input().strip())
        if choice < 1 or choice > len(files):
            console.print("[red]Invalid selection![/red]")
            return None
    except ValueError:
        console.print("[red]Invalid input![/red]")
        return None

    return files[choice - 1]


def select_multiple_files(
    console: Console, directory: Path, title: str, status_func=None
) -> list[Path] | None:
    """Helper function to select multiple files from a directory."""
    files = sorted(list(directory.glob("**/*.pdf")))

    if not files:
        console.print(f"[red]No PDF files found in {directory} directory![/red]")
        return None

    console.print(f"\n[bold cyan]{title}[/bold cyan]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=6)
    table.add_column("File Path")
    if status_func:
        table.add_column("Status", style="green", width=8)

    for i, file in enumerate(files, 1):
        if status_func:
            status = "[green]✓[/green]" if status_func(file) else "[red]✗[/red]"
            table.add_row(str(i), str(file.relative_to(directory)), status)
        else:
            table.add_row(str(i), str(file.relative_to(directory)))

    console.print(table)
    console.print("\n[bold green]Enter numbers (comma-separated, or 'all' for all files):[/bold green] ", end="")

    try:
        user_input = input().strip()

        if user_input.lower() == 'all':
            return files

        choices = [int(x.strip()) for x in user_input.split(',')]
        selected_files = []

        for choice in choices:
            if choice < 1 or choice > len(files):
                console.print(f"[red]Invalid selection: {choice}![/red]")
                return None
            selected_files.append(files[choice - 1])

        return selected_files
    except ValueError:
        console.print("[red]Invalid input![/red]")
        return None


def generate_mark_scheme_mode():
    """Mode for generating only a mark scheme."""
    console = Console()
    past_papers_dir = Path("past_papers")

    # Additional instructions for follow-through marks
    follow_through_instructions = """**Follow-Through Marking Policy:**

When creating the mark scheme, implement a follow-through marks (FT) policy for multi-step questions:

1. **Error Carried Forward (ECF)**: If a student makes an error in an early step but correctly applies subsequent methods using their incorrect answer, award follow-through marks for the method.

2. **Mark Allocation for Follow-Through**:
   - Clearly indicate which marks can be awarded as follow-through marks
   - Use notation like "FT" or "ECF" next to relevant mark allocations
   - Example: "2 marks for correct substitution (FT from part a)"

3. **Guidelines**:
   - Follow-through marks should only apply to method marks, not accuracy marks for final answers
   - If an earlier error makes subsequent parts trivial or impossible, do not award follow-through marks
   - Be explicit about when follow-through applies and when it doesn't
   - For calculation errors: award full method marks if the approach is correct

4. **Example Format**:
   ```
   Part (b) [4 marks]
   - 2 marks: Correct method for calculating X (FT from incorrect Y in part a)
   - 1 mark: Correct algebraic manipulation (FT)
   - 1 mark: Correct final answer (only if Y from part a was correct)
   ```

This ensures fair marking when students make early errors but demonstrate understanding of subsequent concepts."""

    try:
        # Ask user if they want to process single or multiple files
        console.print("\n[bold cyan]Generate mark schemes for:[/bold cyan]")
        console.print("  [dim]1[/dim] Single file")
        console.print("  [dim]2[/dim] Multiple files (parallel)")
        console.print("\n[bold green]Enter choice (1-2):[/bold green] ", end="")

        batch_choice = input().strip()

        if batch_choice == "2":
            # Multiple files - batch mode
            selected_papers = select_multiple_files(
                console, past_papers_dir, "Select Past Papers", status_func=has_mark_scheme
            )
            if not selected_papers:
                return

            console.print(f"\n[green]Selected {len(selected_papers)} file(s):[/green]")
            for paper in selected_papers:
                console.print(f"  • {paper.relative_to(past_papers_dir)}")
            console.print()

            # Generate mark schemes in parallel
            def generate_single_mark_scheme(paper_path):
                """Helper function to generate a single mark scheme."""
                try:
                    generate_mark_scheme(
                        provider="gemini",
                        model="gemini-3-pro-preview",
                        file=str(paper_path),
                        additional_instructions=follow_through_instructions,
                    )
                    return (paper_path, True, None)
                except Exception as e:
                    return (paper_path, False, str(e))

            # Use ThreadPoolExecutor for parallel generation
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console
            ) as progress:
                task = progress.add_task(
                    "[cyan]Generating mark schemes...",
                    total=len(selected_papers)
                )

                with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = {
                        executor.submit(generate_single_mark_scheme, paper): paper
                        for paper in selected_papers
                    }

                    successful = 0
                    failed = 0
                    errors = []

                    for future in as_completed(futures):
                        paper_path, success, error = future.result()
                        progress.update(task, advance=1)

                        if success:
                            successful += 1
                        else:
                            failed += 1
                            errors.append((paper_path, error))

            # Summary
            console.print(f"\n[bold green]✓ Completed![/bold green]")
            console.print(f"  Successful: [green]{successful}[/green]")
            if failed > 0:
                console.print(f"  Failed: [red]{failed}[/red]")
                console.print("\n[yellow]Errors:[/yellow]")
                for paper_path, error in errors:
                    console.print(f"  • {paper_path.name}: {error}")

        else:
            # Single file mode (original behavior)
            selected_paper = select_file(
                console, past_papers_dir, "Select Past Paper", status_func=has_mark_scheme
            )
            if not selected_paper:
                return

            console.print(
                f"\n[green]Selected:[/green] {selected_paper.relative_to(past_papers_dir)}\n"
            )

            with console.status("[bold cyan]Generating mark scheme..."):
                mark_scheme = generate_mark_scheme(
                    provider="gemini",
                    model="gemini-3-pro-preview",
                    file=str(selected_paper),
                    additional_instructions=follow_through_instructions,
                )

            console.print(
                "[bold green]✓ Mark scheme generated successfully![/bold green]\n"
            )

            # Create a panel with max width for centered display
            md_panel = Panel(
                Markdown(mark_scheme),
                title="[bold cyan]Mark Scheme[/bold cyan]",
                border_style="cyan",
                width=min(120, console.width),
                padding=(1, 2),
            )
            console.print(md_panel, justify="center")
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Mark scheme generation cancelled.[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error generating mark scheme: {e}[/red]")


def generate_feedback_mode():
    """Mode for generating feedback only."""
    console = Console()
    past_papers_dir = Path("past_papers")
    solutions_dir = Path("solutions")

    # Additional instructions for follow-through marks
    follow_through_instructions = """**Follow-Through Marking Policy:**

When grading student answers, apply a follow-through marks (FT) policy for multi-step questions:

1. **Error Carried Forward (ECF)**: If a student makes an error in an early step but correctly applies subsequent methods using their incorrect answer, award follow-through marks for the method.

2. **How to Apply Follow-Through**:
   - Check if the mark scheme indicates follow-through marks (FT or ECF notation)
   - Award method marks even if the numerical answer is wrong due to an earlier error
   - Clearly indicate in feedback when follow-through marks are awarded
   - Example: "✓ Correct method for integration (2 marks, FT from incorrect value in part a)"

3. **Guidelines**:
   - Follow-through marks apply to method marks, not accuracy marks for final answers
   - If an earlier error makes subsequent parts trivial, do not award follow-through marks
   - Be explicit in feedback about which marks were awarded as follow-through
   - Track errors through multi-part questions to apply FT consistently

4. **Feedback Format**:
   ```
   Part (b) - 3/4 marks
   ✓ Correct substitution method (2 marks, FT)
   ✓ Correct algebraic steps (1 mark, FT)
   ✗ Final answer incorrect due to error in part (a) (0/1 marks)

   Note: You earned follow-through marks for applying the correct method despite the earlier error.
   ```

This ensures fair grading and helps students understand they demonstrated method understanding even when making earlier mistakes."""

    try:
        selected_paper = select_file(
            console, past_papers_dir, "Select Past Paper", status_func=has_mark_scheme
        )
        if not selected_paper:
            return

        selected_solution = select_file(
            console,
            solutions_dir,
            "Select Student Solution",
            status_func=lambda f: has_feedback(selected_paper, f),
        )
        if not selected_solution:
            return

        console.print(f"\n[green]Selected:[/green]")
        console.print(f"  Paper: {selected_paper.relative_to(past_papers_dir)}")
        console.print(f"  Solution: {selected_solution.relative_to(solutions_dir)}\n")

        with console.status("[bold cyan]Generating feedback..."):
            feedback = generate_feedback(
                provider="gemini",
                model="gemini-3-pro-preview",
                paper_file=str(selected_paper),
                student_answers=str(selected_solution),
                additional_instructions=follow_through_instructions,
            )

        console.print("[bold green]✓ Feedback generated successfully![/bold green]\n")

        # Create a panel with max width for centered display
        feedback_panel = Panel(
            Markdown(feedback),
            title="[bold cyan]Student Feedback[/bold cyan]",
            border_style="cyan",
            width=min(120, console.width),
            padding=(1, 2),
        )
        console.print(feedback_panel, justify="center")
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Feedback generation cancelled.[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error generating feedback: {e}[/red]")


def select_and_discuss():
    """Mode for interactive feedback discussion."""
    console = Console()
    past_papers_dir = Path("past_papers")
    solutions_dir = Path("solutions")

    # Additional instructions for follow-through marks
    follow_through_instructions = """**Follow-Through Marking Policy:**

When grading student answers, apply a follow-through marks (FT) policy for multi-step questions:

1. **Error Carried Forward (ECF)**: If a student makes an error in an early step but correctly applies subsequent methods using their incorrect answer, award follow-through marks for the method.

2. **How to Apply Follow-Through**:
   - Check if the mark scheme indicates follow-through marks (FT or ECF notation)
   - Award method marks even if the numerical answer is wrong due to an earlier error
   - Clearly indicate in feedback when follow-through marks are awarded
   - Example: "✓ Correct method for integration (2 marks, FT from incorrect value in part a)"

3. **Guidelines**:
   - Follow-through marks apply to method marks, not accuracy marks for final answers
   - If an earlier error makes subsequent parts trivial, do not award follow-through marks
   - Be explicit in feedback about which marks were awarded as follow-through
   - Track errors through multi-part questions to apply FT consistently

4. **Feedback Format**:
   ```
   Part (b) - 3/4 marks
   ✓ Correct substitution method (2 marks, FT)
   ✓ Correct algebraic steps (1 mark, FT)
   ✗ Final answer incorrect due to error in part (a) (0/1 marks)

   Note: You earned follow-through marks for applying the correct method despite the earlier error.
   ```

This ensures fair grading and helps students understand they demonstrated method understanding even when making earlier mistakes."""

    try:
        selected_paper = select_file(
            console, past_papers_dir, "Select Past Paper", status_func=has_mark_scheme
        )
        if not selected_paper:
            return

        selected_solution = select_file(
            console,
            solutions_dir,
            "Select Student Solution",
            status_func=lambda f: has_feedback(selected_paper, f),
        )
        if not selected_solution:
            return

        console.print(f"\n[green]Selected:[/green]")
        console.print(f"  Paper: {selected_paper.relative_to(past_papers_dir)}")
        console.print(f"  Solution: {selected_solution.relative_to(solutions_dir)}\n")

        discuss_feedback(
            provider="gemini",
            model="gemini-2.5-flash",
            paper_file=str(selected_paper),
            student_answers=str(selected_solution),
            feedback_provider="gemini",
            feedback_model="gemini-3-pro-preview",
            additional_instructions=follow_through_instructions,
        )
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Discussion cancelled.[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error during discussion: {e}[/red]")

def main():
    """Main entry point for the grading system."""
    console = Console()

    try:
        mode = select_mode(console)

        if mode == "mark_scheme":
            generate_mark_scheme_mode()
        elif mode == "feedback":
            generate_feedback_mode()
        elif mode == "discuss":
            select_and_discuss()
        else:
            console.print("[red]Invalid mode selection![/red]")
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Operation cancelled by user. Goodbye![/yellow]")
    except Exception as e:
        console.print(f"\n[red]Unexpected error: {e}[/red]")


if __name__ == "__main__":
    main()
