from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_locker(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/lockers",
        json={"address": "Marienplatz, Munich", "slots": {"M": 2, "L": 1}},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["address"] == "Marienplatz, Munich"
    assert body["latitude"] == pytest.approx(48.1374, abs=0.01)
    assert len(body["slots"]) == 3
    sizes = sorted(s["size"] for s in body["slots"])
    assert sizes == ["L", "M", "M"]


@pytest.mark.asyncio
async def test_create_requires_auth(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/lockers",
        json={"address": "x", "slots": {"S": 1}},
        headers={"Authorization": ""},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_returns_404_for_unknown(client: AsyncClient) -> None:
    response = await client.get("/api/v1/lockers/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_replaces_slots(client: AsyncClient) -> None:
    created = await client.post(
        "/api/v1/lockers",
        json={"address": "A", "slots": {"S": 1}},
    )
    locker_id = created.json()["id"]

    updated = await client.put(
        f"/api/v1/lockers/{locker_id}",
        json={"slots": {"L": 2}},
    )
    assert updated.status_code == 200
    sizes = [s["size"] for s in updated.json()["slots"]]
    assert sizes == ["L", "L"]


@pytest.mark.asyncio
async def test_delete_locker(client: AsyncClient) -> None:
    created = await client.post(
        "/api/v1/lockers",
        json={"address": "A", "slots": {"S": 1}},
    )
    locker_id = created.json()["id"]

    deleted = await client.delete(f"/api/v1/lockers/{locker_id}")
    assert deleted.status_code == 204

    fetched = await client.get(f"/api/v1/lockers/{locker_id}")
    assert fetched.status_code == 404


@pytest.mark.asyncio
async def test_list_lockers_pagination(client: AsyncClient) -> None:
    for i in range(3):
        await client.post(
            "/api/v1/lockers",
            json={"address": f"Addr {i}", "slots": {"S": 1}},
        )

    response = await client.get("/api/v1/lockers", params={"limit": 2})
    assert response.status_code == 200
    assert len(response.json()) == 2
