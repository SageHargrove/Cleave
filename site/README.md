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

- `index.html` — the whole page (hash-routed sections: security, privacy,
  terms, accessibility).
- `shots/` — the screen tour in the "See it" section, light and dark. A copy of
  the repo's `screenshots/`, which is what the GitHub README reads; only `site/`
  is deployed, so the images have to live under it. Regenerate both from the
  product with `nox -s shots`.
- `cleave-sample-report.pdf` — the executive PDF a run produces, offered as a
  download beside the tour.
- `demo/` — the live demo at cleavehq.com/demo. See below.
- `manual/` — the user documentation, served at `/manual/`. The demo's in-app
  Help fetches it from there by absolute path, so it has to sit at the site
  root rather than under `demo/`.
- `robots.txt`, `sitemap.xml` — single-URL SEO plumbing.
- `.assetsignore` — keeps this README from being served at `/README.md`.

## The demo

`/demo/` is the real product interface with no server behind it. It is the SPA
built from the private repo, wired to a capture of a real server driving the
shipped sample project, so the screens, the numbers and the reasoning are the
build's own rather than a mockup.

Nothing here is the product's engine: the analysis is Python and none of it
ships to the browser in any build. What the demo publishes is the interface,
which already goes out in every wheel, plus one synthetic estate.

It is read-only by construction. There is nothing to write to, so every
non-GET is answered with the product's own "read-only" state and the interface
explains it.

To rebuild it, from the private repo:

```
python scripts/capture_demo.py     # seeds the sample, analyses, captures
cd frontend && npm run build:demo  # builds into frontend/demo-dist/
```

Then copy `demo-dist/` here as `site/demo/`, and its `manual/` folder up to
`site/manual/`. Both are committed, because a clone of this repo has no way to
rebuild them.

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
