"""
ICPS – Insurance Claim Processing System
models.py  –  All 11 ORM model definitions
"""

from __future__ import annotations

import enum
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from database import Base


# ══════════════════════════════════════════════════════════════════════════════
# Enum types
# ══════════════════════════════════════════════════════════════════════════════

class PaymentModeEnum(str, enum.Enum):
    NEFT   = "NEFT"
    RTGS   = "RTGS"
    Cheque = "Cheque"
    UPI    = "UPI"


# ══════════════════════════════════════════════════════════════════════════════
# 1.  POLICYHOLDER
# ══════════════════════════════════════════════════════════════════════════════

class Policyholder(Base):
    __tablename__ = "POLICYHOLDER"

    policyholder_id = Column(String,   primary_key=True)
    full_name       = Column(String,   nullable=False)
    dob             = Column(Date,     nullable=False)
    gender          = Column(String,   nullable=False)
    email           = Column(String,   nullable=False)
    phone           = Column(String,   nullable=False)
    address         = Column(String,   nullable=True)          # Nullable
    id_proof_type   = Column(String,   nullable=False)
    id_proof_number = Column(String,   nullable=False)
    created_at      = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("email",           name="uq_policyholder_email"),
        UniqueConstraint("id_proof_number", name="uq_policyholder_id_proof"),
    )

    # Relationships
    policies = relationship("Policy",      back_populates="policyholder",
                            cascade="all, delete-orphan")
    claims   = relationship("Claim",       back_populates="policyholder",
                            cascade="all, delete-orphan",
                            foreign_keys="[Claim.policyholder_id]")

    def __repr__(self) -> str:
        return f"<Policyholder {self.policyholder_id} – {self.full_name}>"


# ══════════════════════════════════════════════════════════════════════════════
# 2.  POLICY
# ══════════════════════════════════════════════════════════════════════════════

