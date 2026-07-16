# Deploying LightAPI

The frontend deploys to Vercel (static). The backend is a container that runs on
any Dockerfile host. This doc describes the current production setup and how to
reproduce or move it.

## Current state (July 2026)

- **Frontend:** Vercel (`lightai-kohl.vercel.app`), auto-deploys on push to `main`.
  `VITE_API_URL` / `VITE_WS_URL` point at the Render backend.
- **Backend:** Render free tier (`lightapi-ufl5.onrender.com`), deployed from the
  [`render.yaml`](../render.yaml) blueprint at the repo root. Auto-deploys on push
  to `main`.

### Free-tier trade-offs

- The backend **spins down after ~15 idle minutes**; the next request takes ~50 s
  while it wakes (the UI shows loading skeletons until then).
- **No persistent disk** — the SQLite DB lives in the container, so user-created
  workspaces and readings are lost on restart/redeploy. The API directory reseeds
  itself instantly from `backend/data/apis_snapshot.json`.

## 1. Backend (Render)

The blueprint does all the work: it builds `backend/Dockerfile`, sets
`ALLOWED_ORIGINS` and `DATABASE_URL`, and health-checks `/api/directory/categories`.

1. Sign in at [dashboard.render.com](https://dashboard.render.com) (GitHub login, no card).
2. **New + → Blueprint** → select this repo → **Deploy**.
3. First build takes ~10–15 min (PyTorch download); later builds are cached.

Verify: `https://<app>.onrender.com/api/directory/categories` returns `{"total": 1573, ...}`.

## 2. Frontend (Vercel)

In the Vercel project → Settings → Environment Variables (Production **and** Preview):

| Variable | Value |
|---|---|
| `VITE_API_URL` | `https://<app>.onrender.com` |
| `VITE_WS_URL` | `wss://<app>.onrender.com` |

Redeploy (env vars only apply to fresh builds). Then verify end-to-end: the
directory loads, and clicking **Monitor** on any API yields a live latency
reading within ~30 s.

## 3. (Optional) Custom domain

Buy a domain from Cloudflare or Porkbun (~$12/yr), add it in Vercel → Domains,
and set the DNS records Vercel provides. Then add the new origin to
`ALLOWED_ORIGINS` in `render.yaml` so CORS accepts it.

## Upgrading off the free tier

When spin-downs or data loss matter, either upgrade the Render service (paid
instance + persistent disk mounted at `/data`) or move to Fly.io — a 512 MB
machine (~$4/mo, needed for PyTorch; 256 MB will OOM) with a volume:

```bash
cd backend
fly launch --no-deploy        # detects the Dockerfile
fly volumes create lightapi_data --size 1
fly secrets set ALLOWED_ORIGINS=https://lightai-kohl.vercel.app \
                DATABASE_URL=sqlite:////data/lightapi.db
# mount the volume at /data in fly.toml, then:
fly deploy
```

Either way, point the Vercel env vars at the new backend URL and redeploy the
frontend.
