
from src.rules_engine import (
    calculate_weighted_score,
    evaluate_alert_threshold,
    calculate_merge_bonus
)


ALERT_LOG_COLUMNS = [
    "alert_id",
    "eval_date",
    "customer_id",
    "rule_ids",
    "raw_score",
    "pep_kyc_adders",
    "risk_multiplier",
    "merge_bonus",
    "weighted_score",
    "priority",
    "case_id",
    "action",
    "evidence_txn_ids"
]


def resolve_customer_id(finding, accounts):
    """Resolve customer ID from a finding or its account."""

    customer_id = finding.get("customer_id")

    if customer_id:
        return customer_id

    account_id = finding.get("account_id")

    for account in accounts:
        if account["account_id"] == account_id:
            return account["customer_id"]

    raise ValueError(
        f"Cannot resolve customer for account: {account_id}"
    )


def get_evidence_transaction_ids(finding):
    """Extract evidence transaction IDs from any supported finding."""

    evidence = finding.get("evidence_txn_ids")

    if evidence is None:
        evidence = finding.get("txn_ids", [])

    if not evidence and finding.get("transaction_id"):
        evidence = [finding["transaction_id"]]

    transaction_ids = []

    for item in evidence:
        if isinstance(item, dict):
            txn_id = item.get("txn_id")
        else:
            txn_id = item

        if txn_id and txn_id not in transaction_ids:
            transaction_ids.append(txn_id)

    return transaction_ids


def get_rule_ids(finding, additional_rule_ids=None):
    """Collect and normalize all rule IDs for an alert."""

    rule_ids = []

    rule_id = finding.get("rule_id")

    if rule_id:
        rule_ids.append(rule_id)

    additional_rule_id = finding.get("additional_rule_id")

    if additional_rule_id:
        rule_ids.append(additional_rule_id)

    if additional_rule_ids:
        rule_ids.extend(additional_rule_ids)

    # Preserve order while removing duplicates.
    return list(dict.fromkeys(rule_ids))


def calculate_alert_score(
    raw_score,
    risk_rating,
    pep_kyc_adders=0,
    merge_count=0
):
    """
    Apply BR-16 scoring order:

    1. Base rule score.
    2. PEP/KYC adders.
    3. Risk multiplier.
    4. Merge bonus.
    """

    if raw_score < 0:
        raise ValueError("Raw score cannot be negative")

    if pep_kyc_adders < 0:
        raise ValueError("PEP/KYC adders cannot be negative")

    if merge_count < 0:
        raise ValueError("Merge count cannot be negative")

    adjusted_raw_score = raw_score + pep_kyc_adders

    weighted_result = calculate_weighted_score(
        adjusted_raw_score,
        risk_rating
    )

    merge_bonus = calculate_merge_bonus(merge_count)

    weighted_score = round(
        weighted_result["weighted_score"] + merge_bonus,
        1
    )

    threshold_result = evaluate_alert_threshold(
        weighted_score
    )

    return {
        "raw_score": raw_score,
        "pep_kyc_adders": pep_kyc_adders,
        "risk_rating": weighted_result["risk_rating"],
        "risk_multiplier": weighted_result["risk_multiplier"],
        "merge_bonus": merge_bonus,
        "weighted_score": weighted_score,
        "alert_required": threshold_result["alert_required"],
        "priority": threshold_result["priority"]
    }


def build_alert_record(
    finding,
    customer,
    accounts,
    evaluation_date,
    alert_id,
    case_id="",
    pep_kyc_adders=0,
    merge_count=0,
    str_filed=False,
    action="NEW",
    additional_rule_ids=None
):
    """
    Build one alert-log record.

    Returns None when the score is below threshold
    and the STR-filed override does not apply.
    """

    if action not in {"NEW", "MERGED"}:
        raise ValueError(f"Invalid alert action: {action}")

    customer_id = resolve_customer_id(
        finding,
        accounts
    )

    if customer_id != customer.get("customer_id"):
        raise ValueError(
            "Finding customer ID does not match customer record"
        )

    raw_score = finding.get(
        "raw_score",
        finding.get("score")
    )

    if raw_score is None:
        raise ValueError(
            f"Missing raw score for rule: {finding.get('rule_id')}"
        )

    scoring = calculate_alert_score(
        raw_score=float(raw_score),
        risk_rating=customer["risk_rating"],
        pep_kyc_adders=pep_kyc_adders,
        merge_count=merge_count
    )

    # STR-filed customers receive priority override.
    alert_required = (
        scoring["alert_required"] or str_filed
    )

    if not alert_required:
        return None

    priority = (
        scoring["priority"] or str_filed
    )

    rule_ids = get_rule_ids(
        finding,
        additional_rule_ids
    )

    evidence_ids = get_evidence_transaction_ids(
        finding
    )

    if not rule_ids:
        raise ValueError("Alert must contain at least one rule ID")

    return {
        "alert_id": alert_id,
        "eval_date": evaluation_date,
        "customer_id": customer_id,
        "rule_ids": "|".join(rule_ids),
        "raw_score": round(float(raw_score), 1),
        "pep_kyc_adders": pep_kyc_adders,
        "risk_multiplier": scoring["risk_multiplier"],
        "merge_bonus": scoring["merge_bonus"],
        "weighted_score": scoring["weighted_score"],
        "priority": priority,
        "case_id": case_id,
        "action": action,
        "evidence_txn_ids": "|".join(evidence_ids)
    }
