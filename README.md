# WeatherWise

A full-stack weather dashboard by Tarun Vigneswaran, completing both frontend and backend assessments. WeatherWise resolves a location using Open-Meteo, retrieves real current conditions and a five-day forecast, and stores requested forecast snapshots in a database. No API key is required.

## Features

- City, town, postal code (where supported by Open-Meteo), or `latitude, longitude` search; browser geolocation with permission.
- Current temperature, conditions, humidity, precipitation and wind; Celsius/Fahrenheit toggle; five-day daily high, low, precipitation and conditions.
- Forecast-derived travel notes and an OpenStreetMap link; responsive layouts and accessible labels, status and error messages.
- Save, list, view, update and delete forecast snapshots; CSV and JSON exports. Updates fetch new observations instead of accepting user-supplied measurements.
- FastAPI validation, SQLite persistence, optional PostgreSQL, and mocked provider tests.

## Run locally

Requires Node.js 20.9+ (22 recommended), npm, Python 3.10+, and internet access. Open two terminals from this directory:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

If PowerShell script execution is disabled, use `cmd` and `.venv\Scripts\activate.bat` instead. In another terminal:

If Windows application control blocks SQLAlchemy's compiled extension, install its pure-Python build instead: `$env:DISABLE_SQLALCHEMY_CEXT='1'; python -m pip install --no-binary sqlalchemy -r requirements.txt`.

```powershell
cd frontend
npm.cmd install
Copy-Item .env.example .env.local
npm.cmd run dev
```

Visit http://localhost:3000. The API documentation is at http://localhost:8000/docs and health check at http://localhost:8000/api/health. On macOS/Linux use `source .venv/bin/activate`, `cp`, and `npm` instead.

SQLite is created automatically in `backend/weatherwise.db`. To use PostgreSQL, set `DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/weatherwise` in `backend/.env` and create the database first. Set `CORS_ORIGINS` to a comma-separated list of allowed frontend origins. Set `NEXT_PUBLIC_API_URL` before building the frontend if the API is hosted elsewhere. Restart after changing environment variables. Never commit credentials.

## Architecture and behavior

The Next.js client calls FastAPI over REST. The backend resolves names with Open-Meteo Geocoding, retrieves forecasts from Open-Meteo, validates the response, and uses SQLAlchemy to store a JSON snapshot with location, coordinates, dates and timestamps. Coordinates are accepted directly; reverse geocoding is not performed. Ambiguous searches select the first geocoding result. Postal-code coverage depends on the provider, and landmark search is not guaranteed.

Date ranges are limited to today through 15 days ahead (inclusive), a conservative subset of the forecast endpoint. They are evaluated against the backend system date; near midnight, the location's local date can differ and Open-Meteo may reject a boundary request. Historical data is not synthesized. Temperatures are stored in Celsius, precipitation in millimeters and wind in km/h; the unit toggle converts temperatures for display. Forecasts are estimates, not observed future weather. History is shared and unauthenticated, appropriate for a local assessment demo but not a public multi-user deployment. Database migrations, rate limiting, authentication, and retention policies would be needed for production.

## API

All weather endpoints are prefixed `/api/weather`:

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/current?location=Boston` | Current weather and five daily forecasts |
| GET | `/forecast?location=Boston` | Five daily forecasts and current conditions |
| POST | `/history` | Create a snapshot |
| GET | `/history` | List snapshots |
| GET | `/history/{id}` | Read a snapshot |
| PUT | `/history/{id}` | Replace location and dates, refreshing provider data |
| DELETE | `/history/{id}` | Delete a snapshot |
| GET | `/export?format=csv` | Download CSV; `format=json` is also supported |
| GET | `/api/health` | Health status (outside the weather prefix) |

POST and PUT accept `{"location":"Boston","start_date":"YYYY-MM-DD","end_date":"YYYY-MM-DD"}`. Validation errors return 422, missing records/locations 404, and upstream failures 502. GET responses include the resolved coordinates and provider data. Browse `/docs` for schemas and interactive requests.

## Tests and checks

```powershell
cd backend
python -m pytest -q
cd ../frontend
npm.cmd run typecheck
npm.cmd run lint
npm.cmd run build
```

The backend tests mock Open-Meteo and cover search, invalid locations and dates, malformed provider responses, CRUD, and exports. Successful checks exit with code zero. Live use requires network access to Open-Meteo.

## Assessment checklist

- [x] Assessment 1: JavaScript framework frontend, responsive web design, input, current location, weather icons, live API data, five-day forecast and errors.
- [x] Assessment 2: REST API, persistent CRUD, validated location/date inputs, stored forecast data and CSV/JSON export.
- [x] Extra integration: OpenStreetMap link and practical forecast-based travel notes.
- [x] Name and PM Accelerator information included in the application.
- [ ] Record a 1–2 minute demo, publish the repository and video, and submit the assessment form. These submission steps require the candidate.

## Suggested 1–2 minute demo

1. Introduce WeatherWise and state that it completes both assessments. Search a city and show current conditions, units, five-day forecast, travel notes and map link.
2. Show the geolocation button and an invalid-location error. Choose a date range, save it, then edit and delete a record; download an export.
3. Briefly show the FastAPI docs, SQLAlchemy model and mocked tests. Explain that updates re-fetch weather and that dates are limited to the provider forecast window.
