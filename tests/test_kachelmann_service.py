"""Tests für kachelmann_service.py — HTTP-Antworten gemockt."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services import kachelmann_service

LAT, LNG = 47.466, 9.745


def _mock_httpx_response(json_data: dict):
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock(return_value=None)
    mock_resp.json = MagicMock(return_value=json_data)
    return mock_resp


def _patch_client(mock_resp):
    """Liefert einen Context-Manager-Patch für httpx.AsyncClient mit fester Antwort."""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)
    cm = patch("httpx.AsyncClient")
    return cm, mock_client


@pytest.fixture(autouse=True)
def _reset_key_cache():
    kachelmann_service.reset_key_cache()
    yield
    kachelmann_service.reset_key_cache()


# ── _get_api_key ──────────────────────────────────────────────────────────────

def test_is_configured_false_without_key(monkeypatch):
    monkeypatch.setattr(kachelmann_service.settings, "KACHELMANN_API_KEY", "")
    # SystemSettings-Lookup wird übersprungen → nur ENV-Fallback (leer) zählt
    with patch("app.db.SessionLocal", side_effect=RuntimeError("no db")):
        kachelmann_service.reset_key_cache()
        assert kachelmann_service.is_configured() is False


def test_get_api_key_env_fallback(monkeypatch):
    monkeypatch.setattr(kachelmann_service.settings, "KACHELMANN_API_KEY", "env-key-123")
    with patch("app.db.SessionLocal", side_effect=RuntimeError("no db")):
        kachelmann_service.reset_key_cache()
        assert kachelmann_service._get_api_key() == "env-key-123"
        assert kachelmann_service.is_configured() is True


# ── fetch_current ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_fetch_current_parses_flat_response():
    data = {
        "temperature": 12.5,
        "relativeHumidity": 80,
        "windSpeed": 5.0,
        "windGust": 9.0,
        "windDirection": 270,
        "precipitation": 1.2,
    }
    cm, _ = _patch_client(_mock_httpx_response(data))
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=_mock_httpx_response(data))
    with patch.object(kachelmann_service, "_get_api_key", return_value="k"), cm as mock_cls:
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=None)
        result = await kachelmann_service.fetch_current(LAT, LNG)

    assert result is not None
    assert result.source == "kachelmann"
    assert result.temperature_c == pytest.approx(12.5)
    assert result.humidity_pct == pytest.approx(80)
    assert result.wind_speed_ms == pytest.approx(5.0)
    assert result.gust_speed_ms == pytest.approx(9.0)
    assert result.wind_direction_deg == pytest.approx(270)
    assert result.precipitation_1h_mm == pytest.approx(1.2)


@pytest.mark.asyncio
async def test_fetch_current_normalizes_kmh_wind():
    data = {"temperature": 10.0, "windSpeed": 54.0}   # >40 → als km/h interpretiert
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=_mock_httpx_response(data))
    with patch.object(kachelmann_service, "_get_api_key", return_value="k"), \
            patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=None)
        result = await kachelmann_service.fetch_current(LAT, LNG)

    assert result.wind_speed_ms == pytest.approx(54.0 / 3.6, rel=1e-3)


@pytest.mark.asyncio
async def test_fetch_current_nested_data_key():
    data = {"data": {"temp": 7.0, "wind": 3.0}}
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=_mock_httpx_response(data))
    with patch.object(kachelmann_service, "_get_api_key", return_value="k"), \
            patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=None)
        result = await kachelmann_service.fetch_current(LAT, LNG)

    assert result is not None
    assert result.temperature_c == pytest.approx(7.0)


@pytest.mark.asyncio
async def test_fetch_current_none_without_key():
    with patch.object(kachelmann_service, "_get_api_key", return_value=None):
        result = await kachelmann_service.fetch_current(LAT, LNG)
    assert result is None


@pytest.mark.asyncio
async def test_fetch_current_none_on_http_error():
    import httpx
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.HTTPStatusError(
        "401", request=MagicMock(), response=MagicMock(status_code=401)))
    with patch.object(kachelmann_service, "_get_api_key", return_value="k"), \
            patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=None)
        result = await kachelmann_service.fetch_current(LAT, LNG)
    assert result is None


@pytest.mark.asyncio
async def test_fetch_current_none_on_unexpected_shape():
    data = {"foo": "bar"}   # keine verwertbaren Felder
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=_mock_httpx_response(data))
    with patch.object(kachelmann_service, "_get_api_key", return_value="k"), \
            patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=None)
        result = await kachelmann_service.fetch_current(LAT, LNG)
    assert result is None


# ── fetch_forecast ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_fetch_forecast_accumulates_precipitation():
    hourly = [
        {"time": f"2026-06-15T{h:02d}:00:00+00:00",
         "temperature": 14.0 + h * 0.1,
         "windSpeed": 4.0,
         "windGust": 7.0,
         "precipitation": 1.0}
        for h in range(25)
    ]
    data = {"hourly": hourly}
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=_mock_httpx_response(data))
    with patch.object(kachelmann_service, "_get_api_key", return_value="k"), \
            patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=None)
        result = await kachelmann_service.fetch_forecast(LAT, LNG, horizons=(6, 12, 24))

    assert result is not None
    assert result.source == "kachelmann"
    assert len(result.horizons) == 3
    h6 = result.horizons[0]
    assert h6.hours == 6
    # akkumuliert: Summe prec[0..6] = 7 * 1.0
    assert h6.precipitation_acc_mm == pytest.approx(7.0, rel=1e-3)
    assert h6.temperature_c == pytest.approx(14.6, rel=1e-3)
    assert h6.wind_speed_ms == pytest.approx(4.0)


@pytest.mark.asyncio
async def test_fetch_current_real_wrapped_shape():
    """Echte /current-Struktur: data-Objekt, je Feld {"value": …}."""
    data = {
        "lat": 47.46, "lon": 9.75, "systemOfUnits": "metric",
        "data": {
            "temp": {"name": "temp", "value": 21.9, "type": "float"},
            "humidityRelative": {"name": "humidityRelative", "value": 45},
            "windSpeed": {"name": "windSpeed", "value": 0.5},
            "windGust": {"name": "windGust", "value": 5.3},
            "windDirection": {"name": "windDirection", "value": 307},
            "prec1h": {"name": "prec1h", "value": 0},
        },
    }
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=_mock_httpx_response(data))
    with patch.object(kachelmann_service, "_get_api_key", return_value="k"), \
            patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=None)
        result = await kachelmann_service.fetch_current(47.46, 9.75)

    assert result is not None
    assert result.temperature_c == pytest.approx(21.9)
    assert result.humidity_pct == pytest.approx(45)
    assert result.wind_speed_ms == pytest.approx(0.5)
    assert result.gust_speed_ms == pytest.approx(5.3)
    assert result.wind_direction_deg == pytest.approx(307)
    assert result.precipitation_1h_mm == pytest.approx(0)


@pytest.mark.asyncio
async def test_fetch_forecast_real_data_shape():
    """Echte /forecast-Struktur: data-Liste, flache Werte, precCurrent + windSpeed."""
    rows = [
        {"dateTime": f"2026-06-16T{9 + h:02d}:00:00+00:00",
         "temp": 20.0 + h, "humidityRelative": 50,
         "windSpeed": 1.5, "windGust": 4.0, "windDirection": 280,
         "precCurrent": 2.0, "snowAmount": 0}
        for h in range(15)
    ]
    data = {"lat": 47.46, "lon": 9.75, "resolution": "SUPER_HIGH", "data": rows}
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=_mock_httpx_response(data))
    with patch.object(kachelmann_service, "_get_api_key", return_value="k"), \
            patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=None)
        result = await kachelmann_service.fetch_forecast(47.46, 9.75, horizons=(6, 12, 24))

    assert result is not None
    h6 = result.horizons[0]
    assert h6.hours == 6
    # precCurrent=2.0 je Stunde, akkumuliert bis index 6 = 7 * 2.0
    assert h6.precipitation_acc_mm == pytest.approx(14.0, rel=1e-3)
    assert h6.wind_speed_ms == pytest.approx(1.5)
    # +24h liegt jenseits der 15er-Reihe → auf letzten Schritt geclamped (Werte vorhanden)
    h24 = result.horizons[2]
    assert h24.temperature_c is not None
    assert h24.wind_speed_ms is not None


@pytest.mark.asyncio
async def test_fetch_forecast_none_on_empty():
    data = {"hourly": []}
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=_mock_httpx_response(data))
    with patch.object(kachelmann_service, "_get_api_key", return_value="k"), \
            patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=None)
        result = await kachelmann_service.fetch_forecast(LAT, LNG)
    assert result is None
