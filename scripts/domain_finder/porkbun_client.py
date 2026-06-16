"""Thin Porkbun API v3 client."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import httpx

BASE_URL = "https://api.porkbun.com/api/json/v3"
CHECK_DOMAIN_INTERVAL_SECONDS = 10.5


@dataclass(frozen=True)
class DomainCheckResult:
    domain: str
    available: bool
    price_usd: float | None
    premium: bool
    listing_type: str | None
    raw: dict[str, Any]


@dataclass(frozen=True)
class MarketplaceListing:
    domain: str
    tld: str
    sld: str
    sld_length: int
    price_usd: float
    create_date: str


class PorkbunClient:
    def __init__(
        self,
        api_key: str,
        secret_key: str,
        *,
        timeout: float = 60.0,
        check_interval: float = CHECK_DOMAIN_INTERVAL_SECONDS,
    ) -> None:
        self._auth = {"apikey": api_key, "secretapikey": secret_key}
        self._timeout = timeout
        self._check_interval = check_interval
        self._last_check_at = 0.0

    def ping(self) -> dict[str, Any]:
        return self._post("/ping")

    def get_com_registration_price(self) -> float:
        data = self._post("/pricing/get", auth=False)
        pricing = data.get("pricing", {}).get("com", {})
        return float(pricing.get("registration", 0))

    def check_domain(self, domain: str) -> DomainCheckResult:
        self._wait_for_check_slot()
        data = self._post(f"/domain/checkDomain/{domain}")
        limits = data.get("limits") or {}
        ttl = limits.get("TTL")
        if isinstance(ttl, (int, float)) and ttl > 0:
            self._check_interval = max(self._check_interval, float(ttl) + 0.5)
        response = data.get("response", {})
        price_raw = response.get("price")
        return DomainCheckResult(
            domain=domain,
            available=response.get("avail") == "yes",
            price_usd=float(price_raw) if price_raw is not None else None,
            premium=response.get("premium") == "yes",
            listing_type=response.get("type"),
            raw=response,
        )

    def list_marketplace(
        self,
        *,
        tlds: list[str] | None = None,
        query: str | None = None,
        sld_length_min: int | None = None,
        sld_length_max: int | None = None,
        sort_name: str | None = None,
        sort_direction: str | None = None,
        start: int = 0,
        limit: int = 1000,
    ) -> list[MarketplaceListing]:
        body: dict[str, Any] = {**self._auth, "start": start, "limit": limit}
        if tlds:
            body["tlds"] = tlds
        if query:
            body["query"] = query
        if sld_length_min is not None:
            body["sldLengthMin"] = sld_length_min
        if sld_length_max is not None:
            body["sldLengthMax"] = sld_length_max
        if sort_name:
            body["sortName"] = sort_name
        if sort_direction:
            body["sortDirection"] = sort_direction

        data = self._post("/marketplace/getAll", json_body=body)
        listings: list[MarketplaceListing] = []
        for item in data.get("domains", []):
            domain = item["domain"]
            sld = domain.split(".", 1)[0]
            listings.append(
                MarketplaceListing(
                    domain=domain,
                    tld=item.get("tld", "com"),
                    sld=sld,
                    sld_length=int(item.get("sld_length", len(sld))),
                    price_usd=float(item["price"]),
                    create_date=str(item.get("create_date", "")),
                )
            )
        return listings

    def _wait_for_check_slot(self) -> None:
        elapsed = time.monotonic() - self._last_check_at
        if elapsed < self._check_interval:
            time.sleep(self._check_interval - elapsed)
        self._last_check_at = time.monotonic()

    def _post(
        self,
        path: str,
        *,
        auth: bool = True,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = dict(json_body or {})
        if auth:
            payload.update(self._auth)
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(f"{BASE_URL}{path}", json=payload)
        try:
            data = response.json()
        except ValueError:
            response.raise_for_status()
            raise RuntimeError(f"Non-JSON response from Porkbun ({response.status_code})")

        if response.status_code >= 400 and data.get("status") != "SUCCESS":
            message = data.get("message", f"HTTP {response.status_code}")
            raise RuntimeError(message)

        if data.get("status") != "SUCCESS":
            message = data.get("message", "Unknown Porkbun API error")
            raise RuntimeError(message)
        return data
