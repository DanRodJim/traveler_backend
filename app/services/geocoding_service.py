from typing import Optional, Tuple
import httpx


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

HEADERS = {
    "User-Agent": "TravelPlannerApp/1.0"
}


async def geocode_address(address: str) -> Optional[Tuple[float, float]]:
    if not address or not address.strip():
        return None

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                NOMINATIM_URL,
                params={
                    "q": address,
                    "format": "json",
                    "limit": 1,
                },
                headers=HEADERS,
            )
            response.raise_for_status()
            results = response.json()

            if not results:
                return None

            lat = float(results[0]["lat"])
            lon = float(results[0]["lon"])
            return (lat, lon)
    except Exception:
        return None