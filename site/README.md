# cleavehq.com

The marketing site. A single self-contained `index.html` with no build step, no
external requests, and no analytics.

## Deploy (Cloudflare Pages)

This folder is a **subdirectory** of the `cleave` repo, so the Pages project has
to be pointed at it:

1. Cloudflare dashboard → **Workers & Pages → Create → Pages → Connect to Git**,
   and pick the `cleave` repo.
2. Build settings:
   - **Root directory:** `site`
   - **Framework preset:** None
   - **Build command:** *(empty)*
   - **Build output directory:** `/`
3. **Custom domains** → add `cleavehq.com` and `www.cleavehq.com`. DNS and TLS
   are automatic, since the zone is already on Cloudflare.

The root directory setting is the one that matters. Without it, Pages publishes
the repo root and serves the showcase README instead of the site.

## Files

- `index.html` — the whole site (hash-routed pages: security, privacy, terms,
  accessibility).
- `_redirects` — sends unknown paths to `/`; real files take precedence.
- `robots.txt`, `sitemap.xml` — single-URL SEO plumbing.

## Before sharing widely

- The `@cleavehq.com` addresses on the page are placeholders until Cloudflare
  Email Routing (or a mailbox) exists for them.
- Privacy and Terms carry a visible "Draft" banner until reviewed by counsel.
  **These pages exist in two copies**, here and in the app's in-app `/legal/*`
  routes. Keep them in sync.
