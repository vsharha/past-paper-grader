from grader import discuss_feedback
from pathlib import Path
from rich.console import Console
from rich.table import Table


def select_and_discuss():
    console = Console()

    past_papers_dir = Path("past_papers")
    solutions_dir = Path("solutions")

    past_papers = sorted(list(past_papers_dir.glob("*.pdf")))
    solutions = sorted(list(solutions_dir.glob("*.pdf")))

    if not past_papers:
        console.print("[red]No PDF files found in past_papers directory![/red]")
        return

    if not solutions:
        console.print("[red]No PDF files found in solutions directory![/red]")
        return

    console.print("\n[bold cyan]Select Past Paper[/bold cyan]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=6)
    table.add_column("File Name")

    for i, paper in enumerate(past_papers, 1):
        table.add_row(str(i), paper.name)

    console.print(table)
    console.print("\n[bold green]Enter number:[/bold green] ", end="")
    paper_choice = int(input().strip())

    if paper_choice < 1 or paper_choice > len(past_papers):
        console.print("[red]Invalid selection![/red]")
        return

    selected_paper = past_papers[paper_choice - 1]

    console.print("\n[bold cyan]Select Student Solution[/bold cyan]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=6)
    table.add_column("File Name")

    for i, solution in enumerate(solutions, 1):
        table.add_row(str(i), solution.name)

    console.print(table)
    console.print("\n[bold green]Enter number:[/bold green] ", end="")
    solution_choice = int(input().strip())

    if solution_choice < 1 or solution_choice > len(solutions):
        console.print("[red]Invalid selection![/red]")
        return

    selected_solution = solutions[solution_choice - 1]

    console.print(f"\n[green]Selected:[/green]")
    console.print(f"  Paper: {selected_paper.name}")
    console.print(f"  Solution: {selected_solution.name}\n")

    discuss_feedback(
        provider="gemini",
        model="gemini-2.5-flash",
        paper_file=str(selected_paper),
        student_answers=str(selected_solution),
        feedback_provider="gemini",
        feedback_model="gemini-3-pro-preview"
    )


if __name__ == "__main__":
    select_and_discuss()