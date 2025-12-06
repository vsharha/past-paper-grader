from grader import generate_mark_scheme, generate_feedback, discuss_feedback

# Example 1: Generate mark scheme for a past paper
# generate_mark_scheme(
#     provider="gemini",
#     model="gemini-3-pro-preview",
#     file="past_papers/2017281-INFR08018.pdf"
# )

# Example 2: Generate feedback for student answers
# generate_feedback(
#     provider="gemini",
#     model="gemini-3-pro-preview",
#     paper_file="past_papers/2017281-INFR08018.pdf",
#     student_answers="student_submissions/example_answers.pdf"
# )

# Example 3: Interactive chat to discuss feedback with AI
discuss_feedback(
    provider="gemini",
    model="gemini-3-pro-preview",
    paper_file="past_papers/2017281-INFR08018.pdf",
    student_answers="student_submissions/example_answers.pdf"
)