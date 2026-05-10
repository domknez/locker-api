from __future__ import annotations

from datetime import UTC, datetime

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_parcel_assigns_slot(client: AsyncClient) -> None:
    locker = await client.post(
        "/api/v1/lockers",
        json={"address": "A", "slots": {"M": 1}},
    )
    assert locker.status_code == 201

    parcel = await client.post(
        "/api/v1/parcels",
        json={"sender": "Alice", "receiver": "Bob", "size": "M"},
    )
    assert parcel.status_code == 201
    body = parcel.json()
    assert body["state"] == "ASSIGNED"
    assert body["slot_id"] is not None


@pytest.mark.asyncio
async def test_no_slot_returns_409(client: AsyncClient) -> None:
    await client.post("/api/v1/lockers", json={"address": "A", "slots": {"S": 1}})

    response = await client.post(
        "/api/v1/parcels",
        json={"sender": "a", "receiver": "b", "size": "XL"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


@pytest.mark.asyncio
async def test_slot_freed_after_pickup(client: AsyncClient) -> None:
    await client.post("/api/v1/lockers", json={"address": "A", "slots": {"M": 1}})

    first = await client.post(
        "/api/v1/parcels",
        json={"sender": "a", "receiver": "b", "size": "M"},
    )
    assert first.status_code == 201
    pid = first.json()["id"]

    second = await client.post(
        "/api/v1/parcels",
        json={"sender": "x", "receiver": "y", "size": "M"},
    )
    assert second.status_code == 409

    await client.post(
        f"/api/v1/parcels/{pid}/transition",
        json={"target_state": "IN_LOCKER"},
    )
    picked = await client.post(
        f"/api/v1/parcels/{pid}/transition",
        json={"target_state": "PICKED_UP"},
    )
    assert picked.status_code == 200

    third = await client.post(
        "/api/v1/parcels",
        json={"sender": "x", "receiver": "y", "size": "M"},
    )
    assert third.status_code == 201


@pytest.mark.asyncio
async def test_invalid_state_transition(client: AsyncClient) -> None:
    await client.post("/api/v1/lockers", json={"address": "A", "slots": {"M": 1}})
    parcel = await client.post(
        "/api/v1/parcels",
        json={"sender": "a", "receiver": "b", "size": "M"},
    )
    pid = parcel.json()["id"]

    response = await client.post(
        f"/api/v1/parcels/{pid}/transition",
        json={"target_state": "CREATED"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_naive_datetime_rejected(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/parcels",
        json={
            "sender": "a",
            "receiver": "b",
            "size": "M",
            "submitted_at": "2026-01-01T10:00:00",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_timezone_normalized_to_utc(client: AsyncClient) -> None:
    await client.post("/api/v1/lockers", json={"address": "A", "slots": {"M": 1}})

    response = await client.post(
        "/api/v1/parcels",
        json={
            "sender": "a",
            "receiver": "b",
            "size": "M",
            "submitted_at": "2026-01-01T10:00:00+02:00",
        },
    )
    assert response.status_code == 201
    submitted_at = datetime.fromisoformat(
        response.json()["submitted_at"].replace("Z", "+00:00")
    )
    assert submitted_at == datetime(2026, 1, 1, 8, 0, 0, tzinfo=UTC)
