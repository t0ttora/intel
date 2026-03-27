"""Fetch user's active shipments/routes from Supabase for personalization."""
from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class UserShipment:
    """A user's active shipment."""

    code: str
    route: str
    origin: str
    destination: str
    current_status: str
    carrier: str | None = None
    teu: int = 1


async def fetch_user_shipments(user_id: str) -> list[UserShipment]:
    """Fetch active shipments for a user from Supabase.

    Calls the Supabase REST API with the service role key to get
    the user's shipments that are in_transit or pending.
    """
    settings = get_settings()

    url = f"{settings.supabase_url}/rest/v1/shipments"
    headers = {
        "apikey": settings.supabase_service_key,
        "Authorization": f"Bearer {settings.supabase_service_key}",
        "Content-Type": "application/json",
    }
    params = {
        "select": "code,origin,destination,status,carrier,teu",
        "user_id": f"eq.{user_id}",
        "status": "in.in_transit,pending,booked",
        "order": "created_at.desc",
        "limit": "20",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

        shipments: list[UserShipment] = []
        for row in data:
            shipments.append(
                UserShipment(
                    code=row.get("code", ""),
                    route=f"{row.get('origin', '')} → {row.get('destination', '')}",
                    origin=row.get("origin", ""),
                    destination=row.get("destination", ""),
                    current_status=row.get("status", "unknown"),
                    carrier=row.get("carrier"),
                    teu=row.get("teu", 1),
                )
            )

        logger.info(f"Fetched {len(shipments)} active shipments for user {user_id}")
        return shipments

    except httpx.HTTPStatusError as exc:
        logger.warning(f"Supabase HTTP error fetching shipments: {exc.response.status_code}")
        return []
    except httpx.RequestError as exc:
        logger.warning(f"Supabase request error: {exc}")
        return []
    except Exception as exc:
        logger.error(f"Error fetching user shipments: {exc}")
        return []


def match_shipment_to_zone(shipment: UserShipment, affected_zones: list[str]) -> bool:
    """Check if a shipment's route passes through any affected zone."""
    route_text = f"{shipment.origin} {shipment.destination} {shipment.route}".lower()

    # Map zone IDs to location keywords
    zone_to_keywords: dict[str, list[str]] = {
        "suez_canal": ["suez", "red sea", "mediterranean", "rotterdam", "hamburg", "europe"],
        "bab_el_mandeb": ["red sea", "aden", "djibouti", "bab el mandeb"],
        "panama_canal": ["panama", "pacific", "atlantic"],
        "strait_of_malacca": ["malacca", "singapore", "malaysia"],
        "rotterdam": ["rotterdam", "europoort", "netherlands"],
        "shanghai": ["shanghai", "yangshan", "china"],
        "singapore": ["singapore"],
    }

    for zone in affected_zones:
        keywords = zone_to_keywords.get(zone, [zone.replace("_", " ")])
        for keyword in keywords:
            if keyword in route_text:
                return True

    return False
