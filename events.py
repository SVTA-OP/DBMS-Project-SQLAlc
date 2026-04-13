"""
ICPS – Insurance Claim Processing System
events.py  –  SQLAlchemy Event Listeners (simulate database triggers)

Business Rules enforced here
─────────────────────────────
BR-1  Claim.policyholder_id must always equal the policyholder_id of the
      Policy referenced by Claim.policy_id.  This is the controlled-
      denormalization consistency rule documented in the normalisation report.

BR-2  LifePolicy.maturity_date must be later than the parent Policy.start_date.
      (Cannot be expressed as a simple CHECK constraint because start_date
       lives in a different table.)
"""

from sqlalchemy import event, inspect

from models import Claim, LifePolicy


# ══════════════════════════════════════════════════════════════════════════════
#  Helper – resolve a Policy row from within an event hook
# ══════════════════════════════════════════════════════════════════════════════

def _get_policy(session, policy_id: str):
    """
    Look up a Policy by its PK using the active Session.
    Works both inside and outside a unit-of-work flush.
    """
    from models import Policy  # local import avoids circular dependency
    return session.get(Policy, policy_id)


# ══════════════════════════════════════════════════════════════════════════════
#  BR-1  CLAIM  –  policyholder_id must match POLICY.policyholder_id
# ══════════════════════════════════════════════════════════════════════════════

def _enforce_claim_policyholder(mapper, connection, target):
    """
    Fired before INSERT and before UPDATE on CLAIM.
    Raises ValueError if Claim.policyholder_id != Policy.policyholder_id.
    """
    # We need to read the parent policy; use the Session attached to the target.
    session = inspect(target).session
    if session is None:
        # Object is being inserted outside a session – skip (unit tests may do this)
        return

    policy = _get_policy(session, target.policy_id)
    if policy is None:
        raise ValueError(
            f"[BR-1] No Policy found with policy_id='{target.policy_id}'."
        )
    if policy.policyholder_id != target.policyholder_id:
        raise ValueError(
            f"[BR-1] Claim.policyholder_id='{target.policyholder_id}' "
            f"does not match Policy.policyholder_id='{policy.policyholder_id}' "
            f"for policy_id='{target.policy_id}'. "
            "Controlled-denormalisation consistency violated."
        )


event.listen(Claim, "before_insert", _enforce_claim_policyholder)
event.listen(Claim, "before_update", _enforce_claim_policyholder)


# ══════════════════════════════════════════════════════════════════════════════
#  BR-2  LIFE_POLICY  –  maturity_date > Policy.start_date
# ══════════════════════════════════════════════════════════════════════════════

def _enforce_life_policy_maturity(mapper, connection, target):
    """
    Fired before INSERT and before UPDATE on LIFE_POLICY.
    Raises ValueError if maturity_date <= Policy.start_date.
    """
    session = inspect(target).session
    if session is None:
        return

    policy = _get_policy(session, target.policy_id)
    if policy is None:
        raise ValueError(
            f"[BR-2] No Policy found with policy_id='{target.policy_id}'."
        )
    if target.maturity_date <= policy.start_date:
        raise ValueError(
            f"[BR-2] LifePolicy.maturity_date ({target.maturity_date}) "
            f"must be after Policy.start_date ({policy.start_date})."
        )


event.listen(LifePolicy, "before_insert", _enforce_life_policy_maturity)
event.listen(LifePolicy, "before_update", _enforce_life_policy_maturity)
