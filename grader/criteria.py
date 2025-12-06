from pathlib import Path


def _get_unique_output_path(
    input_path: Path, output_dir: Path, suffix: str = ".md"
) -> Path:
    """
    Generate a unique output path that preserves directory structure.

    For files in subdirectories, creates corresponding subdirectories in output_dir.
    For files in current directory, uses filename directly.

    Examples:
        past_papers/2023/exam.pdf -> mark_schemes/past_papers/2023/exam.md
        exam.pdf -> mark_schemes/exam.md
    """
    # Get the absolute path to handle relative paths correctly
    abs_input = input_path.resolve()
    cwd = Path.cwd()

    # Try to get relative path from current working directory
    try:
        rel_path = abs_input.relative_to(cwd)
        # If the file is in a subdirectory, preserve the structure
        if rel_path.parent != Path("."):
            output_subdir = output_dir / rel_path.parent
            output_subdir.mkdir(parents=True, exist_ok=True)
            return output_subdir / (rel_path.stem + suffix)
    except ValueError:
        # File is outside cwd, use absolute path's parent dirs
        pass

    # Fallback: just use the filename
    return output_dir / (input_path.stem + suffix)


def has_mark_scheme(paper_file: str | Path) -> bool:
    """
    Check if a mark scheme already exists for the given paper.

    Args:
        paper_file: Path to the exam paper PDF

    Returns:
        True if mark scheme exists, False otherwise
    """
    paper_path = Path(paper_file)
    mark_schemes_dir = Path("mark_schemes")
    mark_scheme_path = _get_unique_output_path(
        paper_path, mark_schemes_dir, suffix=".md"
    )
    return mark_scheme_path.exists()


def has_feedback(paper_file: str | Path, student_answers: str | Path) -> bool:
    """
    Check if feedback already exists for the given paper and student answers.

    Args:
        paper_file: Path to the exam paper PDF
        student_answers: Path to the student's answers

    Returns:
        True if feedback exists, False otherwise
    """
    paper_path = Path(paper_file)
    feedback_dir = Path("feedback")

    # Handle list of files
    if isinstance(student_answers, list):
        student_path = Path(student_answers[0])
    else:
        student_path = Path(student_answers)

    # Get unique paths for both paper and student answers
    paper_unique_path = _get_unique_output_path(paper_path, Path("_temp"), suffix="")
    student_unique_path = _get_unique_output_path(
        student_path, Path("_temp"), suffix=""
    )

    # Create the feedback path matching generate_feedback logic
    if paper_unique_path.parent != Path("_temp"):
        # Paper is in subdirectory - preserve structure
        feedback_subdir = feedback_dir / paper_unique_path.parent
        output_filename = (
            f"{paper_unique_path.stem}_feedback_{student_unique_path.stem}.md"
        )
        feedback_path = feedback_subdir / output_filename
    else:
        # Paper is in root - use simple naming
        output_filename = f"{paper_path.stem}_feedback_{student_path.stem}.md"
        feedback_path = feedback_dir / output_filename

    return feedback_path.exists()
