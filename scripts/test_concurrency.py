"""
Load testing: Fires n simultaneous booking requests at the SAME slot and confirms
exactly one succeeds (201) while the rest get a clean 409 — proving the
row lock + partial unique index actually prevent double-booking under
real concurrency, not just in sequential testing.
"""

import asyncio
import httpx

BASE_URL = "http://localhost:8000"
CONCURRENT_REQUESTS = 100


async def attempt_booking(client: httpx.AsyncClient, slot_id: str, customer_num: int):
    response = await client.post(
        f"{BASE_URL}/bookings",
        json={
            "slot_id": slot_id,
            "customer_name": f"Customer {customer_num}",
            "customer_email": f"customer{customer_num}@example.com",
        },
    )
    return response.status_code


async def main():
    async with httpx.AsyncClient(
        base_url=BASE_URL,
        timeout=10.0,
    ) as client:
        # Setup: create a provider and one slot to race for
        provider_resp = await client.post(
            "/providers", json={"name": "Dr. Race Condition"}
        )
        provider_id = provider_resp.json()["id"]

        from datetime import datetime, timedelta, UTC

        start = datetime.now(UTC) + timedelta(days=1)
        slot_resp = await client.post(
            "/slots",
            json={
                "provider_id": provider_id,
                "start_time": start.isoformat(),
                "end_time": (start + timedelta(minutes=30)).isoformat(),
            },
        )
        slot_id = slot_resp.json()["id"]
        print(f"Racing {CONCURRENT_REQUESTS} requests for slot {slot_id}...\n")

        # The actual test: fire all requests at once via asyncio.gather,
        # not one after another — this is what makes it a real race
        # instead of a sequential simulation of one.
        results = await asyncio.gather(
            *[attempt_booking(client, slot_id, i) for i in range(CONCURRENT_REQUESTS)]
        )

        successes = results.count(201)
        conflicts = results.count(409)
        other = len(results) - successes - conflicts

        print(f"Results: {results}")
        print(f"  201 (booked):    {successes}")
        print(f"  409 (conflict):  {conflicts}")
        print(f"  other:           {other}")

        assert (
            successes == 1
        ), f"Expected exactly 1 success, got {successes} — DOUBLE-BOOKING BUG"
        assert (
            conflicts == CONCURRENT_REQUESTS - 1
        ), f"Expected {CONCURRENT_REQUESTS - 1} conflicts, got {conflicts}"
        print("\n✅ PASS — exactly one booking succeeded under concurrent load.")


if __name__ == "__main__":
    asyncio.run(main())
