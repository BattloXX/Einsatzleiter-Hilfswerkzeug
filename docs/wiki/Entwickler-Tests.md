# Tests

← [Zurück zur Startseite](Home)

## Test-Stack

| Werkzeug | Zweck |
|----------|-------|
| **pytest** | Test-Runner |
| **FastAPI TestClient** | HTTP-Tests ohne echten Server |
| **SQLite** | In-Memory-DB für Tests (statt MariaDB) |

## Tests ausführen

```bash
# Alle Tests:
pytest tests/ -v

# Nur Unit-Tests:
pytest tests/test_breathing.py -v

# Nur API-Tests:
pytest tests/test_api.py -v

# Mit Coverage:
pytest tests/ --cov=app --cov-report=html
```

## Test-Struktur

```
tests/
├── conftest.py          – Fixtures (SQLite-DB, TestClient, API-Key)
├── test_api.py          – REST-API-Tests
└── test_breathing.py    – Atemschutz-Service-Tests
```

## conftest.py — Fixtures

```python
# SQLite-Testdatenbank (automatisch in pytest-Session erstellt):
@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSession()
    seed(db)    # Wolfurt-Stammdaten einfüllen
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)

# FastAPI-TestClient mit überschriebener DB-Dependency:
@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

## test_breathing.py — Unit-Tests

```python
def test_withdraw_pressure_calculation():
    assert calc_withdraw_pressure(300, 0.5, 10) == 160.0
    assert calc_withdraw_pressure(200, 0.5, 10) == 110.0

def test_warning_level_yellow():
    # 220 bar bei 300 Anfangsdruck → unter 75% = 225 → gelb
    assert get_warning_level(troop) == "yellow"

def test_warning_level_red():
    # 155 bar bei Rückzugsdruck 160 → rot
    assert get_warning_level(troop) == "red"
```

## test_api.py — Integrations-Tests

```python
def test_create_incident_no_key(client):
    r = client.post("/api/v1/einsatz", json=PAYLOAD)
    assert r.status_code == 422   # Fehlender Header

def test_create_incident_success(client, api_key):
    r = client.post("/api/v1/einsatz", json=PAYLOAD,
                    headers={"X-API-Key": api_key})
    assert r.status_code == 200
    assert r.json()["created"] is True

def test_idempotency(client, api_key):
    # Zweiter Aufruf mit gleichem Key → created=False
    r2 = client.post("/api/v1/einsatz", json=PAYLOAD,
                     headers={"X-API-Key": api_key})
    assert r2.json()["created"] is False
```

## CI-Pipeline (GitHub Actions)

Drei parallele Jobs in `.github/workflows/ci.yml`:

1. **lint** — `ruff check app/`
2. **typecheck** — `mypy app/ --ignore-missing-imports`
3. **test** — pytest mit echtem MariaDB-Service-Container

```yaml
services:
  mariadb:
    image: mariadb:10.11
    env:
      MARIADB_DATABASE: einsatzleiter_test
      MARIADB_USER: einsatzleiter
      MARIADB_PASSWORD: testpass
```

## Tests schreiben

Neue Tests in `tests/test_*.py` anlegen. Fixtures aus `conftest.py` per Parameter-Name einbinden:

```python
def test_mein_test(client, api_key, setup_db):
    ...
```

## Was wir NICHT mocken

Wir mocken die Datenbank **nicht** in Tests — alle Tests laufen gegen eine echte (SQLite-/MariaDB-)Datenbank. Mock/DB-Divergenz hat in der Vergangenheit Migrationsbugs verdeckt.
