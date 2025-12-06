from litellm_utils import request_ai
from pathlib import Path


def _get_unique_output_path(input_path: Path, output_dir: Path, suffix: str = ".md") -> Path:
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
        if rel_path.parent != Path('.'):
            output_subdir = output_dir / rel_path.parent
            output_subdir.mkdir(parents=True, exist_ok=True)
            return output_subdir / (rel_path.stem + suffix)
    except ValueError:
        # File is outside cwd, use absolute path's parent dirs
        pass

    # Fallback: just use the filename
    return output_dir / (input_path.stem + suffix)


def generate_mark_scheme(provider: str, model: str, file: str | Path, save: bool = True, additional_instructions: str = ""):
    system_prompt = """You are an expert mark scheme creator for undergraduate Computer Science and Mathematics courses.

Your task is to analyze the provided exam paper PDF and generate a comprehensive, structured mark scheme that will be used by an AI grading system to provide feedback to students.

## Instructions:

1. **Analyze the Paper**: Carefully read through all questions in the exam paper
2. **Question-by-Question Breakdown**: Create a mark scheme for each question and sub-question
3. **Output Format**: Use clear markdown formatting for easy parsing by AI systems

## Mark Scheme Structure:

For each question, provide:

### Question Headers
- Use markdown headers: `## Question 1`, `### Part (a)`, etc.
- Include mark allocation: `[X marks]` or `[X points]` after each question/part

### Model Answers
- Provide clear, concise model answers or solution approaches
- For CS questions: Include code examples, algorithm descriptions, pseudocode, complexity analysis where relevant
- For Math questions: Include step-by-step solutions, formulas, equations, numerical answers

### Marking Criteria
- List key points that earn marks using bullet points
- Specify mark distribution (e.g., "1 mark for correct formula, 2 marks for correct calculation, 1 mark for final answer")
- Include partial credit rules (e.g., "Award 2/3 marks if method is correct but calculation error")

### Alternative Solutions
- Note any acceptable alternative approaches or answers
- Specify variations that should receive full credit
- This is especially important for CS (multiple valid algorithms) and Math (different solution methods)

### Common Mistakes (Optional)
- Brief notes on common errors to watch for
- Helps the AI grader recognize and provide better feedback

## Formatting Requirements:

- Use consistent markdown structure throughout
- Use bullet points (`-` or `*`) for lists
- Use code blocks (```) for code examples
- Use LaTeX notation for mathematical expressions where needed (e.g., `$x^2 + y^2 = r^2$`)
- Include a marks summary table at the end showing total marks per question

## Target Audience:

- Undergraduate foundational level (Year 1-2)
- Assume students have basic knowledge but may make common beginner mistakes
- Mark schemes should be precise enough for automated grading but fair and educational

## Example Structure:

```markdown
## Question 1 [10 marks]

### Part (a) [4 marks]
**Question**: [Extracted from paper]

**Model Answer**:
[Clear solution]

**Marking Criteria**:
- 2 marks: Correct identification of algorithm/formula
- 1 mark: Proper setup of equation/code structure
- 1 mark: Correct final answer

**Alternative Approaches**:
- [Any other valid methods]

### Part (b) [6 marks]
...

---

## Marks Summary

| Question | Marks |
|----------|-------|
| 1        | 10    |
| 2        | 15    |
| **Total**| **25**|
```

Generate a complete, well-structured mark scheme following these guidelines.
"""

    # Append additional instructions if provided
    if additional_instructions:
        system_prompt += f"\n\n## Additional Instructions:\n\n{additional_instructions}"

    response = request_ai(
        provider=provider,
        model=model,
        system_prompt=system_prompt,
        user_text="Use the attached file as reference",
        file=file
    )

    if save:
        mark_schemes_dir = Path("mark_schemes")
        mark_schemes_dir.mkdir(exist_ok=True)

        if isinstance(file, list):
            pdf_path = Path(file[0])
        else:
            pdf_path = Path(file)

        output_path = _get_unique_output_path(pdf_path, mark_schemes_dir, suffix=".md")
        output_path.write_text(response)
        print(f"Mark scheme saved to: {output_path}")

    return response



