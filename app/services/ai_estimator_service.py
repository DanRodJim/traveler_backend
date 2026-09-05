import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from groq import Groq, APIError
from openai import OpenAI

from app.core.config import settings
from app.core.exceptions import EstimationNotFoundError
from app.schemas.ai_estimator import (
    AiEstimatorRequest,
    AiEstimatorResponse,
    AiEstimatorBreakdown,
)

logger = logging.getLogger(__name__)

DATE_FORMAT = "%Y-%m-%d"

TRAVEL_ESTIMATE_SCHEMA = {
    "type": "object",
    "properties": {
        "destination": {"type": "string"},
        "origin": {"type": "string"},
        "duration_days": {"type": "integer"},
        "travelers": {"type": "integer"},
        "currency": {"type": "string"},
        "total_estimated": {"type": "number"},
        "breakdown": {
            "type": "object",
            "properties": {
                "flights": {"type": "number"},
                "accommodation": {"type": "number"},
                "food": {"type": "number"},
                "activities": {"type": "number"},
                "transport": {"type": "number"},
                "misc": {"type": "number"}
            },
            "required": ["flights", "accommodation", "food", "activities", "transport", "misc"],
            "additionalProperties": False
        },
        "notes": {"type": "string"},
        "travel_style": {"type": "string"},
        "start_date": {"type": "string"},
        "end_date": {"type": "string"}
    },
    "required": [
        "destination", "origin", "duration_days", "travelers", "currency",
        "total_estimated", "breakdown", "notes", "travel_style", "start_date", "end_date"
    ],
    "additionalProperties": False
}


class AiEstimatorService:
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = "openai/gpt-oss-20b"

        self.openrouter_client = OpenAI(
            base_url="https://openrouter.ai",
            api_key=settings.OPENROUTER_API_KEY,
            default_headers={
                "HTTP-Referer": settings.FRONTEND_URL,
                "X-Title": "Travel Planner App",
            }
        )
        self.backup_model = "qwen/qwen-2.5-7b-instruct:free"

    def _build_prompt(self, request: AiEstimatorRequest, start_date: str, end_date: str) -> str:
        interests_str = ", ".join(request.interests) if request.interests else "general tourism"

        return f"""You are an expert travel budget planner with deep knowledge of seasonal pricing worldwide.

TRIP DETAILS:
- Origin: {request.origin}
- Destination: {request.destination}
- Duration: {request.duration_days} days
- Travelers: {request.travelers} people
- Travel style: {request.travel_style}
- Accommodation preference: {request.accommodation_type}
- Interests: {interests_str}
- Currency: {request.currency}
{f'- Additional notes: {request.additional_notes}' if request.additional_notes else ''}

TRAVEL DATES ANALYSIS (this MUST affect your price calculations):
- Departure Date: {start_date}
- Return Date: {end_date}
- Research the typical season for {request.destination} during these specific dates (peak, shoulder, or low).
- Apply realistic price multipliers based on this season.

IMPORTANT PRICING RULES:
1. Base your estimates on REAL current market prices.
2. Seasonal pricing MUST be reflected in your numbers.
3. All amounts represent total cost for ALL {request.travelers} traveler(s).
4. CRITICAL: The sum of flights, accommodation, food, activities, transport, and misc MUST exactly equal total_estimated.
5. CRITICAL FOR THE 'notes' FIELD: Write a MAXIMUM of 1 or 2 very short and concise sentences explaining the seasonal context. Avoid long paragraphs to save tokens."""

    def _resolve_dates(self, request: AiEstimatorRequest) -> tuple[str, str]:
        if not request.start_date or not request.start_date.strip():
            start_dt = datetime.today()
        else:
            try:
                start_dt = datetime.strptime(request.start_date, DATE_FORMAT)
            except ValueError:
                start_dt = datetime.today()

        if request.end_date and request.end_date.strip():
            end_date_str = request.end_date
        else:
            end_dt = start_dt + timedelta(days=request.duration_days)
            end_date_str = end_dt.strftime(DATE_FORMAT)

        return start_dt.strftime(DATE_FORMAT), end_date_str

    def generate_estimate(self, request: AiEstimatorRequest) -> AiEstimatorResponse:
        start_date, end_date = self._resolve_dates(request)
        prompt = self._build_prompt(request, start_date, end_date)
        content: Optional[str] = None

        # --- First try with GROQ ---
        try:
            logger.info(f"Attempting estimate with Groq ({self.model})...")
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a travel budget expert. Generate a precise cost estimation matching the requested JSON schema perfectly."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=2048,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "travel_estimate",
                        "strict": True,
                        "schema": TRAVEL_ESTIMATE_SCHEMA
                    }
                }
            )
            content = completion.choices[0].message.content

        except APIError as groq_error:
            status_code = getattr(groq_error, "status_code", None)

            if status_code == 400:
                logger.exception(f"Groq schema/request error (400): {groq_error}")
                raise groq_error

            logger.warning(f"Groq unavailable ({groq_error}). Falling back to OpenRouter...")

            # --- When GROQ fail, try with OpenRouter ---
            try:
                backup_completion = self.openrouter_client.chat.completions.create(
                    model=self.backup_model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a travel budget expert. Respond ONLY with a valid JSON object matching the requested fields. "
                                "Never wrap the response in markdown blocks like ```json."
                            )
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.1,
                    max_tokens=2048
                )
                content = backup_completion.choices[0].message.content

            except Exception as backup_error:
                logger.exception(f"Critical failure: OpenRouter also failed: {backup_error}")
                raise EstimationNotFoundError()

        if content is None:
            raise EstimationNotFoundError()

        raw_response = content.strip()
        if raw_response.startswith("```"):
            parts = raw_response.split("```")
            if len(parts) > 1:
                raw_response = parts[1]
                if raw_response.startswith("json"):
                    raw_response = raw_response[4:]
            raw_response = raw_response.strip()

        try:
            data = json.loads(raw_response)
        except json.JSONDecodeError as json_err:
            logger.exception(f"Failed to parse JSON response: {json_err}. Raw content: {content}")
            raise EstimationNotFoundError()

        try:
            return AiEstimatorResponse(
                destination=data["destination"],
                origin=data["origin"],
                duration_days=int(data["duration_days"]),
                travelers=int(data["travelers"]),
                currency=data["currency"],
                total_estimated=float(data["total_estimated"]),
                breakdown=AiEstimatorBreakdown(
                    flights=float(data["breakdown"]["flights"]),
                    accommodation=float(data["breakdown"]["accommodation"]),
                    food=float(data["breakdown"]["food"]),
                    activities=float(data["breakdown"]["activities"]),
                    transport=float(data["breakdown"]["transport"]),
                    misc=float(data["breakdown"]["misc"]),
                ),
                notes=data["notes"],
                travel_style=data["travel_style"],
                start_date=start_date,
                end_date=end_date,
            )
        except (KeyError, ValueError, TypeError) as mapping_error:
            logger.exception(f"Malformed response data: {mapping_error}. Raw data: {data}")
            raise EstimationNotFoundError()