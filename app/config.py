from pydantic_settings import BaseSettings, SettingsConfigDict


SECRET_KEY_PLACEHOLDER = "change-me-in-production"
BOOTSTRAP_PASSWORD_PLACEHOLDER = "admin"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "mysql+pymysql://einsatzleiter:pw@127.0.0.1:3306/einsatzleiter"
    SECRET_KEY: str = SECRET_KEY_PLACEHOLDER
    SESSION_MAX_AGE_SECONDS: int = 86400
    SESSION_INACTIVITY_SECONDS: int = 28800  # 8 h Inaktivitäts-Timeout

    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8092
    APP_BASE_URL: str = "http://localhost:8092"
    PUBLIC_BASE_URL: str = ""  # Für Mail-Links; leer = falls leer APP_BASE_URL verwenden
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False

    # Cookie-Flags
    COOKIE_SECURE: bool = False  # In Produktion auf true (HTTPS)

    VAPID_PRIVATE_KEY: str = ""
    VAPID_PUBLIC_KEY: str = ""
    VAPID_CLAIM_EMAIL: str = "admin@feuerwehr-wolfurt.at"

    BOOTSTRAP_ADMIN_USER: str = "admin"
    BOOTSTRAP_ADMIN_PASSWORD: str = ""  # Leer → wird beim ersten Start zufällig generiert

    PDF_LOGO_PATH: str = "app/static/img/logo.png"

    # IANA-Zeitzone fuer Anzeige von Datums-/Zeitwerten, wenn die Org keine eigene
    # Zeitzone konfiguriert hat. DB-Werte bleiben immer UTC.
    DEFAULT_TIMEZONE: str = "Europe/Vienna"

    # SMTP / Mail
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    SMTP_STARTTLS: bool = True
    SMTP_TIMEOUT: int = 15

    PASSWORD_RESET_TTL_MIN: int = 30

    # Login-Lockout
    LOGIN_MAX_FAILED: int = 10
    LOGIN_LOCKOUT_MINUTES: int = 15

    # Update-Mechanismus: erwarteter SHA256 der nächsten Release-ZIP (optional;
    # wenn gesetzt, muss er auch im Upload-Form vom Admin angegeben werden)
    UPDATE_ZIP_REQUIRE_HASH: bool = True

    @property
    def effective_public_base_url(self) -> str:
        return self.PUBLIC_BASE_URL or self.APP_BASE_URL


settings = Settings()


def validate_startup_secrets() -> list[str]:
    """Gibt eine Liste fataler Konfigurationsfehler zurück.
    Aufgerufen aus app.main beim Start; in Nicht-Debug-Umgebung wird hart abgebrochen.
    """
    errors: list[str] = []
    if not settings.SECRET_KEY or settings.SECRET_KEY == SECRET_KEY_PLACEHOLDER:
        errors.append("SECRET_KEY ist nicht gesetzt oder enthält Default-Platzhalter")
    if len(settings.SECRET_KEY) < 32:
        errors.append("SECRET_KEY ist kürzer als 32 Zeichen")
    return errors
