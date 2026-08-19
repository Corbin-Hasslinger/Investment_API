
from uuid import UUID

from sqlmodel import col, select

from atlas_api.schemas.security import SecurityUpdate
from atlas_api.tools.errors import SecurityNotFoundError

from ..models import Security


class SecurityRepository:
    def __init__(self, session):
        self.session = session

    @property
    def model_type(self) -> type[Security]:
        return Security

    def commit(self) -> None:
        self.session.commit()

    def refresh(self, security: Security) -> None:
        self.session.refresh(security)

    def create_security(self, security: Security) -> Security:
        self.session.add(security)
        self.session.flush()
        return security

    def get_security_by_id(self, security_id: UUID) -> Security | None:
        return self.session.exec(
            select(Security).where(Security.id == security_id)
        ).first()

    def get_all_securities(self) -> list[Security]:
        return self.session.exec(
            select(Security).order_by(col(Security.symbol).asc(), col(Security.id).asc())
        ).all()

    def update_security(self, security_id: UUID, payload: SecurityUpdate) -> Security:
        security = self.get_security_by_id(security_id)
        if security:
            for key, value in payload.model_dump(exclude_unset=True).items():
                setattr(security, key, value)
            self.session.add(security)
            self.session.flush()
            return security
        raise SecurityNotFoundError(f"Security with ID {security_id} not found")

    def delete_security(self, security_id: UUID) -> None:
        security = self.get_security_by_id(security_id)
        if security:
            self.session.delete(security)
            return
        raise SecurityNotFoundError(f"Security with ID {security_id} not found")

    def get_security_by_symbol(self, symbol: str) -> Security | None:
        """Retrieve a Security by its canonical symbol.
        
        Returns None if not found (does not check upstream).
        Symbol should be pre-normalized.
        """
        return self.session.exec(
            select(Security).where(Security.symbol == symbol)
        ).first()

