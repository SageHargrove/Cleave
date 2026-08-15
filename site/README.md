# cleavehq.com

The marketing site. A single self-contained `index.html` with no build step, no
external requests, and no analytics.

## Deploy (Cloudflare Workers static assets)

Cloudflare retired the standalone Pages creation flow, so this deploys as a
**static-asset Worker**. [`wrangler.jsonc`](../wrangler.jsonc) in the repo root
does the work: it points at `./site`, and declares no `main` script because
nothing here runs server-side.

1. Cloudflare dashboard → **Compute (Workers) → Create → Import a repository**,
   and pick the `cleave` repo.
2. Settings:
   - **Project name:** `cleave`, matching `name` in `wrangler.jsonc`
   - **Build command:** *(empty)*
   - **Deploy command:** `npx wrangler deploy`
   - **Root directory:** *(leave blank)* — `wrangler.jsonc` already points at
     `site/`, so setting this too would double up the path
3. Deploy, confirm the `*.workers.dev` URL serves the site.
4. Worker → **Settings → Domains & Routes → Add → Custom domain**, add
   `cleavehq.com`, then repeat for `www.cleavehq.com`. DNS and TLS are
   automatic, since the zone is already on Cloudflare.

Pushing to `main` redeploys automatically.

## Files

- `index.html` — the whole site (hash-routed pages: security, privacy, terms,
  accessibility).
- `robots.txt`, `sitemap.xml` — single-URL SEO plumbing.
- `.assetsignore` — keeps this README from being served at `/README.md`.

There is deliberately **no `_redirects` file.** Under Pages, `_redirects` was
evaluated after static assets, so `/* / 302` was a harmless catch-all. Under
Workers static assets it is evaluated *first*, so that rule matched `/` itself
and redirected the homepage to itself forever. `not_found_handling:
"single-page-application"` in [`wrangler.jsonc`](../wrangler.jsonc) does the
same job correctly: unmatched paths serve `index.html` with a 200 instead of
bouncing. Do not reintroduce `_redirects` without testing the root path.

## Before sharing widely

- The `@cleavehq.com` addresses on the page are placeholders until Cloudflare
  Email Routing (or a mailbox) exists for them.
- Privacy and Terms carry a visible "Draft" banner until reviewed by counsel.
  **These pages exist in two copies**, here and in the app's in-app `/legal/*`
  routes. Keep them in sync.
