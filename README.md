# AI School OS

Phase 3A — Simple Architecture refactor (structural only).

## Layout

```
ai-school/
├── app/
│   ├── index.html          # navigation shell + inline views
│   ├── dashboard.html      # dashboard view partial
│   ├── classroom.html      # classroom view partial
│   ├── css/
│   │   └── style.css       # single CSS file (all styles)
│   ├── js/
│   │   ├── api.js          # data layer + Phase 3B API stubs
│   │   ├── home.js         # shell, router, chrome
│   │   ├── dashboard.js    # dashboard + subject page rendering
│   │   └── classroom.js    # classroom + transition + workspace
│   └── assets/
│       ├── images/
│       ├── icons/
│       └── fonts/
├── core/                   # backend skeleton (Phase 3B)
├── services/
├── teachers/
├── tools/
├── data/
├── tests/
├── run.py                  # dev server
├── requirements.txt
├── README.md
└── AGENTS.md
```

## Rules (Phase 3A)

- No redesign, no rewrite, no UI change.
- No frameworks, bundlers, TypeScript.
- Single CSS file, vanilla JS.
- Pixel-perfect: identical look, behavior, localStorage keys, IDs, classes, routes.

## Run

```powershell
python run.py
# then open http://localhost:8000/
```

## Backend

`core/`, `services/`, `teachers/`, `tools/`, `data/`, `tests/` are empty skeletons
prepared for Phase 3B (FastAPI). No backend logic is implemented in Phase 3A.
