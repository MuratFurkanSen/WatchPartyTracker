# World Cup Watch Parties

A tiny public bulletin board for organizing World Cup match watch parties.

People can create parties, choose countries and places, add their name, remove names, and manage unused places. There is no login or admin system.

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Or with `uv`:

```powershell
uv sync
```

## Run

```powershell
uvicorn app.main:app --reload
```

With `uv`:

```powershell
uv run uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000
```

## Docker

Build and run with Docker Compose:

```powershell
docker compose up --build
```

Then open:

```text
http://127.0.0.1:8000
```

Run in the background:

```powershell
docker compose up --build -d
```

Stop:

```powershell
docker compose down
```

Compose stores the SQLite database in `./data/app.db` through a bind mount. If another local server is already using port `8000`, stop it first or change the left side of the port mapping in [compose.yaml](compose.yaml).

## Database

SQLite is stored at:

```text
data/app.db
```

The database tables are created on startup. Countries are seeded automatically when the country table is empty.

For temporary testing, set:

```powershell
$env:WATCH_PARTY_DB_PATH = "C:\tmp\watch-party-test.db"
```

## Cleanup

Old parties are deleted automatically when these pages are loaded:

- `/`
- `/parties/new`
- `/places`

A party is old when `match_date < today`. Attendees for deleted old parties are removed too.

## Public Board Warning

Anyone with the URL can create parties, join parties, remove names, add places, and delete unused places. This is intentional.
