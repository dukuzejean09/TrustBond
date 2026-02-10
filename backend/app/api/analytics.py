"""Analytics endpoints — aggregated dashboard statistics."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/overview")
async def get_overview():
    """Dashboard overview: total reports, by status, by category, trust distributions."""
    pass


@router.get("/trends")
async def get_trends():
    """Incident trends over time."""
    pass


@router.get("/device-trust")
async def get_device_trust_stats():
    """Device trust score distribution and trends."""
    pass
