# TripMate AI — Next.js

A Next.js (App Router) port of the TripMate AI travel-planner UI, keeping the
original dark, glassy aesthetic (blurred gradient orbs, frosted cards,
blue-to-purple accent) but rebuilt as proper React components with state
instead of raw DOM manipulation.

## What's included

- `app/layout.js` — root layout, loads global styles + Inter font
- `app/page.js` — the planner UI: prompt textarea, quick-prompt chips,
  result panel with Markdown rendering, copy button, and PDF export
- `app/globals.css` — the original visual design (1:1 port of the shared
  `style.css`), including the print stylesheet used for PDF export

## Getting started

```bash
npm install
npm run dev
```

Open http://localhost:3000.

## Connecting your backend

The UI posts to `NEXT_PUBLIC_API_URL` (defaults to `/api/plan`) with:

```json
{ "message": "Plan a 7 day Japan trip...", "thread_id": null }
```

and expects a JSON response shaped like:

```json
{ "reply": "## Your itinerary...", "thread_id": "abc-123" }
```

Point it at your existing FastAPI/LangGraph service by setting an env var in
`.env.local`:

```
NEXT_PUBLIC_API_URL=https://your-fastapi-host/api/plan
```

If your backend returns the plan under a different key (`result`, `message`,
etc.) the page already falls back to those field names — adjust in
`app/page.js` if needed.

## Notes

- Markdown → HTML rendering uses `marked`.
- PDF export uses `html2pdf.js`, dynamically imported client-side only (it
  needs `window`), targeting the `.pdf-content` panel — the print stylesheet
  in `globals.css` hides everything else when exporting.
- Fully responsive down to mobile (single-column input, stacked actions),
  matching the original's `@media (max-width: 760px)` breakpoint.
