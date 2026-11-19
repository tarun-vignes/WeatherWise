from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base, get_db
from app.main import app
from app import weather

@pytest.fixture
def client(monkeypatch):
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    def override():
        with Session() as db:
            yield db
    app.dependency_overrides[get_db] = override
    async def fake_fetch(url, params):
        if url == weather.GEOCODE:
            if params['name'] == 'nowhere': return {}
            return {'results': [{'name': params['name'], 'country': 'US', 'latitude': 40, 'longitude': -74}]}
        start = date.fromisoformat(params['start_date']) if 'start_date' in params else date.today()
        count = (date.fromisoformat(params['end_date']) - start).days + 1 if 'end_date' in params else 5
        return {'timezone': 'America/New_York', 'current': dict(zip(weather.CURRENT.split(','), [20, 50, 0, 0, 10])), 'daily': {'time': [(start + timedelta(days=i)).isoformat() for i in range(count)], **{key: [1] * count for key in weather.DAILY.split(',')}}}
    monkeypatch.setattr(weather, 'fetch', fake_fetch)
    with TestClient(app) as c: yield c
    app.dependency_overrides.clear()
    engine.dispose()

def payload(location='Boston'):
    return {'location': location, 'start_date': date.today().isoformat(), 'end_date': (date.today()+timedelta(days=2)).isoformat()}

def test_search_and_invalid_location(client):
    r = client.get('/api/weather/current', params={'location':'Boston'})
    assert r.status_code == 200 and len(r.json()['daily']['time']) == 5
    assert client.get('/api/weather/forecast', params={'location':'nowhere'}).status_code == 404
    assert client.get('/api/weather/current', params={'location':'91, 0'}).status_code == 422

def test_date_validation_and_provider_failure(client, monkeypatch):
    assert client.post('/api/weather/history', json={**payload(), 'end_date':'2000-01-01'}).status_code == 422
    assert client.post('/api/weather/history', json={**payload(), 'start_date':'2000-01-01'}).status_code == 422
    async def bad(*args): return {}
    monkeypatch.setattr(weather, 'fetch', bad)
    assert client.get('/api/weather/current', params={'location':'40, -74'}).status_code == 502

def test_crud_and_export(client):
    r = client.post('/api/weather/history', json=payload())
    assert r.status_code == 201
    id = r.json()['id']
    assert client.get(f'/api/weather/history/{id}').json()['location'] == 'Boston, US'
    assert len(client.get('/api/weather/history').json()) == 1
    assert client.put(f'/api/weather/history/{id}', json=payload('Seattle')).json()['location'] == 'Seattle, US'
    assert client.put(f'/api/weather/history/{id}', json={**payload(), 'weather':{}}).status_code == 422
    assert 'Seattle' in client.get('/api/weather/export?format=csv').text
    assert client.get('/api/weather/export?format=json').json()[0]['id'] == id
    assert client.delete(f'/api/weather/history/{id}').status_code == 204
    assert client.get(f'/api/weather/history/{id}').status_code == 404