def generate_feedback(provider: str, model: str, paper_file: str | Path, student_answers: str | Path | list[str | Path], save: bool = True, additional_instructions: str = ""):
    paper_path = Path(paper_file)
    mark_schemes_dir = Path("mark_schemes")

    # Use the same unique path logic to find the mark scheme
    mark_scheme_path = _get_unique_output_path(paper_path, mark_schemes_dir, suffix=".md")

    if not mark_scheme_path.exists():
        print(f"Mark scheme not found. Generating mark scheme for {paper_path.name}...")
        generate_mark_scheme(provider, model, paper_file, additional_instructions=additional_instructions)

    mark_scheme = mark_scheme_path.read_text()

    feedback_prompt = """You are an expert academic grader for undergraduate Computer Science and Mathematics courses.

Your task is to evaluate student answers against the provided mark scheme and generate detailed, constructive feedback.

## Instructions:

1. **Review the Mark Scheme**: Understand the expected answers, marking criteria, and point allocations
2. **Evaluate Student Answers**: Compare student responses to the mark scheme
3. **Provide Structured Feedback**: Give question-by-question feedback with grades

## Feedback Structure:

### For Each Question:
- **Question Number/Part**: Clearly identify which question
- **Student Answer Summary**: Briefly summarize what the student wrote
- **Marks Awarded**: Show marks earned vs. total marks (e.g., "7/10 marks")
- **Strengths**: What the student did well
- **Areas for Improvement**: What was missing or incorrect
- **Specific Feedback**: Point-by-point comparison to mark scheme criteria

### Overall Assessment:
- **Total Score**: Sum of all marks (e.g., "Total: 75/100 marks = 75%")
- **Grade**: Convert to letter grade if appropriate
- **General Comments**: Overall performance summary
- **Study Recommendations**: Specific topics to review

## Feedback Style:

- Be constructive and encouraging
- Be specific about what was right or wrong
- Reference the mark scheme criteria
- Suggest how to improve
- Use clear markdown formatting

## Output Format:

```markdown
# Grading Feedback: [Exam Name/Code]

---

## Question 1 [10 marks]

### Part (a) - **3/4 marks**

**Student Answer**: [Brief summary]

**Feedback**:
✓ Correct identification of the algorithm (2 marks)
✓ Proper setup (1 mark)
✗ Final answer incorrect due to calculation error (0/1 marks)

**Comments**: Your approach was correct, but there's an error in the final calculation. Review [specific topic].

### Part (b) - **5/6 marks**
...

---

## Question 2 [15 marks]
...

---

## Overall Assessment

**Total Score**: 75/100 marks (75%)
**Grade**: B

**Overall Comments**:
[Summary of performance]

**Strengths**:
- [Key strengths]

**Areas for Improvement**:
- [Key areas to work on]

**Recommended Study Topics**:
- [Specific topics to review]
```

## Important Guidelines:

- Award partial credit fairly according to the mark scheme
- Be specific about which marking criteria were met or missed
- If an answer is completely correct, acknowledge it enthusiastically
- If an answer is wrong, explain why and how to improve
- Consider alternative valid approaches mentioned in the mark scheme
- Be consistent with the mark scheme's grading rubric

Generate comprehensive, fair, and educational feedback.
"""

    # Append additional instructions if provided
    if additional_instructions:
        feedback_prompt += f"\n\n## Additional Instructions:\n\n{additional_instructions}"

    user_message = f"""Please grade the student's answers using the mark scheme below.

# MARK SCHEME:

{mark_scheme}

---

# STUDENT ANSWERS:

Please evaluate the student answers in the attached file.
"""

    response = request_ai(
        provider=provider,
        model=model,
        system_prompt=feedback_prompt,
        user_text=user_message,
        file=student_answers
    )

    if save:
        feedback_dir = Path("feedback")
        feedback_dir.mkdir(exist_ok=True)

        # Handle both single file and list of files
        if isinstance(student_answers, list):
            student_path = Path(student_answers[0])
        else:
            student_path = Path(student_answers)

        # Get unique paths for both paper and student answers
        paper_unique_path = _get_unique_output_path(paper_path, Path("_temp"), suffix="")
        student_unique_path = _get_unique_output_path(student_path, Path("_temp"), suffix="")

        # Create the relative path structure in feedback directory
        # Combine paper and student paths to create unique identifier
        if paper_unique_path.parent != Path("_temp"):
            # Paper is in subdirectory - preserve structure
            feedback_subdir = feedback_dir / paper_unique_path.parent
            feedback_subdir.mkdir(parents=True, exist_ok=True)
            output_filename = f"{paper_unique_path.stem}_feedback_{student_unique_path.stem}.md"
            output_path = feedback_subdir / output_filename
        else:
            # Paper is in root - use simple naming
            output_filename = f"{paper_path.stem}_feedback_{student_path.stem}.md"
            output_path = feedback_dir / output_filename

        output_path.write_text(response)
        print(f"Feedback saved to: {output_path}")

    return response
