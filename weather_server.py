"""MCP server for weather forecasts using Open-Meteo (free, no API key)."""

from mcp.server.fastmcp import FastMCP
import httpx

mcp = FastMCP("weather")

# Singapore coordinates
CITY_COORDS = {
    "singapore": (1.3521, 103.8198),
}

WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def _weather_desc(code: int) -> str:
    return WEATHER_CODES.get(code, f"Code {code}")


@mcp.tool()
async def get_weather_forecast(city: str = "Singapore", days: int = 3) -> str:
    """Get weather forecast for a city. Use for current conditions and multi-day forecasts.

    Args:
        city: City name (default Singapore).
        days: Number of forecast days (1-7, default 3).
    """
    days = max(1, min(7, days))
    coords = CITY_COORDS.get(city.lower(), CITY_COORDS["singapore"])
    lat, lon = coords

    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,relative_humidity_2m,precipitation,weathercode"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode"
        f"&forecast_days={days}&timezone=Asia/Singapore"
    )

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as e:
        return f"Weather service unavailable: {e}"

    current = data.get("current", {})
    daily = data.get("daily", {})

    lines = [f"Weather forecast for {city} (via Open-Meteo MCP tool):", ""]
    lines.append("Current conditions:")
    lines.append(f"  Temperature: {current.get('temperature_2m', 'N/A')}°C")
    lines.append(f"  Humidity: {current.get('relative_humidity_2m', 'N/A')}%")
    lines.append(f"  Precipitation: {current.get('precipitation', 0)} mm")
    lines.append(f"  Conditions: {_weather_desc(current.get('weathercode', 0))}")
    lines.append("")
    lines.append(f"{days}-day forecast:")

    dates = daily.get("time", [])
    for i, date in enumerate(dates[:days]):
        max_t = daily["temperature_2m_max"][i]
        min_t = daily["temperature_2m_min"][i]
        rain = daily["precipitation_sum"][i]
        code = daily["weathercode"][i]
        rain_note = " (rain expected)" if rain > 1 else ""
        lines.append(
            f"  {date}: {min_t}°C - {max_t}°C, "
            f"{_weather_desc(code)}, rain {rain} mm{rain_note}"
        )

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
