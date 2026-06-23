"""weather_station – lokale Wetterstation je Org (Ist-Stand + Push-Token)

Die Zeitreihe (weather_reading) liegt in einer SEPARATEN Wetter-DB und wird dort
per create_all initialisiert – sie ist NICHT Teil dieser Alembic-Kette.

Revision ID: 0097
Revises: 0096
Create Date: 2026-06-23
"""
from alembic import op
from sqlalchemy import text

revision = "0097"
down_revision = "0096"
branch_labels = None
depends_on = None


def _table_exists(conn, table: str) -> bool:
    row = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.TABLES "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t"
    ), {"t": table}).scalar()
    return bool(row)


def _index_exists(conn, table: str, index: str) -> bool:
    row = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.STATISTICS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t AND INDEX_NAME = :i"
    ), {"t": table, "i": index}).scalar()
    return bool(row)


def upgrade() -> None:
    conn = op.get_bind()

    if not _table_exists(conn, "weather_station"):
        conn.execute(text("""
            CREATE TABLE weather_station (
                id                 BIGINT       NOT NULL AUTO_INCREMENT PRIMARY KEY,
                org_id             BIGINT       NOT NULL,
                name               VARCHAR(150) NOT NULL,
                quelle             VARCHAR(50)  NOT NULL DEFAULT 'davis_meteobridge',
                lat                DOUBLE       NULL,
                lng                DOUBLE       NULL,
                ingest_token_hash  VARCHAR(64)  NOT NULL,
                active             TINYINT(1)   NOT NULL DEFAULT 1,
                created_at         DATETIME     NOT NULL,
                last_seen_at       DATETIME     NULL,
                last_measured_at   DATETIME     NULL,
                last_temp_c        DOUBLE       NULL,
                last_hum_pct       DOUBLE       NULL,
                last_wind_ms       DOUBLE       NULL,
                last_gust_ms       DOUBLE       NULL,
                last_wind_dir_deg  DOUBLE       NULL,
                last_pressure_hpa  DOUBLE       NULL,
                last_rain_rate_mmh DOUBLE       NULL,
                last_rain_day_mm   DOUBLE       NULL,
                last_dewpoint_c    DOUBLE       NULL,
                last_solar_wm2     DOUBLE       NULL,
                last_uv            DOUBLE       NULL
            )
        """))

    if not _index_exists(conn, "weather_station", "ix_weather_station_org"):
        conn.execute(text(
            "CREATE INDEX ix_weather_station_org ON weather_station(org_id)"
        ))
    if not _index_exists(conn, "weather_station", "uq_weather_station_token"):
        conn.execute(text(
            "CREATE UNIQUE INDEX uq_weather_station_token ON weather_station(ingest_token_hash)"
        ))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("DROP TABLE IF EXISTS weather_station"))
