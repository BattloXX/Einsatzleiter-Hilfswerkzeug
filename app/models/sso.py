from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class OrgSsoConfig(Base):
    """Entra-ID/OIDC-Verbindung einer Organisation (1:1 je Org)."""
    __tablename__ = "org_sso_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    org_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("fire_dept.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Entra-Verbindung
    tenant_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    client_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    client_secret_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    authority_base: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Provisioning / Sicherheit
    allowed_domains: Mapped[str | None] = mapped_column(String(500), nullable=True)
    default_role_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("role.id"), nullable=True)
    deny_if_no_group: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sync_profile: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    enforce_sso: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    org: Mapped[object] = relationship("FireDept", foreign_keys=[org_id], lazy="joined")
    group_mappings: Mapped[list[OrgSsoGroupMap]] = relationship(
        back_populates="config", cascade="all, delete-orphan", lazy="selectin"
    )
    default_role: Mapped[object | None] = relationship(
        "Role", foreign_keys=[default_role_id], lazy="joined"
    )

    @property
    def allowed_domain_list(self) -> list[str]:
        if not self.allowed_domains:
            return []
        return [d.strip().lower() for d in self.allowed_domains.split(",") if d.strip()]

    @property
    def is_fully_configured(self) -> bool:
        return bool(self.tenant_id and self.client_id and self.client_secret_enc)


class OrgSsoGroupMap(Base):
    """Mapping: Entra-Sicherheitsgruppe (Object ID) → App-Rolle, je Org."""
    __tablename__ = "org_sso_group_map"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    config_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("org_sso_config.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entra_group_id: Mapped[str] = mapped_column(String(36), nullable=False)
    label: Mapped[str | None] = mapped_column(String(150), nullable=True)
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("role.id", ondelete="CASCADE"), nullable=False)

    config: Mapped[OrgSsoConfig] = relationship(back_populates="group_mappings")
    role: Mapped[object] = relationship("Role", lazy="joined")
