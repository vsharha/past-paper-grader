from litellm_utils import Conversation
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from .generate_grade import generate_feedback


def discuss_feedback(
    provider: str,
    model: str,
    paper_file: str | Path,
    student_answers: str | Path,
    feedback_provider: str | None = None,
    feedback_model: str | None = None
) -> None:
    """
    Interactive chat to discuss exam feedback with AI.

    This function:
    1. Checks if feedback exists, generates it if not
    2. Loads the feedback and context files
    3. Starts an interactive conversation with an AI academic advisor
    4. Allows students to ask questions about their grades and feedback

    Args:
        provider: AI provider for chat conversation (e.g., "gemini", "openai", "claude")
        model: Model for chat conversation (e.g., "gemini-3-pro-preview", "gpt-4", "claude-sonnet-4.5")
        paper_file: Path to the original past paper PDF
        student_answers: Path to the student's answers (PDF or text file)
        feedback_provider: AI provider for feedback generation (defaults to chat_provider if None)
        feedback_model: Model for feedback generation (defaults to chat_model if None)

    Special commands:
        - quit/exit: End the conversation
        - history: Show full conversation history
        - clear: Clear conversation history (keeps system prompt)
        - feedback: Re-display the original feedback
    """
    # Default feedback provider/model to chat provider/model if not specified
    if feedback_provider is None:
        feedback_provider = provider
    if feedback_model is None:
        feedback_model = model
    console = Console()

    # Convert to Path objects
    paper_path = Path(paper_file)
    student_path = Path(student_answers)

    # Derive expected feedback file path
    feedback_dir = Path("feedback")
    feedback_filename = f"{paper_path.stem}_feedback_{student_path.stem}.md"
    feedback_path = feedback_dir / feedback_filename

    # Check if feedback exists, generate if not
    if not feedback_path.exists():
        console.print(f"[yellow]Feedback not found. Generating feedback for {paper_path.name}...[/yellow]")
        generate_feedback(feedback_provider, feedback_model, paper_file, student_answers)
        console.print("[green]Feedback generated successfully![/green]\n")

    # Load feedback content
    try:
        feedback_content = feedback_path.read_text()
    except Exception as e:
        console.print(f"[red]Error reading feedback file: {e}[/red]")
        return

    # Initialize conversation
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

    # Send initial context message
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

        # Stream initial response
        response = ""
        for chunk in conversation.stream(
            user_text=initial_message,
            file=[str(paper_file), str(student_answers)]
        ):
            response += chunk

        # Display with Rich markdown
        console.print(Markdown(response))
    except Exception as e:
        console.print(f"[red]Error initializing conversation: {e}[/red]")
        return

    # Main chat loop
    while True:
        try:
            # Get user input
            console.print("\n[bold green]You:[/bold green] ", end="")
            user_input = input().strip()

            if not user_input:
                continue

            # Handle special commands
            if user_input.lower() in ['quit', 'exit']:
                console.print("\n[yellow]Ending conversation. Good luck with your studies![/yellow]")
                break

            if user_input.lower() == 'history':
                history = conversation.get_history()
                console.print("\n[bold cyan]--- Conversation History ---[/bold cyan]")
                for i, msg in enumerate(history, 1):
                    role = msg['role'].upper()
                    console.print(f"\n[bold]{i}. {role}:[/bold]")
                    if isinstance(msg.get('content'), str):
                        console.print(Markdown(msg['content']))
                    else:
                        console.print(msg.get('content'))
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

            # Stream AI response
            console.print("\n[bold cyan]Assistant:[/bold cyan]")
            response_text = ""

            try:
                for chunk in conversation.stream(user_text=user_input):
                    response_text += chunk

                # Display with Rich markdown
                console.print(Markdown(response_text))

            except Exception as e:
                console.print(f"[red]Error getting response: {e}[/red]")
                continue

        except KeyboardInterrupt:
            console.print("\n\n[yellow]Interrupted by user. Goodbye![/yellow]")
            break
        except Exception as e:
            console.print(f"\n[red]Unexpected error: {e}[/red]")
            continue
