"""MCP server for currency conversion using Frankfurter API (free, no API key)."""

from mcp.server.fastmcp import FastMCP
import httpx

mcp = FastMCP("currency")


@mcp.tool()
async def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert an amount between two currencies using live exchange rates.

    Args:
        amount: Amount to convert (e.g. 50000).
        from_currency: Source currency code (e.g. INR, USD, SGD).
        to_currency: Target currency code (e.g. SGD, INR, USD).
    """
    from_currency = from_currency.upper().strip()
    to_currency = to_currency.upper().strip()

    url = (
        f"https://api.frankfurter.dev/v1/latest"
        f"?amount={amount}&from={from_currency}&to={to_currency}"
    )

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as e:
        return f"Currency service unavailable: {e}"

    rate = data.get("rates", {}).get(to_currency)
    if rate is None:
        return f"Could not convert {from_currency} to {to_currency}. Check currency codes."

    return (
        f"Currency conversion (via Frankfurter MCP tool):\n"
        f"  {amount:,.2f} {from_currency} = {rate:,.2f} {to_currency}\n"
        f"  Date: {data.get('date', 'unknown')}\n"
        f"  Rate: 1 {from_currency} = {rate / amount:.6f} {to_currency}"
    )


if __name__ == "__main__":
    mcp.run()
