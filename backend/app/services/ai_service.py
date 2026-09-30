import json
import logging
import httpx
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.core.logging import logger

class AIService:
    """
    Dedicated AI Service for analyzing email conversations and generating personalized follow-up emails.
    Supports OpenAI, Gemini, or fallback template engine when API keys are not provided.
    """

    @classmethod
    def generate_followup(
        cls,
        company: str,
        job_title: str,
        hr_name: str,
        user_name: str,
        original_email: str,
        email_thread: List[Dict[str, Any]],
        previous_followups: List[Dict[str, Any]],
        followup_number: int = 1
    ) -> Dict[str, Any]:

        # First check if HR has already replied in thread
        hr_replied = any(
            msg.get("sender_type") == "hr" or msg.get("is_reply", False)
            for msg in email_thread
        )

        if hr_replied:
            logger.log_event("ai_generation_skipped", {
                "company": company,
                "reason": "Recruiter has already responded."
            })
            return {
                "should_follow_up": False,
                "reason": "Recruiter has already responded.",
                "subject": None,
                "body": None
            }

        # Context build
        thread_summary = []
        for msg in email_thread:
            sender = msg.get("sender", "Unknown")
            body_snippet = msg.get("body", "")[:300]
            thread_summary.append(f"From {sender}: {body_snippet}")

        context_prompt = f"""
Company: {company}
Position: {job_title}
HR Contact Name: {hr_name}
Applicant Name: {user_name}
Follow-up Stage Number: {followup_number}

Original Email Sent:
{original_email[:500]}

Thread Messages:
{chr(10).join(thread_summary) if thread_summary else "No subsequent messages."}

Previous Follow-ups Count: {len(previous_followups)}
"""

        # Try API provider if configured
        if settings.AI_API_KEY and settings.AI_PROVIDER in ["openai", "gemini"]:
            try:
                if settings.AI_PROVIDER == "openai":
                    return cls._call_openai(context_prompt, company, job_title, hr_name, user_name, followup_number)
                elif settings.AI_PROVIDER == "gemini":
                    return cls._call_gemini(context_prompt, company, job_title, hr_name, user_name, followup_number)
            except Exception as e:
                logger.log_event("ai_generation_failed", {
                    "error": str(e),
                    "fallback": "Using intelligent template generator"
                }, level="warning")

        # Smart fallback template generator
        return cls._fallback_template(company, job_title, hr_name, user_name, followup_number)

    @classmethod
    def _call_openai(cls, prompt: str, company: str, job_title: str, hr_name: str, user_name: str, followup_number: int) -> Dict[str, Any]:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.AI_API_KEY}",
            "Content-Type": "application/json"
        }

        system_instruction = (
            "You are an AI career consultant. Generate a concise, polite, professional follow-up email. "
            "Respond ONLY with valid JSON containing keys: 'should_follow_up' (boolean), 'subject' (string), 'body' (string)."
        )

        payload = {
            "model": settings.AI_MODEL or "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.5
        }

        with httpx.Client(timeout=20.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            return {
                "should_follow_up": parsed.get("should_follow_up", True),
                "reason": parsed.get("reason"),
                "subject": parsed.get("subject", f"Follow-up: {job_title} Application - {company}"),
                "body": parsed.get("body", "")
            }

    @classmethod
    def _call_gemini(cls, prompt: str, company: str, job_title: str, hr_name: str, user_name: str, followup_number: int) -> Dict[str, Any]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.AI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        
        full_prompt = (
            "You are an AI assistant. Return ONLY a JSON object with keys 'should_follow_up', 'subject', 'body'.\n"
            f"{prompt}"
        )
        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}]
        }

        with httpx.Client(timeout=20.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            # Clean markdown formatting if present
            clean_text = raw_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            parsed = json.loads(clean_text)
            return {
                "should_follow_up": parsed.get("should_follow_up", True),
                "reason": parsed.get("reason"),
                "subject": parsed.get("subject", f"Follow-up: {job_title} Application - {company}"),
                "body": parsed.get("body", "")
            }

    @classmethod
    def _fallback_template(cls, company: str, job_title: str, hr_name: str, user_name: str, followup_number: int) -> Dict[str, Any]:
        salutation = f"Dear {hr_name}," if hr_name and hr_name.lower() != "hr" else "Dear Hiring Manager,"

        if followup_number == 1:
            body = (
                f"{salutation}\n\n"
                f"I hope this email finds you well.\n\n"
                f"I am writing to follow up on my application for the {job_title} role at {company}. "
                f"I remain enthusiastic about the position and the opportunity to contribute to your team.\n\n"
                f"Please let me know if you need any additional information or documentation from my end. "
                f"I look forward to hearing from you regarding the next steps.\n\n"
                f"Best regards,\n"
                f"{user_name}"
            )
        elif followup_number == 2:
            body = (
                f"{salutation}\n\n"
                f"Following up on my previous message regarding the {job_title} position at {company}.\n\n"
                f"I wanted to re-iterate my strong interest in joining {company}. "
                f"Given my background and skillset, I am confident I could add immediate value to your team.\n\n"
                f"I would appreciate any quick update on the hiring timeline when convenient for you.\n\n"
                f"Thank you for your time and consideration.\n\n"
                f"Best regards,\n"
                f"{user_name}"
            )
        elif followup_number == 3:
            body = (
                f"{salutation}\n\n"
                f"I am checking in once more regarding the {job_title} application submitted for {company}.\n\n"
                f"I understand your team is likely busy with recruitment, but I wanted to make sure my application hasn't fallen through the cracks.\n\n"
                f"Could you please confirm if this position is still open or if the hiring process has progressed?\n\n"
                f"Best regards,\n"
                f"{user_name}"
            )
        else:
            body = (
                f"{salutation}\n\n"
                f"I hope you are having a great week.\n\n"
                f"This will be my final follow-up regarding the {job_title} role at {company}. "
                f"I remain very keen on potential opportunities with your team, either now or in the future.\n\n"
                f"If the position has been filled, I would be grateful for a quick confirmation so I can update my records. "
                f"Either way, thank you again for your time and consideration.\n\n"
                f"Warm regards,\n"
                f"{user_name}"
            )

        subject = f"Follow-up: {job_title} Application - {company}"

        return {
            "should_follow_up": True,
            "reason": None,
            "subject": subject,
            "body": body
        }
