from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class SaltEdgeConfig:
    base_url: str
    app_id: str
    secret: str


class SaltEdgeError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None, payload: Any | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class SaltEdgeClient:
    def __init__(self, config: SaltEdgeConfig):
        self._config = config

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "App-id": self._config.app_id,
            "Secret": self._config.secret,
        }

    def _url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        if path.startswith("/api/"):
            return f"https://www.saltedge.com{path}"
        return f"{self._config.base_url.rstrip('/')}/{path.lstrip('/')}"

    def _raise(self, response: httpx.Response) -> None:
        payload: Any | None = None
        try:
            payload = response.json()
        except Exception:
            payload = response.text
        raise SaltEdgeError(
            f"Salt Edge API error ({response.status_code})",
            status_code=response.status_code,
            payload=payload,
        )

    async def create_customer(self, *, identifier: str) -> str:
        # Docs: Customers endpoint returns data.id (customer_id)
        payload = {"data": {"identifier": identifier}}
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(self._url("/customers"), headers=self._headers(), json=payload)
        if resp.status_code >= 400:
            self._raise(resp)
        data = resp.json().get("data") or {}
        customer_id = data.get("id")
        if not customer_id:
            raise SaltEdgeError("Salt Edge customer id missing", payload=resp.json())
        return str(customer_id)

    async def create_connect_url(
        self,
        *,
        customer_id: str,
        return_to: str,
        from_date: str | None = None,
        scopes: list[str] | None = None,
    ) -> str:
        if scopes is None:
            scopes = ["account_details", "transactions_details"]

        consent: dict[str, Any] = {"scopes": scopes}
        if from_date:
            consent["from_date"] = from_date

        payload = {
            "data": {
                "customer_id": customer_id,
                "consent": consent,
                "attempt": {"return_to": return_to},
            }
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(self._url("/connections/connect"), headers=self._headers(), json=payload)
        if resp.status_code >= 400:
            self._raise(resp)
        data = resp.json().get("data") or {}
        connect_url = data.get("connect_url")
        if not connect_url:
            raise SaltEdgeError("Salt Edge connect_url missing", payload=resp.json())
        return str(connect_url)

    async def list_connections(self, *, customer_id: str) -> list[dict[str, Any]]:
        params = {"customer_id": customer_id}
        items: list[dict[str, Any]] = []
        async with httpx.AsyncClient(timeout=30) as client:
            url = self._url("/connections")
            while True:
                resp = await client.get(url, headers=self._headers(), params=params)
                if resp.status_code >= 400:
                    self._raise(resp)
                body = resp.json()
                items.extend(body.get("data") or [])
                meta = body.get("meta") or {}
                next_page = meta.get("next_page")
                if not next_page:
                    break
                url = self._url(next_page)
                params = None
        return items

    async def list_accounts(self, *, connection_id: str) -> list[dict[str, Any]]:
        params = {"connection_id": connection_id}
        items: list[dict[str, Any]] = []
        async with httpx.AsyncClient(timeout=30) as client:
            url = self._url("/accounts")
            while True:
                resp = await client.get(url, headers=self._headers(), params=params)
                if resp.status_code >= 400:
                    self._raise(resp)
                body = resp.json()
                items.extend(body.get("data") or [])
                meta = body.get("meta") or {}
                next_page = meta.get("next_page")
                if not next_page:
                    break
                url = self._url(next_page)
                params = None
        return items

    async def list_transactions(self, *, connection_id: str, account_id: str) -> list[dict[str, Any]]:
        params = {"connection_id": connection_id, "account_id": account_id}
        items: list[dict[str, Any]] = []
        async with httpx.AsyncClient(timeout=30) as client:
            url = self._url("/transactions")
            while True:
                resp = await client.get(url, headers=self._headers(), params=params)
                if resp.status_code >= 400:
                    self._raise(resp)
                body = resp.json()
                items.extend(body.get("data") or [])
                meta = body.get("meta") or {}
                next_page = meta.get("next_page")
                if not next_page:
                    break
                url = self._url(next_page)
                params = None
        return items

