# Bruno Collection

API requests for the Parcel Locker service. Edit + run with [Bruno](https://www.usebruno.com/).

## Usage

1. Open Bruno → **Open Collection** → select this `bruno/` directory.
2. Top-right environment switcher → pick **local**.
3. Run requests individually or use **Run Collection** for a full smoke flow.

## Environments

- `environments/local.bru` — `baseUrl=http://localhost:8000`, `token=dev-secret-change-me`. Adjust if your `.env` differs.

## Flow

Suggested order for an end-to-end run:

1. **Health → Liveness, Readiness**
2. **Lockers → Create Locker** (stores `lastLockerId` in collection vars)
3. **Lockers → Get / List / Nearest / Update**
4. **Parcels → Create Parcel** (stores `lastParcelId`)
5. **Parcels → Transition → IN_LOCKER → PICKED_UP**
6. **Parcels → Transition → Invalid** (asserts 409)
7. **Lockers → Delete Locker**

Negative cases included: unauthorized create, naive datetime (422), no-slot conflict (409), invalid state transition (409).
