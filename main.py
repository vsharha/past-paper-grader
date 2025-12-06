from grader import discuss_feedback
from grader.generate_grade import generate_mark_scheme, generate_feedback
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown


def select_mode(console: Console) -> str:
    """Display mode selection menu and return selected mode."""
    console.print("\n")
    console.print(Panel.fit(
        "[bold cyan]Past Paper Grading System[/bold cyan]\n\n"
        "Select operation mode:",
        border_style="cyan"
    ))

    table = Table(show_header=True, header_style="bold magenta", border_style="dim")
    table.add_column("#", style="cyan", width=6)
    table.add_column("Mode", style="white")
    table.add_column("Description", style="dim")

    table.add_row("1", "Generate Mark Scheme", "Create marking criteria from a past paper")
    table.add_row("2", "Generate Feedback", "Grade student answers using mark scheme")
    table.add_row("3", "Discuss Feedback", "Interactive chat to discuss grading")

    console.print(table)
    console.print("\n[bold green]Enter mode (1-3):[/bold green] ", end="")

    choice = input().strip()

    mode_map = {
        "1": "mark_scheme",
        "2": "feedback",
        "3": "discuss"
    }

    return mode_map.get(choice, "")


def select_file(console: Console, directory: Path, title: str) -> Path | None:
    """Helper function to select a file from a directory."""
    files = sorted(list(directory.glob("**/*.pdf")))

    if not files:
        console.print(f"[red]No PDF files found in {directory} directory![/red]")
        return None

    console.print(f"\n[bold cyan]{title}[/bold cyan]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=6)
    table.add_column("File Path")

    for i, file in enumerate(files, 1):
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
        selected_paper = select_file(console, past_papers_dir, "Select Past Paper")
        if not selected_paper:
            return

        console.print(f"\n[green]Selected:[/green] {selected_paper.relative_to(past_papers_dir)}\n")

        with console.status("[bold cyan]Generating mark scheme..."):
            mark_scheme = generate_mark_scheme(
                provider="gemini",
                model="gemini-3-pro-preview",
                file=str(selected_paper),
                additional_instructions=follow_through_instructions
            )

        console.print("[bold green]✓ Mark scheme generated successfully![/bold green]\n")
        console.print("=" * 80)
        console.print(Markdown(mark_scheme))
        console.print("=" * 80)
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
        selected_paper = select_file(console, past_papers_dir, "Select Past Paper")
        if not selected_paper:
            return

        selected_solution = select_file(console, solutions_dir, "Select Student Solution")
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
                additional_instructions=follow_through_instructions
            )

        console.print("[bold green]✓ Feedback generated successfully![/bold green]\n")
        console.print("=" * 80)
        console.print(Markdown(feedback))
        console.print("=" * 80)
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
        selected_paper = select_file(console, past_papers_dir, "Select Past Paper")
        if not selected_paper:
            return

        selected_solution = select_file(console, solutions_dir, "Select Student Solution")
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
            additional_instructions=follow_through_instructions
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