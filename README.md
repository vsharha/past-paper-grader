# Past Paper Grader

AI-powered CLI tool for grading past exam papers. Generates mark schemes, provides student feedback, and enables interactive discussion of grades.

## Requirements

- Python 3.14+
- [UV](https://github.com/astral-sh/uv) package manager

## Installation

```bash
uv sync
```

## Usage

```bash
uv run python main.py
```

Select from three modes:

1. **Generate Mark Scheme** - Creates marking criteria from a past paper PDF
2. **Generate Feedback** - Grades student answers against a mark scheme
3. **Discuss Feedback** - Interactive chat to discuss grading results

## Directory Structure

```
past_papers/     # Place exam paper PDFs here
solutions/       # Place student answer PDFs here
mark_schemes/    # Generated mark schemes (auto-created)
feedback/        # Generated feedback files (auto-created)
```

## Configuration

The tool uses Gemini models by default. Configure your API key:

```bash
export GEMINI_API_KEY=your_key_here
```

## Features

- Batch processing with parallel execution
- Follow-through marking (ECF) support
- Preserves directory structure for organized output
- Streaming responses with live markdown rendering
- Input history in chat mode (arrow keys)
