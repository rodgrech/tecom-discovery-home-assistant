"""Async client for the local Tecom Discovery web API."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable
import logging
from typing import Any

from aiohttp import ClientError, ClientResponse, ClientSession, ClientTimeout

from .const import KIND_AREA, KIND_INPUT, KIND_RELAY
from .models import DiscoveryEntityState

_LOGGER = logging.getLogger(__name__)


class DiscoveryError(Exception):
    """Base API error."""


class DiscoveryAuthenticationError(DiscoveryError):
    """Authentication failed."""


class DiscoveryConnectionError(DiscoveryError):
    """The panel could not be reached."""


class DiscoveryApiError(DiscoveryError):
    """The panel returned an API error."""


class DiscoveryApi:
    """Client for a Discovery panel's onboard REST API."""

    def __init__(
        self,
        session: ClientSession,
        host: str,
        email: str,
        password: str,
        verify_ssl: bool,
    ) -> None:
        host = host.strip().rstrip("/")
        if not host.startswith(("http://", "https://")):
            host = f"https://{host}"
        self._base_url = f"{host}/api"
        self._session = session
        self._email = email
        self._password = password
        self._verify_ssl = verify_ssl
        self._access_token: str | None = None
        self._auth_lock = asyncio.Lock()

    @property
    def base_url(self) -> str:
        """Return the API base URL."""

        return self._base_url

    async def async_login(self, *, force: bool = False) -> None:
        """Authenticate and retain the bearer token."""

        async with self._auth_lock:
            if self._access_token and not force:
                return
            response = await self._raw_post(
                "auth/sign-in",
                {"email": self._email.strip(), "password": self._password},
                authenticated=False,
            )
            data = _unwrap(response)
            token = _first_value(data, ("accessToken", "access_token", "token"))
            if not isinstance(token, str) or not token:
                raise DiscoveryAuthenticationError(
                    "The panel accepted the request but did not return an access token"
                )
            self._access_token = token

    async def async_panel_info(self) -> dict[str, Any]:
        """Fetch the public panel identity."""

        response = await self._raw_post("panel/getinfo", {}, authenticated=False)
        data = _unwrap(response)
        return data if isinstance(data, dict) else {}

    async def async_recall_states(
        self, kind: str, count: int
    ) -> list[DiscoveryEntityState]:
        """Fetch and normalize states, in modest batches."""

        if count <= 0:
            return []

        endpoint, payload_key = {
            KIND_INPUT: ("recallInputStatus", "entities"),
            KIND_AREA: ("recallAreaStatus", "entities"),
            KIND_RELAY: ("recallRelayStatus", "entities"),
        }[kind]

        states: list[DiscoveryEntityState] = []
        numbers = range(1, count + 1)
        for batch in _chunks(numbers, 32):
            payload: dict[str, Any] = {payload_key: batch}
            if kind in (KIND_INPUT, KIND_RELAY):
                payload["name"] = True
            response = await self.async_post(endpoint, payload)
            states.extend(normalize_states(response, kind, batch))
        return states

    async def async_post(self, endpoint: str, payload: Any) -> Any:
        """Make an authenticated API request, refreshing once on HTTP 401."""

        await self.async_login()
        try:
            return await self._raw_post(endpoint, payload, authenticated=True)
        except DiscoveryAuthenticationError:
            await self.async_login(force=True)
            return await self._raw_post(endpoint, payload, authenticated=True)

    async def _raw_post(
        self, endpoint: str, payload: Any, *, authenticated: bool
    ) -> Any:
        headers = {"Content-Type": "application/json"}
        if authenticated and self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"

        url = f"{self._base_url}/{endpoint.lstrip('/')}"
        try:
            async with self._session.post(
                url,
                json=payload,
                headers=headers,
                ssl=self._verify_ssl,
                timeout=ClientTimeout(total=15),
            ) as response:
                return await self._decode_response(response, authenticated)
        except (ClientError, TimeoutError, asyncio.TimeoutError) as err:
            raise DiscoveryConnectionError(f"Unable to contact {url}: {err}") from err

    async def _decode_response(
        self, response: ClientResponse, authenticated: bool
    ) -> Any:
        if response.status in (401, 403):
            if authenticated:
                self._access_token = None
            raise DiscoveryAuthenticationError("Invalid credentials or insufficient access")

        try:
            body = await response.json(content_type=None)
        except (ValueError, TypeError) as err:
            text = await response.text()
            raise DiscoveryApiError(
                f"Unexpected response from panel ({response.status}): {text[:200]}"
            ) from err

        if response.status >= 400:
            raise DiscoveryApiError(_error_message(body, response.status))
        if isinstance(body, dict) and body.get("success") is False:
            raise DiscoveryApiError(_error_message(body, response.status))
        return body


