# Deploying LightAPI

The frontend deploys to Vercel (static). The backend is a container that runs on
any Dockerfile host. This doc walks the full path to a live production instance.

## Current state

- **Frontend:** deployed on Vercel (`lightai-kohl.vercel.app`), auto-deploys on push to `main`.
- **Backend:** not yet hosted. Until it is, the live site shows "backend unreachable."

## 1. Deploy the backend (Fly.io)

Fly runs the `backend/Dockerfile` directly. A 512 MB machine (needed for PyTorch)
is ~$3.88/mo.

```bash
brew install flyctl
fly auth login            # or: fly auth signup  (card required for verification)

cd backend
fly launch --no-deploy    # detects the Dockerfile; creates fly.toml
```

During `fly launch`:
- **App name:** e.g. `lightapi`
- **Region:** closest to you
- **Postgres / Redis / Upstash:** decline all (LightAPI uses SQLite)
- **Deploy now:** no (we set the machine size + volume first)

Then configure:

```bash
# Persistent volume so the SQLite DB + trained models survive restarts
fly volumes create lightapi_data --size 1 --region <your-region>

# Environment
fly secrets set ALLOWED_ORIGINS=https://lightai-kohl.vercel.app
fly secrets set DATABASE_URL=sqlite:////data/lightapi.db
# Optional: require an API key on the SDK ingest endpoint
# fly secrets set LIGHTAI_API_KEY=<generate-a-random-string>
```

Edit `fly.toml`:
- Mount the volume at `/data`:
  ```toml
  [[mounts]]
    source = "lightapi_data"
    destination = "/data"
  ```
- Ensure `[[vm]]` memory is `512` MB (256 will OOM on torch).
- Internal port should be `8000` (the Dockerfile listens on `$PORT`, Fly sets it).

Deploy:

```bash
fly deploy
fly open        # opens https://<app>.fly.dev
```

Verify: `https://<app>.fly.dev/api/directory/categories` returns `{"total": 1573, ...}`.

## 2. Point the frontend at the backend (Vercel)

In the Vercel project settings → Environment Variables, set:

| Variable | Value |
|---|---|
| `VITE_API_URL` | `https://<app>.fly.dev` |
| `VITE_WS_URL` | `wss://<app>.fly.dev` |

Then redeploy the frontend (push any commit, or "Redeploy" in the Vercel dashboard).

## 3. Verify end-to-end

- Open the site → the directory loads.
- Click **Monitor** on any API → it appears on the dashboard and gets a live latency reading within ~30s.

## 4. (Optional) Custom domain

Buy a domain (`lightapi.dev` / `.app`) from Cloudflare or Porkbun (~$12/yr), add it
in Vercel → Domains, and set the DNS records Vercel provides. Do this only after the
deploy above works end-to-end.

## Notes

- The Dockerfile has not been built locally (no Docker in the dev env). Fly's build
  is the first real build — if it errors, the log will say why (usually a missing
  system lib for torch; the CPU wheel used here avoids CUDA).
- The API directory seeds instantly from `backend/data/apis_snapshot.json` and
  refreshes from GitHub daily.
