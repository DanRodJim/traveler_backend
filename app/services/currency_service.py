from decimal import Decimal
from typing import Dict

import httpx


async def get_exchange_rates(base_currency: str) -> Dict[str, float]:
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
            return rates
    except Exception:
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