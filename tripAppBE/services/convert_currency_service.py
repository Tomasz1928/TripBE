from decimal import Decimal, ROUND_HALF_UP

import requests


def fetch_currency_rates(from_currency):
    """
    Fetch exchange rates for `from_currency` and return a flat dictionary
    with 'date' and currency rates.
    """
    url = f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/{from_currency.lower()}.json"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        rate_date = data.get("date")
        base_rates = next((v for k, v in data.items() if k != "date"), {})
        flat_rates = {"date": rate_date, **base_rates}

        return flat_rates

    except Exception as e:
        print(f"Error fetching rates for {from_currency}: {e}")
        return {"date": None}  # fallback


def convert_currency(value, from_currency, to_currency, rates_dict):
    """
    Convert `value` from `from_currency` to `to_currency` using `rates_dict`.
    """
    rate = rates_dict.get(to_currency.lower())
    if rate is None:
        raise ValueError(f"Currency '{to_currency}' not found in rates for '{from_currency}'")
    converted_value = (value * Decimal(rate)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return converted_value


def update_description(description, value, calculated_value, from_currency, to_currency, rates_dict):
    """
    Append conversion info to description if provided.
    """
    if description:
        rate = rates_dict.get(to_currency.lower())
        rate_date = rates_dict.get("date")
        return (
            f"{description} | Automatic conversion of {value} {from_currency} "
            f"to {calculated_value} {to_currency} at rate {rate} (date: {rate_date})"
        )
        return description