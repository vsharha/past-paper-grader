from litellm_utils import Conversation
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live
from rich.spinner import Spinner
from .generate_grade import generate_feedback, _get_relative_structure
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.styles import Style


def stream_markdown(stream_iterator, console: Console) -> str:
    accumulated_text = ""
    first_chunk = True

    with Live(Spinner("dots", text="[dim]Thinking...[/dim]"), console=console, refresh_per_second=10) as live:
        for chunk in stream_iterator:
            accumulated_text += chunk

            # Replace spinner with markdown after first chunk
            if first_chunk:
                first_chunk = False

            live.update(Markdown(accumulated_text))

    return accumulated_text


def discuss_feedback(
    provider: str,
    model: str,
    paper_file: str | Path,
    student_answers: str | Path,
    feedback_provider: str | None = None,
    feedback_model: str | None = None,
    additional_instructions: str = ""
) -> None:
    if feedback_provider is None:
        feedback_provider = provider
    if feedback_model is None:
        feedback_model = model
    console = Console()

    # Convert to Path objects
    paper_path = Path(paper_file)
    student_path = Path(student_answers)

    feedback_dir = Path("feedback")

    paper_parent, paper_stem = _get_relative_structure(paper_path)
    student_parent, student_stem = _get_relative_structure(student_path)

    if paper_parent != Path('.'):
        feedback_subdir = feedback_dir / paper_parent
        output_filename = f"{paper_stem}_feedback_{student_stem}.md"
        feedback_path = feedback_subdir / output_filename
    else:
        output_filename = f"{paper_stem}_feedback_{student_stem}.md"
        feedback_path = feedback_dir / output_filename

    if not feedback_path.exists():
        console.print(f"[yellow]Feedback not found. Generating feedback for {paper_path.name}...[/yellow]")
        generate_feedback(feedback_provider, feedback_model, paper_file, student_answers, additional_instructions=additional_instructions)
        console.print("[green]Feedback generated successfully![/green]\n")

    try:
        feedback_content = feedback_path.read_text()
    except Exception as e:
        console.print(f"[red]Error reading feedback file: {e}[/red]")
        return

    system_prompt = """You are an expert academic advisor for undergraduate Computer Science and Mathematics courses.

You are helping a student understand and discuss their exam feedback. You have access to:
1. The graded feedback with marks and comments
2. The original exam paper with all questions
3. The student's submitted answers

Your role:
- Explain grading decisions clearly and fairly
- Answer questions about why marks were awarded or deducted
- Provide specific examples from their answers
- Suggest concrete study strategies for improvement
- Discuss alternative solution approaches
- Reference specific questions and marking criteria
- Be encouraging while being honest about areas needing work

Guidelines:
- Quote specific parts of their answers when discussing
- Reference question numbers and parts clearly
- Explain marking criteria from the mark scheme
- Provide actionable advice, not just generic encouragement
- If they ask "why did I lose marks on Q2?", give specific reasons
- Use markdown formatting for clarity (code blocks, lists, etc.)

Be constructive, supportive, and educational."""

    conversation = Conversation(
        provider=provider,
        model=model,
        system_prompt=system_prompt,
        temperature=0.3
    )

    console.print("[cyan]Loading feedback and context files...[/cyan]")
    initial_message = f"""I have received feedback on my exam. I'd like to discuss it with you.

Here is my feedback:

{feedback_content}

I also have access to the original exam paper and my answers for reference."""

    try:
        console.print("\n[bold green]Feedback Discussion Started![/bold green]")
        console.print("\n[dim]Commands: 'quit'/'exit' to end, 'history' to view chat, 'clear' to reset, 'feedback' to re-display feedback[/dim]")
        console.print("=" * 60)
        console.print("\n[bold cyan]Assistant:[/bold cyan]")

        stream_markdown(
            conversation.stream(
                user_text=initial_message,
                file=[paper_path, student_path]
            ),
            console
        )
        print()  # Add newline after response
    except Exception as e:
        console.print(f"\n[red]Error initializing conversation: {e}[/red]")
        return

    input_history = InMemoryHistory()

    while True:
        try:
            # Get user input with arrow key support
            console.print("\n[bold green]You:[/bold green] ")
            user_input = prompt(
                "",
                history=input_history,
                multiline=False,
                vi_mode=False
            ).strip()

            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit']:
                console.print("\n[yellow]Ending conversation. Good luck with your studies![/yellow]")
                break

            if user_input.lower() == 'history':
                history = conversation.get_history()
                console.print("\n[bold cyan]--- Conversation History ---[/bold cyan]")
                for i, msg in enumerate(history, 1):
                    role = msg['role'].upper()
                    console.print(f"\n[bold]{i}. {role}:[/bold]")
                    content = msg.get('content')

                    # Handle different content types
                    if isinstance(content, str):
                        console.print(content)
                    elif isinstance(content, list):
                        # Extract only text parts, skip file data
                        for part in content:
                            if isinstance(part, dict):
                                if part.get('type') == 'text':
                                    console.print(part.get('text', ''))
                                elif part.get('type') == 'image_url':
                                    console.print("[dim][File: Image attached][/dim]")
                                else:
                                    console.print(f"[dim][File attached][/dim]")
                            elif isinstance(part, str):
                                console.print(part)
                    else:
                        console.print(str(content))
                console.print("\n[bold cyan]--- End of History ---[/bold cyan]")
                continue

            if user_input.lower() == 'clear':
                conversation.clear_history()
                console.print("[yellow]Conversation history cleared. System prompt retained.[/yellow]")
                continue

            if user_input.lower() == 'feedback':
                console.print("\n[bold cyan]--- Original Feedback ---[/bold cyan]")
                console.print(Markdown(feedback_content))
                console.print("\n[bold cyan]--- End of Feedback ---[/bold cyan]")
                continue

            console.print("\n[bold cyan]Assistant:[/bold cyan]")

            try:
                stream_markdown(conversation.stream(user_text=user_input), console)
                print()  # Add newline after response

            except Exception as e:
                console.print(f"[red]Error getting response: {e}[/red]")
                continue

        except KeyboardInterrupt:
            console.print("\n\n[yellow]Interrupted by user. Goodbye![/yellow]")
            break
        except EOFError:
            console.print("\n\n[yellow]Ending conversation. Good luck with your studies![/yellow]")
            break
        except Exception as e:
            console.print(f"\n[red]Unexpected error: {e}[/red]")
            continue
