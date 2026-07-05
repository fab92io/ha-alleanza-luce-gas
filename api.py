from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta

import aiohttp

from .const import (
    BASE_URL,
    BILLING_ENDPOINT,
    GRAPHQL_ENDPOINT,
    LOGIN_ENDPOINT,
    PROMO_ENDPOINT,
    VOUCHERS_ENDPOINT,
)

_LOGGER = logging.getLogger(__name__)


class AlleanzaLuceGasAPI:
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session
        self._session_token: str | None = None
        self._refresh_token: str | None = None
        self._user_id: str | None = None
        self._user_details_id: str | None = None
        self._customer_code: str | None = None
        self._friend_code: str | None = None

    async def login(self, username: str, password: str) -> dict:
        payload = {"username": username, "password": password}
        headers = {
            "Content-Type": "application/json",
            "Origin": "https://areaclienti.accendilucegas.it",
            "Referer": "https://areaclienti.accendilucegas.it/",
        }
        async with self._session.post(
            LOGIN_ENDPOINT, json=payload, headers=headers
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()

        self._session_token = data["sessionToken"]
        self._refresh_token = data["refreshToken"]
        self._user_id = data["user"]["id"]
        self._user_details_id = data["user"]["userDetails"]["id"]
        return data

    def _get_auth_headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._session_token}",
            "Origin": "https://areaclienti.accendilucegas.it",
            "Referer": "https://areaclienti.accendilucegas.it/",
        }

    async def _graphql_query(self, query: str, variables: dict | None = None) -> dict:
        payload = {"query": query}
        if variables is not None:
            payload["variables"] = json.dumps(variables)
        async with self._session.post(
            GRAPHQL_ENDPOINT, json=payload, headers=self._get_auth_headers()
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
        if "errors" in data:
            raise Exception(f"GraphQL error: {data['errors']}")
        return data["data"]

    async def fetch_customer_data(self) -> dict:
        query = """
        query ($id: ID!) {
          allCustomers (where: {id: $id }) {
            id,
            externalId,
            name,
            surname,
            fiscalCode,
            customerId,
            birthplace,
            birthday,
            phone,
            communicationEmailAddress,
            residences {id, country, city, province, address, civicNumber, postalCode},
            supplyCode {id},
            friendCode
          }
        }
        """
        variables = {"id": self._user_details_id}
        result = await self._graphql_query(query, variables)
        customer = result["allCustomers"][0]
        self._customer_code = customer["customerId"]
        self._friend_code = customer.get("friendCode")
        return customer

    async def fetch_supplies(self) -> list:
        query = """
        query ($customerId: String) {
          allSupplies (where: {customerId: $customerId }) {
            id,
            supplyCode,
            supplyType,
            pod,
            pdr,
            supplyStatus,
            committedPower,
            meterNumber,
            availablePower,
            meterLocationAddress,
            supplyLocationAddress,
            contractNumber,
            billingFrequency,
            name
          }
        }
        """
        if not self._customer_code:
            await self.fetch_customer_data()
        variables = {"customerId": self._customer_code}
        result = await self._graphql_query(query, variables)
        return result["allSupplies"]

    async def fetch_billing_details(self) -> list:
        if not self._customer_code:
            await self.fetch_customer_data()
        payload = {
            "customerCode": self._customer_code,
            "pageNumber": 0,
            "pageSize": 1,
            "sortColumnName": "DOCTES_ANNO_DOC",
            "sortDirection": "DESC",
        }
        async with self._session.post(
            BILLING_ENDPOINT, json=payload, headers=self._get_auth_headers()
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
        return data

    async def fetch_all_data(self) -> dict:
        customer = await self.fetch_customer_data()
        supplies = await self.fetch_supplies()
        bills = await self.fetch_billing_details()
        return {
            "customer": customer,
            "supplies": supplies,
            "latest_bill": bills[0] if bills else None,
        }
