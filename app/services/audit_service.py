
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def record_audit_event(
    db: Session,
    business_id: int,
    action_type: str,
    entity_type: str,
    entity_id: int,
    description: str,
    reason: str | None = None,
    performed_by_membership_id: int | None = None,
    actor_name: str | None = None,
    actor_email: str | None = None,
    old_values: dict[str, Any] | None = None,
    new_values: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    audit_entry = AuditLog(
        business_id=business_id,
        performed_by_membership_id=performed_by_membership_id,
        actor_name=actor_name,
        actor_email=actor_email,
        action_type=action_type,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        reason=reason,
        old_values=old_values,
        new_values=new_values,
        ip_address=ip_address,
    )

    db.add(audit_entry)

    return audit_entry
