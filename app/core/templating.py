"""Zentrale Jinja2Templates-Instanz inklusive Filter-Registry.

Alle Router importieren `templates` von hier statt eigene Instanzen zu bauen.
Damit teilen sie sich dieselbe Jinja-Environment und die Filter (z. B.
`local_time`, `local_datetime`) sind ueberall verfuegbar.

Die Zeitzonen-Filter lesen das User-Objekt aus dem Jinja-Kontext (immer als
`user` uebergeben), entnehmen dort `user.org` und formatieren das datetime in
der jeweiligen Org-Zeitzone. Faellt auf settings.DEFAULT_TIMEZONE zurueck,
wenn weder User noch Org-Zeitzone bekannt sind.
"""
from fastapi.templating import Jinja2Templates
from jinja2 import pass_context

from app.core.timezones import (
    format_local_datetime,
    format_local_iso,
    format_local_time,
    to_org_tz,
)


def _ctx_org(ctx):
    user = ctx.get("user") if ctx else None
    return getattr(user, "org", None) if user else None


@pass_context
def _local_time(ctx, dt):
    return format_local_time(dt, _ctx_org(ctx))


@pass_context
def _local_datetime(ctx, dt):
    return format_local_datetime(dt, _ctx_org(ctx))


@pass_context
def _local_iso(ctx, dt):
    return format_local_iso(dt, _ctx_org(ctx))


@pass_context
def _local(ctx, dt):
    """Konvertiert ein datetime in die Org-Zeitzone (gibt datetime zurueck).
    Verwendung in Templates fuer exotische Formate:
        {{ (dt|local).strftime('%d.%m. %H:%M:%S') }}
    """
    return to_org_tz(dt, _ctx_org(ctx))


templates = Jinja2Templates(directory="app/templates")
templates.env.filters["local"] = _local
templates.env.filters["local_time"] = _local_time
templates.env.filters["local_datetime"] = _local_datetime
templates.env.filters["local_iso"] = _local_iso