def normalize_states(
    response: Any, kind: str, requested_numbers: list[int]
) -> list[DiscoveryEntityState]:
    """Normalize the varying state response shapes used across firmware releases."""

    data = _unwrap(response)
    items = _find_item_list(data)

    if not items and isinstance(data, dict):
        # Some firmware returns a number-keyed map.
        numeric_items: list[dict[str, Any]] = []
        for key, value in data.items():
            if str(key).isdigit():
                item = value.copy() if isinstance(value, dict) else {"state": value}
                item.setdefault("number", int(key))
                numeric_items.append(item)
        items = numeric_items

    result: list[DiscoveryEntityState] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            item = {"state": item}
        fallback = requested_numbers[index] if index < len(requested_numbers) else index + 1
        number = _as_int(
            _first_value(
                item,
                (
                    "number",
                    "entity",
                    "entityNumber",
                    "input",
                    "inputNumber",
                    "area",
                    "areaNumber",
                    "relay",
                    "relayNumber",
                    "id",
                ),
            ),
            fallback,
        )
        name = _first_value(
            item,
            (
                "name",
                "entityName",
                "inputName",
                "areaName",
                "relayName",
                "description",
                "label",
            ),
        )
        state_value = _first_value(
            item,
            (
                "alarmStatus",
                "active",
                "isActive",
                "status",
                "stateSTR",
                "statusSTR",
                "inputState",
                "areaState",
                "relayState",
                "state",
                "value",
            ),
        )
        state, active = _normalized_state(item, state_value, kind)
        result.append(
            DiscoveryEntityState(
                number=number,
                name=str(name or f"{kind.title()} {number}"),
                kind=kind,
                state=state,
                active=active,
                raw=item,
            )
        )

    # Preserve requested entities even if a firmware omits inactive entries.
    present = {item.number for item in result}
    for number in requested_numbers:
        if number not in present:
            result.append(
                DiscoveryEntityState(
                    number=number,
                    name=f"{kind.title()} {number}",
                    kind=kind,
                    state="unknown",
                    active=None,
                    raw={},
                )
            )
    return sorted(result, key=lambda item: item.number)


def _unwrap(value: Any) -> Any:
    """Unwrap common Discovery response envelopes."""

    while isinstance(value, dict):
        next_value = None
        for key in ("data", "retval", "result"):
            if key in value and value[key] is not value:
                next_value = value[key]
                break
        if next_value is None:
            break
        value = next_value
    return value


def _find_item_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in (
            "entities",
            "states",
            "status",
            "inputs",
            "areas",
            "relays",
            "items",
            "records",
        ):
            candidate = value.get(key)
            if isinstance(candidate, list):
                return candidate
        for candidate in value.values():
            if isinstance(candidate, list) and (
                not candidate or isinstance(candidate[0], (dict, str, int, bool))
            ):
                return candidate
    return []


def _first_value(mapping: Any, keys: tuple[str, ...]) -> Any:
    if not isinstance(mapping, dict):
        return None
    lower = {str(key).lower(): value for key, value in mapping.items()}
    for key in keys:
        if key in mapping:
            return mapping[key]
        if key.lower() in lower:
            return lower[key.lower()]
    return None


def _state_text(value: Any) -> str:
    if isinstance(value, bool):
        return "active" if value else "normal"
    if value is None:
        return "unknown"
    if isinstance(value, (int, float)):
        return str(value)
    return str(value).strip().lower().replace(" ", "_")


def _state_active(value: Any, state: str, kind: str) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)

    inactive = {
        "normal",
        "sealed",
        "secure",
        "disarmed",
        "off",
        "closed",
        "inactive",
        "reset",
        "0",
    }
    active = {
        "active",
        "alarm",
        "open",
        "unsealed",
        "on",
        "armed",
        "set",
        "secure_alarm",
        "1",
    }
    if state in inactive:
        return False
    if state in active:
        return True
    if kind == KIND_AREA:
        if any(word in state for word in ("armed", "secure", "alarm")):
            return True
        if any(word in state for word in ("disarm", "access")):
            return False
    return None


def _normalized_state(
    item: dict[str, Any], value: Any, kind: str
) -> tuple[str, bool | None]:
    """Derive a canonical state from the real Discovery status fields."""

    if kind == KIND_AREA:
        if bool(item.get("alarmsActive") or item.get("localAlarmsActive")):
            return "alarm", True
        if bool(item.get("entryTimerActive")):
            return "entry_delay", True
        if bool(item.get("exitTimerActive")):
            return "exit_delay", True
        if bool(item.get("areaStay")):
            return "armed_stay", True
        if bool(item.get("areaSecured")):
            return "armed_away", True
        if item.get("responseStatus") is True:
            return "disarmed", False

    state = _state_text(value)
    return state, _state_active(value, state, kind)


def _chunks(values: Iterable[int], size: int) -> Iterable[list[int]]:
    batch: list[int] = []
    for value in values:
        batch.append(value)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch


def _as_int(value: Any, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _error_message(body: Any, status: int) -> str:
    if isinstance(body, dict):
        message = body.get("message") or body.get("error")
        if isinstance(message, list):
            message = "; ".join(str(part) for part in message)
        if isinstance(message, dict):
            message = message.get("message") or str(message)
        if message:
            return str(message)
    return f"Discovery API returned HTTP {status}"
