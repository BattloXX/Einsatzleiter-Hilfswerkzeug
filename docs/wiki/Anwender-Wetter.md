# Wetter-Integration

← [Zurück zur Startseite](Home)

Das Wetter-Modul zeigt Echtzeit-Wetterdaten, Vorhersagen und amtliche Unwetterwarnungen direkt im Tool an — integriert in Einsatz-Board und Großschadenslage sowie als eigene Seite.

---

## Aktivierung

Das Wetter-Modul ist systemweit standardmäßig aktiv. Jede Organisation kann es in den **Einstellungen → Organisation** individuell deaktivieren.

---

## Einsatz-Board (Wetter-Panel)

Im laufenden Einsatz erscheint rechts im Board ein **Wetter-Panel** mit:

| Bereich | Inhalt |
|---------|--------|
| **Nowcast (15 min)** | Aktuell gemessene Werte: Temperatur, Wind, Böen, Niederschlag, Sicht |
| **Ist-Werte** | Aktuelle Messwerte der nächsten Wetterstation |
| **Vorhersage** | +6h / +12h / +24h (Temperatur, Niederschlag, Wind) |
| **Unwetterwarnungen** | Amtliche ZAMG-Warnungen für den Einsatzort |
| **Szenarien** | Sturm- und Waldbrand-Indikatoren (farblich hervorgehoben) |

Das Wetter-Panel zeigt Daten für den **Einsatzort** (Adresse / Koordinaten des Einsatzes). Ist keine Adresse hinterlegt, wird der Org-Standort als Fallback verwendet.

---

## Globale Wetter-Seite

**URL:** `/wetter`

Die globale Wetter-Seite zeigt Wetterdaten für den **Org-Standort** (konfiguriert in Einstellungen → Organisation → Standort). Sie eignet sich als Überblick ohne aktiven Einsatz.

---

## Wetter in der Großschadenslage

Im GSL-Board gibt es ein dediziertes **Wetter-Tab** mit denselben Daten wie das Einsatz-Board-Panel, aber für den Standort der Großschadenslage.

Zusätzlich: **Radar-Overlay** auf der Lagekarte (Niederschlagsradar via RainViewer, letzte 2h und Nowcast).

---

## Szenario-Indikatoren

Zwei Szenarien werden automatisch berechnet und farblich hervorgehoben:

| Szenario | Kriterien | Farbe |
|----------|-----------|-------|
| **Sturm** | Windböen ≥ 60 km/h oder Warnstufe „Sturm" | Orange / Rot |
| **Waldbrand** | Hohe Temperatur + geringe Luftfeuchtigkeit + Wind + wenig Niederschlag | Rot |

Ist ein Szenario aktiv, erscheint ein auffälliges Banner im Wetter-Panel.

---

## Datenquellen

| Priorität | Quelle | Beschreibung |
|-----------|--------|-------------|
| 1 | **Kachelmann Plus-API** | Beste Auflösung — erfordert kostenpflichtigen API-Key |
| 2 | **GeoSphere Austria / ZAMG** | CC BY 4.0, amtliche österreichische Messdaten + Warnungen |
| 3 | **Open-Meteo** | Kostenloses Fallback — automatisch wenn Primärquelle nicht erreichbar |
| Radar | **RainViewer** | Niederschlagsradar weltweit, kein API-Key nötig |

Die Quelle wird in der Systemadmin-Konsole konfiguriert (API-Keys in den System-Einstellungen).

---

## Datenschutz & Caching

- Wetterdaten werden serverseitig gecacht (15–30 min je nach Endpunkt)
- Es werden **keine personenbezogenen Daten** an Wetterdienste übermittelt — nur Koordinaten des Einsatzorts
- Die ZAMG-Daten (GeoSphere Austria) stehen unter **CC BY 4.0**

---

## Radar-Overlay auf der Lagekarte

In der Großschadenslage-Lagekarte kann das **Niederschlagsradar-Overlay** (RainViewer) über die Karten-Steuerung ein-/ausgeblendet werden:

- Letzte 2 Stunden (animiert rückwärts)
- Aktueller Nowcast
- Farbskala: blau (leicht) → rot (stark)

Hinweis: Das Radar-Overlay benötigt eine aktive Internetverbindung und ist nicht für den Offline-Betrieb verfügbar.
