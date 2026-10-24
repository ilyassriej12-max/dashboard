# AI School OS — Agent Instructions

## Role
You are working on a frontend structural refactor (Phase 3A). The application
already works and must remain visually and functionally identical.

## Constraints (STRICT)
- Do NOT change UI, UX, colors, layout, animations, styling, components,
  buttons, spacing, typography, icons, navigation behavior, search, dashboard
  logic, localStorage, state, or JavaScript behavior.
- Do NOT introduce React/Vue/Svelte, bundlers, TypeScript, or frameworks.
- Do NOT optimize or rename for the sake of it.
- Keep one CSS file: app/css/style.css.
- Keep JS split as: api.js, home.js, dashboard.js, classroom.js.
- localStorage keys, IDs, class names, routes, and navigation must not change.

## Layout
- Frontend lives entirely under `app/`.
- `app/index.html` is the navigation shell (serves inline views + fetches
  dashboard.html / classroom.html into #viewContainer).
- Backend skeleton folders at root: core/, services/, teachers/, tools/,
  data/, tests/ (empty, Phase 3B only).

## Serve locally
`python run.py` → http://localhost:8000/
(The dashboard/classroom partials are fetched via XHR, so use HTTP, not file://.)

## Verification
- Zero console errors.
- No broken paths, duplicate IDs, duplicate files, or missing assets.
- Application looks and behaves identical to the pre-refactor version.
