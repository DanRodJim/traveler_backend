import time
from decimal import Decimal
from typing import Dict, Optional, Tuple

import httpx


_rates_cache: Dict[str, Tuple[Dict[str, float], float]] = {}
_CACHE_TTL_SECONDS = 6 * 60 * 60  # 6 hours


def _get_cached_rates(base_currency: str) -> Optional[Dict[str, float]]:
    cached = _rates_cache.get(base_currency)
    if not cached:
        return None

    rates, cached_at = cached
    if time.monotonic() - cached_at > _CACHE_TTL_SECONDS:
        return None

    return rates


def _store_cached_rates(base_currency: str, rates: Dict[str, float]) -> None:
    _rates_cache[base_currency] = (rates, time.monotonic())


async def get_exchange_rates(base_currency: str) -> Dict[str, float]:
    cached_rates = _get_cached_rates(base_currency)
    if cached_rates is not None:
        return cached_rates

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.frankfurter.dev/v2/rates",
                params={"base": base_currency}
            )
            response.raise_for_status()
            data = response.json()
            rates = {item["quote"]: item["rate"] for item in data}
            rates[base_currency] = 1.0

            _store_cached_rates(base_currency, rates)
            return rates
    except Exception:
        stale_cache = _rates_cache.get(base_currency)
        if stale_cache:
            return stale_cache[0]
        return {base_currency: 1.0}


def convert_currency(
    amount: Decimal,
    from_currency: str,
    base_currency: str,
    rates: Dict[str, float]
) -> Decimal:
    if from_currency == base_currency:
        return amount

    rate = rates.get(from_currency)
    if not rate:
        return Decimal("0")

    return Decimal(str(amount)) / Decimal(str(rate))