from grader import discuss_feedback

discuss_feedback(
    provider="gemini",
    model="gemini-2.5-flash",
    paper_file="past_papers/2017281-INFR08018.pdf",
    student_answers="solutions/Gallery_20251206_143729_251206_143754.pdf",
    feedback_provider="gemini",
    feedback_model="gemini-3-pro-preview"
)