class Policy(Base):
    __tablename__ = "POLICY"

    policy_id        = Column(String, primary_key=True)
    policyholder_id  = Column(String, ForeignKey("POLICYHOLDER.policyholder_id",
                                                  ondelete="CASCADE"),
                              nullable=False)
    policy_number    = Column(String, nullable=False)
    policy_type      = Column(String, nullable=False)
    coverage_amount  = Column(Float,  nullable=False)
    premium_amount   = Column(Float,  nullable=False)
    start_date       = Column(Date,   nullable=False)
    end_date         = Column(Date,   nullable=False)
    status           = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint("policy_number",  name="uq_policy_number"),
        CheckConstraint("coverage_amount > 0", name="ck_policy_coverage_positive"),
        CheckConstraint("premium_amount > 0",  name="ck_policy_premium_positive"),
        CheckConstraint("end_date > start_date",
                        name="ck_policy_dates_order"),
    )

    # Relationships
    policyholder  = relationship("Policyholder", back_populates="policies")
    claims        = relationship("Claim",         back_populates="policy",
                                 cascade="all, delete-orphan",
                                 foreign_keys="[Claim.policy_id]")
    health_policy = relationship("HealthPolicy",  back_populates="policy",
                                 uselist=False, cascade="all, delete-orphan")
    vehicle_policy = relationship("VehiclePolicy", back_populates="policy",
                                  uselist=False, cascade="all, delete-orphan")
    life_policy    = relationship("LifePolicy",    back_populates="policy",
                                  uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Policy {self.policy_id} – {self.policy_number}>"


# ══════════════════════════════════════════════════════════════════════════════
# 3.  CLAIM
#     policyholder_id is a *controlled denormalization*; an event listener
#     in events.py enforces that it always matches POLICY.policyholder_id.
# ══════════════════════════════════════════════════════════════════════════════

class Claim(Base):
    __tablename__ = "CLAIM"

    claim_id        = Column(String, primary_key=True)
    policy_id       = Column(String, ForeignKey("POLICY.policy_id",
                                                  ondelete="CASCADE"),
                             nullable=False)
    # Controlled denormalization – consistency enforced via event listener
    policyholder_id = Column(String, ForeignKey("POLICYHOLDER.policyholder_id",
                                                  ondelete="CASCADE"),
                             nullable=False)
    claim_date      = Column(Date,   nullable=False)
    claim_type      = Column(String, nullable=False)
    claim_amount    = Column(Float,  nullable=False)
    description     = Column(Text,   nullable=True)            # Nullable
    status          = Column(String, nullable=False)
    incident_date   = Column(Date,   nullable=False)

    __table_args__ = (
        CheckConstraint("claim_amount > 0",
                        name="ck_claim_amount_positive"),
        CheckConstraint("incident_date <= claim_date",
                        name="ck_claim_incident_before_claim"),
    )

    # Relationships
    policy        = relationship("Policy",        back_populates="claims",
                                 foreign_keys=[policy_id])
    policyholder  = relationship("Policyholder",  back_populates="claims",
                                 foreign_keys=[policyholder_id])
    documents     = relationship("ClaimDocument", back_populates="claim",
                                 cascade="all, delete-orphan")
    verification  = relationship("Verification",  back_populates="claim",
                                 uselist=False, cascade="all, delete-orphan")
    settlement    = relationship("Settlement",    back_populates="claim",
                                 uselist=False, cascade="all, delete-orphan")
    audit_logs    = relationship("AuditLog",      back_populates="claim",
                                 cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Claim {self.claim_id} – {self.status}>"


# ══════════════════════════════════════════════════════════════════════════════
# 4.  CLAIM_DOCUMENT  (weak entity – composite PK)
# ══════════════════════════════════════════════════════════════════════════════

class ClaimDocument(Base):
    __tablename__ = "CLAIM_DOCUMENT"

    claim_id      = Column(String, ForeignKey("CLAIM.claim_id",
                                               ondelete="CASCADE"),
                           primary_key=True)
    document_id   = Column(String, primary_key=True)
    document_type = Column(String,   nullable=False)
    file_name     = Column(String,   nullable=False)
    file_path     = Column(String,   nullable=False)
    upload_date   = Column(DateTime, nullable=False, default=datetime.utcnow)
    verified_flag = Column(Boolean,  nullable=False, default=False)

    __table_args__ = (
        UniqueConstraint(
            "claim_id", "document_id", "document_type", "file_name", "upload_date",
            name="uq_claim_document_composite",
        ),
    )

    # Relationships
    claim = relationship("Claim", back_populates="documents")

    def __repr__(self) -> str:
        return f"<ClaimDocument {self.claim_id}/{self.document_id}>"


# ══════════════════════════════════════════════════════════════════════════════
# 5.  OFFICER
# ══════════════════════════════════════════════════════════════════════════════

class Officer(Base):
    __tablename__ = "OFFICER"

    officer_id  = Column(String,  primary_key=True)
    full_name   = Column(String,  nullable=False)
    email       = Column(String,  nullable=False)
    phone       = Column(String,  nullable=True)               # Nullable per spec
    department  = Column(String,  nullable=False)
    designation = Column(String,  nullable=False)
    is_active   = Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint("email", name="uq_officer_email"),
    )

    # Relationships
    verifications = relationship("Verification", back_populates="officer")

    def __repr__(self) -> str:
        return f"<Officer {self.officer_id} – {self.full_name}>"


# ══════════════════════════════════════════════════════════════════════════════
# 6.  VERIFICATION  (1:1 with CLAIM)
# ══════════════════════════════════════════════════════════════════════════════

class Verification(Base):
    __tablename__ = "VERIFICATION"

    verification_id   = Column(String, primary_key=True)
    claim_id          = Column(String, ForeignKey("CLAIM.claim_id",
                                                   ondelete="CASCADE"),
                               nullable=False)
    officer_id        = Column(String, ForeignKey("OFFICER.officer_id",
                                                   ondelete="SET NULL"),
                               nullable=True)
    verification_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    decision          = Column(String,   nullable=False)
    remarks           = Column(Text,     nullable=True)
    approved_amount   = Column(Float,    nullable=True)

    __table_args__ = (
        UniqueConstraint("claim_id", name="uq_verification_claim"),   # 1:1 enforced
        CheckConstraint("approved_amount >= 0",
                        name="ck_verification_approved_non_negative"),
    )

    # Relationships
    claim   = relationship("Claim",   back_populates="verification")
    officer = relationship("Officer", back_populates="verifications")

    def __repr__(self) -> str:
        return f"<Verification {self.verification_id} – {self.decision}>"


# ══════════════════════════════════════════════════════════════════════════════
# 7.  SETTLEMENT  (1:1 with CLAIM)
# ══════════════════════════════════════════════════════════════════════════════

class Settlement(Base):
    __tablename__ = "SETTLEMENT"

    settlement_id     = Column(String, primary_key=True)
    claim_id          = Column(String, ForeignKey("CLAIM.claim_id",
                                                   ondelete="CASCADE"),
                               nullable=False)
    settlement_date   = Column(DateTime, nullable=False, default=datetime.utcnow)
    settlement_amount = Column(Float,    nullable=False)
    payment_mode      = Column(
        Enum(PaymentModeEnum, name="payment_mode_enum", create_constraint=True),
        nullable=False,
    )
    transaction_id    = Column(String,  nullable=False)
    status            = Column(String,  nullable=False)

    __table_args__ = (
        UniqueConstraint("claim_id",       name="uq_settlement_claim"),
        UniqueConstraint("transaction_id", name="uq_settlement_txn"),
        CheckConstraint("settlement_amount > 0",
                        name="ck_settlement_amount_positive"),
    )

    # Relationships
    claim = relationship("Claim", back_populates="settlement")

    def __repr__(self) -> str:
        return f"<Settlement {self.settlement_id} – {self.status}>"


# ══════════════════════════════════════════════════════════════════════════════
# 8.  AUDIT_LOG  (append-only)
# ══════════════════════════════════════════════════════════════════════════════

class AuditLog(Base):
    __tablename__ = "AUDIT_LOG"

    log_id      = Column(String,   primary_key=True)
    claim_id    = Column(String,   ForeignKey("CLAIM.claim_id", ondelete="CASCADE"),
                         nullable=False)
    changed_by  = Column(String,   nullable=False)
    change_type = Column(String,   nullable=False)
    old_value   = Column(Text,     nullable=True)
    new_value   = Column(Text,     nullable=True)
    changed_at  = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    claim = relationship("Claim", back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog {self.log_id} – {self.change_type}>"


# ══════════════════════════════════════════════════════════════════════════════
# 9.  HEALTH_POLICY  (EER subtype – 1:1 FK to POLICY)
# ══════════════════════════════════════════════════════════════════════════════

class HealthPolicy(Base):
    __tablename__ = "HEALTH_POLICY"

    policy_id              = Column(String, ForeignKey("POLICY.policy_id",
                                                        ondelete="CASCADE"),
                                    primary_key=True)
    hospital_name          = Column(String, nullable=False)
    pre_existing_conditions = Column(Text,  nullable=True)
    coverage_type          = Column(String, nullable=False)

    # Relationships
    policy = relationship("Policy", back_populates="health_policy")

    def __repr__(self) -> str:
        return f"<HealthPolicy {self.policy_id}>"


# ══════════════════════════════════════════════════════════════════════════════
# 10. VEHICLE_POLICY  (EER subtype)
# ══════════════════════════════════════════════════════════════════════════════

class VehiclePolicy(Base):
    __tablename__ = "VEHICLE_POLICY"

    policy_id             = Column(String, ForeignKey("POLICY.policy_id",
                                                       ondelete="CASCADE"),
                                   primary_key=True)
    vehicle_registration  = Column(String, nullable=False)
    vehicle_type          = Column(String, nullable=False)
    vehicle_make_model    = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint("vehicle_registration",
                         name="uq_vehicle_registration"),
    )

    # Relationships
    policy = relationship("Policy", back_populates="vehicle_policy")

    def __repr__(self) -> str:
        return f"<VehiclePolicy {self.policy_id} – {self.vehicle_registration}>"


# ══════════════════════════════════════════════════════════════════════════════
# 11. LIFE_POLICY  (EER subtype)
# ══════════════════════════════════════════════════════════════════════════════

class LifePolicy(Base):
    __tablename__ = "LIFE_POLICY"

    policy_id         = Column(String, ForeignKey("POLICY.policy_id",
                                                    ondelete="CASCADE"),
                               primary_key=True)
    nominee_name      = Column(String, nullable=False)
    nominee_relation  = Column(String, nullable=False)
    maturity_date     = Column(Date,   nullable=False)

    # NOTE: maturity_date > start_date is validated in events.py
    #       because start_date lives in the parent POLICY table.

    # Relationships
    policy = relationship("Policy", back_populates="life_policy")

    def __repr__(self) -> str:
        return f"<LifePolicy {self.policy_id} – nominee: {self.nominee_name}>"
