from app.services.ai_service import AIService

def test_ai_service_no_reply():
    res = AIService.generate_followup(
        company="Acme Inc",
        job_title="DevOps Engineer",
        hr_name="Sarah HR",
        user_name="Nikhil",
        original_email="I'm applying for DevOps Engineer.",
        email_thread=[{"sender": "nikhil@example.com", "body": "I'm applying.", "is_reply": False}],
        previous_followups=[],
        followup_number=1
    )
    assert res["should_follow_up"] is True
    assert "Acme Inc" in res["subject"] or "DevOps Engineer" in res["subject"]
    assert "DevOps Engineer" in res["body"]

def test_ai_service_hr_replied():
    res = AIService.generate_followup(
        company="Acme Inc",
        job_title="DevOps Engineer",
        hr_name="Sarah HR",
        user_name="Nikhil",
        original_email="I'm applying for DevOps Engineer.",
        email_thread=[
            {"sender": "nikhil@example.com", "body": "I'm applying.", "is_reply": False},
            {"sender": "sarah@acme.com", "body": "Thanks, let's talk next Tuesday.", "is_reply": True, "sender_type": "hr"}
        ],
        previous_followups=[],
        followup_number=1
    )
    assert res["should_follow_up"] is False
    assert "already responded" in res["reason"].lower()
