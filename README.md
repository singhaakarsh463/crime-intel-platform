# Crime Intelligence Platform — Phase 1 through 5

Full build through Phase 5: the original MVP plan (Login/Dashboard/Case DB, Charts/Map/Export,
deep-search AI assistant, Network Graph/Similar Cases/Predictions) plus the additional Key
Features requested afterward — bilingual voice chat, chat-transcript PDF export, and an
explainable-AI audit trail.

## What's included
- **Backend** (`/backend`): FastAPI + SQLAlchemy + JWT auth
  - `users`, `cases`, `persons`, `evidence`, `chat_sessions`, `chat_messages`, `audit_logs` tables
  - Role-based access (investigator / analyst / admin / viewer)
  - Case search+filter+create, case detail (with linked persons/evidence), map data, dashboard
    stats, PDF case-report export, a deep-search RAG chatbot, a case-relationship network graph,
    similar-case suggestions, and predictive district-trend alerts
  - SQLite by default (swap `DATABASE_URL` env var for Postgres later)
- **Frontend** (`/frontend`): React + Vite + Tailwind
  - Login page, protected routes
  - Dashboard: case counts, crime-type/district charts, high-severity alerts, **predictive alerts**
    (districts trending up over the last 30 days)
  - Case Search → Case Detail (persons, evidence, PDF export) → **Similar Cases** panel
  - Hotspot Map (Leaflet, dark basemap)
  - **Network Graph**: force-directed graph (d3) of cases and linked persons, with dashed red
    edges flagging people who share a phone number across different cases
  - **Case Assistant**: a floating chat button (bottom-right, on every page) instead of a sidebar
    tab — click to open a compact chat panel

## The AI Case Assistant (deep search, not a simple Q&A bot)
The assistant is built to behave like an investigator's research partner rather than a lookup tool:
1. **Deep search** (`app/routers/chat.py`): a query is checked for an exact case ID
   (e.g. `CR-2026-0016`) or a phone number, and those records are pulled in directly and given
   priority - alongside a broader TF-IDF similarity search (`app/rag.py`) over every case, person,
   and evidence record. Results are merged and deduplicated.
2. **Investigator-grade answers** (`app/llm.py`): the system prompt asks the model to explain
   cases in plain terms, proactively surface connections across cases (shared people, phone
   numbers, districts, timing), and suggest concrete next investigative steps - not just answer
   the literal question. Requires an Anthropic API key (see below); without one, it still returns
   the retrieved case matches with an explicit note that AI generation is unavailable.
3. **Conversation history** is still saved per session (`chat_sessions` / `chat_messages`) so
   context isn't lost - the widget keeps its active session in the browser and reuses it across
   page navigation.

**To enable AI-generated answers**, set an environment variable before starting the backend:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

## Network graph logic
`GET /api/network/graph` returns case nodes, person nodes, `linked_to` edges (person → case), and
`shared_phone` edges whenever the same phone number appears on persons attached to *different*
cases - a quick way to surface a possible recurring suspect. The frontend renders this with a
d3-force simulation (drag to reposition, scroll to zoom, click a node for details).

## Phase 5 — remaining Key Features
Added on top of Phase 1-4, matching the feature list in the project brief:

- **Bilingual chatbot (English + Kannada)**: a language toggle (EN / ಕನ್ನಡ) in the chat widget is
  sent with every message; the backend instructs the model to answer fully in Kannada script when
  selected, translating case facts rather than leaving them in English.
- **Voice-enabled interaction**: the mic button uses the browser's Web Speech API
  (`SpeechRecognition`) for voice input in the selected language, and the speaker icon on each
  assistant reply uses `speechSynthesis` to read the answer aloud. Works best in Chrome; the app
  degrades gracefully (a message explains it isn't supported) in browsers without this API.
- **PDF export of conversation history**: the "PDF" button in the chat widget calls
  `GET /api/export/chat/{session_id}/report`, which renders the full transcript (investigator
  questions, assistant answers, and cited sources) as a downloadable PDF via reportlab.
- **Explainable AI with audit trails**: every chat query now records *why* each case was
  retrieved — `direct_case_id` (exact case-ID mention), `phone_match` (phone-number lookup), or
  `similarity` (TF-IDF match) — shown as a label on each source chip in the UI. Every AI query,
  case creation, and PDF export is also written to `audit_logs`, visible to admins on the new
  **Audit Trail** page (`/audit`), so any answer or action can be traced back to who asked what
  and when.
- Context-aware conversations, criminal network visualization, crime trend/hotspot detection,
  predictive analytics, and role-based secure access were already covered in Phases 1-4.

## Next steps (beyond the current plan)
- Move similarity search from TF-IDF to real embeddings + a vector DB (pgvector / Chroma) at scale
- Switch SQLite → PostgreSQL + PostGIS for production-grade geospatial queries
- Audit log viewer, sensitive-data masking, encryption at rest
- Replace the simple 30-day trend heuristic with a proper time-series forecasting model

## Run the backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows
pip install -r requirements.txt
python seed.py                  # creates admin user + 40 sample cases
uvicorn app.main:app --reload --port 8000
```
Backend runs at `http://localhost:8000`. Interactive API docs: `http://localhost:8000/docs`.

Default login: **admin@crimeintel.local / Admin@123**

## Run the frontend
```bash
cd frontend
npm install
npm run dev
```
Frontend runs at `http://localhost:5173` and proxies `/api` calls to the backend.

## Next steps (Phase 4, from the plan)
- Network graph (suspects / phone numbers / locations linked visually)
- Similar-case suggestions, alerts and predictions
- Switch SQLite → PostgreSQL + PostGIS, and TF-IDF → real embeddings + a vector DB, for production scale
- Audit log viewer, sensitive-data masking, encryption at rest
