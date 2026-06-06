"""Tests für den Adress-Autocomplete-Service und den /adresse/vorschlaege-Endpoint."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.address_autocomplete import (
    AddressSuggestion,
    _cache,
    _parse_feature,
    photon_suggest,
    suggest_addresses,
)


# ── Hilfsfunktionen ───────────────────────────────────────────────────────────

def _photon_feature(name=None, street=None, housenumber=None,
                    city="Wolfurt", lat=47.4664, lon=9.7416, field="street"):
    """Erstellt ein minimales Photon-GeoJSON-Feature."""
    props: dict = {"city": city}
    if name:
        props["name"] = name
    if street:
        props["street"] = street
    if housenumber:
        props["housenumber"] = housenumber
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": props,
    }


def _photon_response(*features):
    return {"type": "FeatureCollection", "features": list(features)}


def _mock_client(response_json: dict):
    """Erstellt ein gemocktes httpx.AsyncClient."""
    mock_resp = AsyncMock()
    mock_resp.raise_for_status = MagicMock(return_value=None)
    mock_resp.json = MagicMock(return_value=response_json)
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)
    return mock_client


@pytest.fixture(autouse=True)
def clear_cache():
    """Leert den Service-Cache vor jedem Test."""
    _cache.clear()
    yield
    _cache.clear()


# ── _parse_feature ─────────────────────────────────────────────────────────────

def test_parse_feature_street():
    feat = _photon_feature(name="Flotzbachstraße", city="Wolfurt", field="street")
    s = _parse_feature(feat, "street")
    assert s is not None
    assert s.street == "Flotzbachstraße"
    assert s.city == "Wolfurt"
    assert s.source == "photon"
    assert "Flotzbachstraße" in s.label
    assert "Wolfurt" in s.label


def test_parse_feature_house():
    feat = _photon_feature(street="Flotzbachstraße", housenumber="3", city="Wolfurt")
    s = _parse_feature(feat, "house")
    assert s is not None
    assert s.house_number == "3"
    assert s.street == "Flotzbachstraße"
    assert "3" in s.label


def test_parse_feature_house_no_housenumber_returns_none():
    feat = _photon_feature(name="Irgendwas", city="Wolfurt")
    s = _parse_feature(feat, "house")
    assert s is None


def test_parse_feature_city():
    feat = {"type": "Feature",
            "geometry": {"type": "Point", "coordinates": [9.74, 47.46]},
            "properties": {"name": "Wolfurt", "postcode": "6922"}}
    s = _parse_feature(feat, "city")
    assert s is not None
    assert s.city == "Wolfurt"
    assert "6922" in s.label


def test_parse_feature_handles_missing_coords():
    feat = {"type": "Feature", "geometry": {"type": "Point", "coordinates": []},
            "properties": {"name": "TestStraße", "city": "Wolfurt"}}
    s = _parse_feature(feat, "street")
    assert s is not None
    assert s.lat is None
    assert s.lng is None


# ── photon_suggest ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_photon_parses_geojson():
    resp = _photon_response(
        _photon_feature(name="Flotzbachstraße", city="Wolfurt"),
        _photon_feature(name="Flurweg", city="Wolfurt"),
    )
    with patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=_mock_client(resp))
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        items = await photon_suggest("fl", field="street", city="Wolfurt",
                                     lat_bias=47.4664, lon_bias=9.7416)
    assert len(items) == 2
    labels = [i.label for i in items]
    assert any("Flotzbachstraße" in l for l in labels)
    assert all(i.source == "photon" for i in items)


@pytest.mark.asyncio
async def test_photon_city_filter_keeps_only_matching_city():
    resp = _photon_response(
        _photon_feature(name="Flotzbachstraße", city="Wolfurt"),
        _photon_feature(name="Feldgasse", city="Bregenz"),
    )
    with patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=_mock_client(resp))
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        items = await photon_suggest("f", field="street", city="Wolfurt",
                                     lat_bias=None, lon_bias=None)
    # Bregenz-Treffer soll herausgefiltert werden
    assert all("Wolfurt" in i.city for i in items if i.city)


@pytest.mark.asyncio
async def test_photon_house_layer_sends_combined_query():
    resp = _photon_response()
    call_args_captured = {}

    async def fake_get(url, **kwargs):
        call_args_captured['params'] = kwargs.get('params', [])
        mock_resp = AsyncMock()
        mock_resp.raise_for_status = MagicMock(return_value=None)
        mock_resp.json = MagicMock(return_value=resp)
        return mock_resp

    with patch("httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.get.side_effect = fake_get
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        # suggest_addresses setzt q = "{street} {q}" für field=="house"
        await suggest_addresses(
            MagicMock(),
            q="3",
            field="house",
            city="Wolfurt",
            street="Flotzbachstraße",
            org_id=None,
            limit=8,
        )

    params = call_args_captured.get('params', [])
    param_dict = dict(params) if isinstance(params, list) else params
    # Query muss Straße + Hausnummer enthalten
    q_val = next((v for k, v in params if k == 'q'), None) if isinstance(params, list) else params.get('q')
    assert q_val is not None
    assert "Flotzbachstraße" in q_val
    assert "3" in q_val
    # Layer muss "house" sein
    layers = [v for k, v in params if k == 'layer'] if isinstance(params, list) else [params.get('layer')]
    assert "house" in layers


@pytest.mark.asyncio
async def test_photon_unreachable_falls_back_to_history():
    hist_item = AddressSuggestion(
        label="Flotzbachstraße, Wolfurt", street="Flotzbachstraße",
        house_number=None, city="Wolfurt", lat=47.4664, lng=9.7416, source="history",
    )
    with patch("app.services.address_autocomplete.photon_suggest", return_value=[]):
        with patch("app.services.address_autocomplete._history_fallback", return_value=[hist_item]):
            items = await suggest_addresses(
                MagicMock(), q="flo", field="street",
                city="Wolfurt", street=None, org_id=1, limit=8,
            )
    assert len(items) == 1
    assert items[0].source == "history"
    assert "Flotzbachstraße" in items[0].label


@pytest.mark.asyncio
async def test_photon_result_cache_hit():
    resp = _photon_response(_photon_feature(name="Flotzbachstraße", city="Wolfurt"))
    call_count = {"n": 0}

    async def fake_get(url, **kwargs):
        call_count["n"] += 1
        mock_resp = AsyncMock()
        mock_resp.raise_for_status = MagicMock(return_value=None)
        mock_resp.json = MagicMock(return_value=resp)
        return mock_resp

    with patch("httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.get.side_effect = fake_get
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        db_mock = MagicMock()
        db_mock.query.return_value.filter.return_value.first.return_value = None

        await suggest_addresses(db_mock, q="fl", field="street",
                                city="Wolfurt", street=None, org_id=None, limit=8)
        await suggest_addresses(db_mock, q="fl", field="street",
                                city="Wolfurt", street=None, org_id=None, limit=8)

    assert call_count["n"] == 1, "Zweiter Aufruf soll aus Cache kommen"


@pytest.mark.asyncio
async def test_suggest_empty_query_returns_empty():
    items = await suggest_addresses(
        MagicMock(), q="", field="street", city="Wolfurt",
        street=None, org_id=None, limit=8,
    )
    assert items == []


# ── Endpoint-Smoke-Tests (ohne Auth) ─────────────────────────────────────────

class TestAddressSuggestionsEndpoint:
    """Smoke-Tests ohne gültige Session → 401/403/Redirect."""

    def test_requires_auth(self, client, setup_db):
        r = client.get("/adresse/vorschlaege?q=fl&field=street",
                       follow_redirects=False)
        assert r.status_code in (302, 401, 403)

    def test_missing_query_returns_empty_or_auth_error(self, client, setup_db):
        r = client.get("/adresse/vorschlaege?q=&field=street",
                       follow_redirects=False)
        # Ohne Auth → 401/302; mit Auth aber leerem q → {"items": []}
        assert r.status_code in (200, 302, 401, 403)
        if r.status_code == 200:
            assert r.json().get("items") == []

    def test_invalid_field_returns_empty_or_auth_error(self, client, setup_db):
        r = client.get("/adresse/vorschlaege?q=test&field=ungueltig",
                       follow_redirects=False)
        assert r.status_code in (200, 302, 401, 403)
        if r.status_code == 200:
            assert r.json().get("items") == []
