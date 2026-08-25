import json
from groq import Groq
from app.core.config import settings
from app.schemas.ai_estimator import (
    AiEstimatorRequest,
    AiEstimatorResponse,
    AiEstimatorBreakdown,
)


class AiEstimatorService:
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = "llama-3.3-70b-versatile"

    def _build_prompt(self, request: AiEstimatorRequest) -> str:
        interests_str = ", ".join(request.interests) if request.interests else "general tourism"

        dates_context = ""
        if request.start_date and request.end_date:
            dates_context = f"""
TRAVEL DATES ANALYSIS (this MUST affect your price calculations):
- Departure: {request.start_date}
- Return: {request.end_date}
- You must research the typical season for {request.destination} during these dates
- Identify if this falls in peak, shoulder, or low season
- Apply realistic price multipliers based on the season (e.g. peak season flights and hotels can be 50-200% more expensive than low season)
- Consider local holidays, festivals, and events during these dates that affect prices
"""
        elif request.start_date:
            dates_context = f"""
TRAVEL DATE ANALYSIS (this MUST affect your price calculations):
- Departure: {request.start_date}
- Research the typical season for {request.destination} during this period
- Apply realistic price multipliers based on the season
"""

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
{dates_context}

IMPORTANT PRICING RULES:
- Base your estimates on REAL current market prices
- If travel dates are provided, seasonal pricing MUST be reflected in your numbers
- Peak seasons (cherry blossom in Japan March-April, summer in Europe, etc.) significantly increase flight and hotel costs
- Low seasons offer 20-40% discounts vs peak
- All amounts represent total cost for ALL {request.travelers} traveler(s)
- The sum of breakdown items MUST equal total_estimated

Respond ONLY with a valid JSON object, no markdown, no explanation, just the JSON:

{{
    "destination": "{request.destination}",
    "origin": "{request.origin}",
    "duration_days": {request.duration_days},
    "travelers": {request.travelers},
    "currency": "{request.currency}",
    "total_estimated": <total cost for ALL travelers>,
    "breakdown": {{
        "flights": <round trip flights for all travelers>,
        "accommodation": <total accommodation cost>,
        "food": <total food and dining cost>,
        "activities": <total activities and entrance fees>,
        "transport": <local transport cost>,
        "misc": <miscellaneous and emergency fund>
    }},
    "notes": "<2-3 sentences: explain the seasonal pricing context for these dates, mention if it's peak/shoulder/low season, and give a key money-saving tip>",
    "travel_style": "{request.travel_style}",
    "start_date": "{request.start_date or ''}",
    "end_date": "{request.end_date or ''}"
}}"""

    async def generate_estimate(
        self,
        request: AiEstimatorRequest
    ) -> AiEstimatorResponse:
        prompt = self._build_prompt(request)

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a travel budget expert with expertise in seasonal pricing. Always respond with valid JSON only, no markdown. Your price estimates must accurately reflect seasonal demand and local events for the specified travel dates."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            max_tokens=1024,
        )

        raw_response = completion.choices[0].message.content.strip() if completion.choices[0].message.content is not None else ""

        if raw_response.startswith("```"):
            raw_response = raw_response.split("```")[1]
            if raw_response.startswith("json"):
                raw_response = raw_response[4:]
            raw_response = raw_response.strip()

        data = json.loads(raw_response)

        return AiEstimatorResponse(
            destination=data["destination"],
            origin=data["origin"],
            duration_days=data["duration_days"],
            travelers=data["travelers"],
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
            start_date=request.start_date,
        )