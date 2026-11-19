import re
from datetime import date, timedelta
import httpx
from fastapi import HTTPException

GEOCODE = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST = "https://api.open-meteo.com/v1/forecast"
DAILY = "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max"
CURRENT = "temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m"

async def fetch(url, params):
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict) or data.get("error"):
                raise ValueError("Invalid response")
            return data
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(502, "Weather provider is unavailable or returned invalid data. Please retry.") from exc

async def resolve(query: str):
    query = query.strip()
    if not query or len(query) > 200:
        raise HTTPException(422, "Enter a valid location.")
    coordinates = re.fullmatch(r"\s*([+-]?\d+(?:\.\d+)?)\s*,\s*([+-]?\d+(?:\.\d+)?)\s*", query)
    if coordinates:
        lat, lon = map(float, coordinates.groups())
        if not -90 <= lat <= 90 or not -180 <= lon <= 180:
            raise HTTPException(422, "Coordinates must be within latitude -90 to 90 and longitude -180 to 180.")
        return {"name": f"{lat:.4f}, {lon:.4f}", "latitude": lat, "longitude": lon}
    data = await fetch(GEOCODE, {"name": query, "count": 1, "language": "en", "format": "json"})
    results = data.get("results") or []
    if not results:
        raise HTTPException(404, "Location not found. Try a city, postal code, or coordinates.")
    try:
        item = results[0]
        lat, lon = float(item["latitude"]), float(item["longitude"])
        if not -90 <= lat <= 90 or not -180 <= lon <= 180:
            raise ValueError()
        return {"name": ", ".join(str(item[k]) for k in ("name", "admin1", "country") if item.get(k)), "latitude": lat, "longitude": lon}
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        raise HTTPException(502, "Geocoding provider returned invalid data.") from exc

async def weather(place, start=None, end=None):
    params = {"latitude": place["latitude"], "longitude": place["longitude"], "current": CURRENT, "daily": DAILY, "timezone": "auto"}
    if start and end:
        # The forecast endpoint guarantees only the next 16 days. Restrict to UTC
        # today through day 15 conservatively; the provider remains authoritative.
        today = date.today()
        if start < today or end > today + timedelta(days=15):
            raise HTTPException(422, "Date range must be within today and the next 15 days; historical and more distant dates are unavailable.")
        params.update(start_date=start.isoformat(), end_date=end.isoformat())
    else:
        params["forecast_days"] = 5
    data = await fetch(FORECAST, params)
    try:
        current, daily = data["current"], data["daily"]
        for key in CURRENT.split(","):
            if current[key] is None or not isinstance(current[key], (int, float)):
                raise ValueError()
        times = daily["time"]
        if not times or (start and len(times) != (end - start).days + 1) or (not start and len(times) != 5):
            raise ValueError()
        for key in DAILY.split(","):
            if len(daily[key]) != len(times) or any(not isinstance(x, (int, float)) for x in daily[key]):
                raise ValueError()
        return {"location": place, "timezone": data.get("timezone", ""), "current": current, "daily": daily}
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(502, "Weather provider returned incomplete data. Please retry.") from exc
