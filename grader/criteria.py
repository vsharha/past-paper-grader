from pathlib import Path


def _get_unique_output_path(
    input_path: Path, output_dir: Path, suffix: str = ".md"
) -> Path:
    abs_input = input_path.resolve()
    cwd = Path.cwd()

    try:
        rel_path = abs_input.relative_to(cwd)
        if rel_path.parent != Path("."):
            output_subdir = output_dir / rel_path.parent
            output_subdir.mkdir(parents=True, exist_ok=True)
            return output_subdir / (rel_path.stem + suffix)
    except ValueError:
        pass

    return output_dir / (input_path.stem + suffix)


def has_mark_scheme(paper_file: str | Path) -> bool:
    paper_path = Path(paper_file)
    mark_schemes_dir = Path("mark_schemes")
    mark_scheme_path = _get_unique_output_path(
        paper_path, mark_schemes_dir, suffix=".md"
    )
    return mark_scheme_path.exists()


def has_feedback(paper_file: str | Path, student_answers: str | Path) -> bool:
    paper_path = Path(paper_file)
    feedback_dir = Path("feedback")

    if isinstance(student_answers, list):
        student_path = Path(student_answers[0])
    else:
        student_path = Path(student_answers)

    paper_unique_path = _get_unique_output_path(paper_path, Path("_temp"), suffix="")
    student_unique_path = _get_unique_output_path(
        student_path, Path("_temp"), suffix=""
    )

    if paper_unique_path.parent != Path("_temp"):
        feedback_subdir = feedback_dir / paper_unique_path.parent
        output_filename = (
            f"{paper_unique_path.stem}_feedback_{student_unique_path.stem}.md"
        )
        feedback_path = feedback_subdir / output_filename
    else:
        output_filename = f"{paper_path.stem}_feedback_{student_path.stem}.md"
        feedback_path = feedback_dir / output_filename

    return feedback_path.exists()
