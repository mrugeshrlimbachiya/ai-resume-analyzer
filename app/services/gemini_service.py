import json
import re
import google.generativeai as genai
from app.config import settings

# Configure Gemini API key once at module load
genai.configure(api_key=settings.GEMINI_API_KEY)

ANALYSIS_PROMPT_TEMPLATE = """
You are an expert ATS (Applicant Tracking System) analyzer and career coach.
Analyze the following resume text and return a detailed evaluation.

RESUME TEXT:
{resume_text}

Provide your analysis STRICTLY in the following JSON format (no extra text, no markdown, no code blocks):

{{
  "ats_score": <integer between 0 and 100>,
  "strengths": [
    "<strength 1>",
    "<strength 2>",
    "<strength 3>",
    "<strength 4>",
    "<strength 5>"
  ],
  "weaknesses": [
    "<weakness 1>",
    "<weakness 2>",
    "<weakness 3>",
    "<weakness 4>",
    "<weakness 5>"
  ],
  "missing_keywords": [
    "<keyword 1>",
    "<keyword 2>",
    "<keyword 3>",
    "<keyword 4>",
    "<keyword 5>",
    "<keyword 6>",
    "<keyword 7>",
    "<keyword 8>"
  ],
  "interview_questions": [
    "<question 1>",
    "<question 2>",
    "<question 3>",
    "<question 4>",
    "<question 5>",
    "<question 6>",
    "<question 7>"
  ]
}}

SCORING CRITERIA for ats_score:
- Contact information completeness (10 pts)
- Work experience relevance and detail (25 pts)
- Education section (15 pts)
- Skills section with relevant keywords (20 pts)
- Resume formatting and structure (10 pts)
- Quantifiable achievements (10 pts)
- Action verbs usage (10 pts)

RULES:
- Return ONLY valid JSON. No markdown, no explanation, no ```json``` blocks.
- ats_score must be an integer (0-100).
- Each list must have at least 3 items.
- Interview questions should be based on the actual experience listed in the resume.
- missing_keywords should be relevant to the candidate's field.
"""


class GeminiService:
    """Service class for interacting with Google Gemini API."""

    def __init__(self):
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config=genai.GenerationConfig(
                temperature=0.3,         # Low temperature for consistent structured output
                top_p=0.95,
                top_k=40,
                max_output_tokens=4096,
            ),
        )

    async def analyze_resume(self, resume_text: str) -> dict:
        """
        Send resume text to Gemini and parse the structured JSON response.

        Args:
            resume_text: Extracted plain text from the resume PDF.

        Returns:
            Dictionary with keys: ats_score, strengths, weaknesses,
            missing_keywords, interview_questions.

        Raises:
            ValueError: If Gemini response cannot be parsed as valid JSON.
            Exception: For API errors.
        """
        if not resume_text or not resume_text.strip():
            raise ValueError("Resume text is empty. Cannot analyze an empty document.")

        # Trim to ~12000 chars to stay within free-tier token limits
        trimmed_text = resume_text[:12000]

        prompt = ANALYSIS_PROMPT_TEMPLATE.format(resume_text=trimmed_text)

        try:
            response = self.model.generate_content(prompt)
        except Exception as e:
            raise Exception(f"Gemini API call failed: {str(e)}")

        raw_text = response.text.strip()

        parsed = self._parse_response(raw_text)
        return parsed

    def _parse_response(self, raw_text: str) -> dict:
        """
        Parse and validate the JSON response from Gemini.

        Handles cases where the model wraps output in markdown code fences.
        """
        # Strip markdown code fences if present
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            # Remove opening fence (```json or ```)
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            # Remove closing fence
            cleaned = re.sub(r"\s*```$", "", cleaned)
            cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Gemini returned invalid JSON. Parse error: {str(e)}\n"
                f"Raw response (first 500 chars): {raw_text[:500]}"
            )

        # Validate required fields
        required_fields = ["ats_score", "strengths", "weaknesses", "missing_keywords", "interview_questions"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field in Gemini response: '{field}'")

        # Coerce and clamp ats_score
        try:
            data["ats_score"] = max(0, min(100, float(data["ats_score"])))
        except (TypeError, ValueError):
            raise ValueError(f"Invalid ats_score value: {data.get('ats_score')}")

        # Ensure list fields are actually lists
        list_fields = ["strengths", "weaknesses", "missing_keywords", "interview_questions"]
        for field in list_fields:
            if not isinstance(data[field], list):
                raise ValueError(f"Field '{field}' must be a list, got: {type(data[field])}")
            if len(data[field]) == 0:
                raise ValueError(f"Field '{field}' must not be empty.")

        return data


# Module-level singleton
gemini_service = GeminiService()
