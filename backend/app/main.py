import csv
import io
import json
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session
from .config import settings
from .database import Base, engine, get_db
from .models import WeatherHistory
from .schemas import HistoryOut, LocationInput
from . import weather as service

@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine)
    yield

app = FastAPI(title="WeatherWise API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in settings.cors_origins.split(",") if x.strip()], allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["Content-Type"])

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.get("/api/weather/current")
async def current(location: str = Query(min_length=1, max_length=200)):
    return await service.weather(await service.resolve(location))

@app.get("/api/weather/forecast")
async def forecast(location: str = Query(min_length=1, max_length=200)):
    return await service.weather(await service.resolve(location))

def get_record(db, record_id):
    record = db.get(WeatherHistory, record_id)
    if record is None:
        raise HTTPException(404, "Saved record not found.")
    return record

@app.post("/api/weather/history", response_model=HistoryOut, status_code=201)
async def create_history(body: LocationInput, db: Session = Depends(get_db)):
    place = await service.resolve(body.location)
    data = await service.weather(place, body.start_date, body.end_date)
    record = WeatherHistory(location=place["name"], latitude=place["latitude"], longitude=place["longitude"], start_date=body.start_date, end_date=body.end_date, weather=data)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

@app.get("/api/weather/history", response_model=list[HistoryOut])
def list_history(db: Session = Depends(get_db)):
    return db.scalars(select(WeatherHistory).order_by(WeatherHistory.id.desc())).all()

@app.get("/api/weather/export")
def export(format: str = Query("csv", pattern="^(csv|json)$"), db: Session = Depends(get_db)):
    records = [HistoryOut.model_validate(r).model_dump(mode="json") for r in db.scalars(select(WeatherHistory).order_by(WeatherHistory.id.desc())).all()]
    if format == "json":
        return Response(json.dumps(records, indent=2), media_type="application/json", headers={"Content-Disposition": 'attachment; filename="weatherwise.json"'})
    out = io.StringIO(newline="")
    fields = list(HistoryOut.model_fields)
    writer = csv.DictWriter(out, fieldnames=fields)
    writer.writeheader()
    for record in records:
        record["weather"] = json.dumps(record["weather"])
        # Prevent spreadsheet formula execution from user-derived strings.
        for key, value in record.items():
            if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
                record[key] = "'" + value
        writer.writerow(record)
    return Response(out.getvalue(), media_type="text/csv", headers={"Content-Disposition": 'attachment; filename="weatherwise.csv"'})

@app.get("/api/weather/history/{record_id}", response_model=HistoryOut)
def read_history(record_id: int, db: Session = Depends(get_db)):
    return get_record(db, record_id)

@app.put("/api/weather/history/{record_id}", response_model=HistoryOut)
async def update_history(record_id: int, body: LocationInput, db: Session = Depends(get_db)):
    record = get_record(db, record_id)
    place = await service.resolve(body.location)
    data = await service.weather(place, body.start_date, body.end_date)
    record.location, record.latitude, record.longitude = place["name"], place["latitude"], place["longitude"]
    record.start_date, record.end_date, record.weather = body.start_date, body.end_date, data
    db.commit()
    db.refresh(record)
    return record

@app.delete("/api/weather/history/{record_id}", status_code=204)
def delete_history(record_id: int, db: Session = Depends(get_db)):
    db.delete(get_record(db, record_id))
    db.commit()
