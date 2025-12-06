from grader import discuss_feedback

# Example 1: Use the same model for both chat and feedback generation
# discuss_feedback(
#     chat_provider="gemini",
#     chat_model="gemini-3-pro-preview",
#     paper_file="past_papers/2017281-INFR08018.pdf",
#     student_answers="solutions/Gallery_20251206_143729_251206_143754.pdf"
# )

# Example 2: Use different models - better model for chat, cheaper for feedback
discuss_feedback(
    provider="gemini",
    model="gemini-3-pro-preview",
    paper_file="past_papers/2017281-INFR08018.pdf",
    student_answers="solutions/Gallery_20251206_143729_251206_143754.pdf",
    feedback_provider="gemini",
    feedback_model="gemini-2.5-flash"
)