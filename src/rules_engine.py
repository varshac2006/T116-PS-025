
from collections import defaultdict
from datetime import datetime, timedelta


# Official AML thresholds
CTR_THRESHOLD = 1_000_000
STRUCTURING_MIN = 900_000
STRUCTURING_MAX = 999_999
STRUCTURING_MIN_COUNT = 3
STRUCTURING_WINDOW_DAYS = 7

# Velocity thresholds
VELOCITY_WINDOW_DAYS = 30
VELOCITY_NEW_ACCOUNT_DAYS = 90
NEW_ACCOUNT_TURNOVER = 200_000


def parse_timestamp(value):
    """Convert transaction timestamp into a datetime object."""
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


def get_cash_transactions(transactions):
    """Return valid cash deposits and withdrawals."""
    return [
        txn for txn in transactions
        if txn["txn_type"] in {"CASH_DEPOSIT", "CASH_WITHDRAWAL"}
    ]


def detect_daily_ctr(transactions):
    """
    Detect daily cash transactions exceeding Rs 10 lakh
    for an individual account.
    """

    grouped = defaultdict(list)

    for txn in get_cash_transactions(transactions):
        timestamp = parse_timestamp(txn["txn_ts"])
        key = (txn["account_id"], timestamp.date())
        grouped[key].append(txn)

    alerts = []

    for (account_id, txn_date), records in grouped.items():
        total_cash = sum(float(txn["amount"]) for txn in records)

        if total_cash > CTR_THRESHOLD:
            alerts.append({
                "rule_id": "BR-01",
                "account_id": account_id,
                "txn_date": txn_date.isoformat(),
                "total_cash": round(total_cash, 2),
                "txn_ids": sorted(
                    records,
                    key=lambda txn: parse_timestamp(txn["txn_ts"])
                )
            })

    return alerts


def detect_monthly_ctr(transactions):
    """
    Detect monthly cash transactions exceeding Rs 10 lakh
    for an individual account.
    """

    grouped = defaultdict(list)

    for txn in get_cash_transactions(transactions):
        timestamp = parse_timestamp(txn["txn_ts"])
        key = (txn["account_id"], timestamp.strftime("%Y-%m"))
        grouped[key].append(txn)

    alerts = []

    for (account_id, month), records in grouped.items():
        total_cash = sum(float(txn["amount"]) for txn in records)

        if total_cash > CTR_THRESHOLD:
            alerts.append({
                "rule_id": "BR-02",
                "account_id": account_id,
                "month": month,
                "total_cash": round(total_cash, 2),
                "txn_ids": sorted(
                    records,
                    key=lambda txn: parse_timestamp(txn["txn_ts"])
                )
            })

    return alerts


def detect_structuring(transactions, accounts):
    """
    Detect 3 or more cash deposits between Rs 9 lakh
    and Rs 9,99,999 within an inclusive rolling 7-day window.

    Adds 20 points when deposits occur at 2 or more branches.
    """

    account_to_customer = {
        account["account_id"]: account["customer_id"]
        for account in accounts
    }

    grouped = defaultdict(list)

    for txn in transactions:
        if txn["txn_type"] != "CASH_DEPOSIT":
            continue

        amount = float(txn["amount"])

        if STRUCTURING_MIN <= amount <= STRUCTURING_MAX:
            grouped[txn["account_id"]].append(txn)

    findings = []

    for account_id, records in grouped.items():

        records.sort(key=lambda txn: parse_timestamp(txn["txn_ts"]))

        for start_index in range(len(records)):

            window_start = parse_timestamp(
                records[start_index]["txn_ts"]
            )

            window_records = []

            for txn in records[start_index:]:
                current_time = parse_timestamp(txn["txn_ts"])

                if current_time - window_start <= timedelta(
                    days=STRUCTURING_WINDOW_DAYS
                ):
                    window_records.append(txn)
                else:
                    break

            if len(window_records) < STRUCTURING_MIN_COUNT:
                continue

            branch_ids = {
                txn["branch_id"]
                for txn in window_records
                if txn.get("branch_id", "").strip()
            }

            raw_score = 40

            if len(branch_ids) >= 2:
                raw_score += 20

            finding = {
                "rule_id": "BR-03",
                "customer_id": account_to_customer.get(account_id),
                "account_id": account_id,
                "raw_score": raw_score,
                "branch_bonus": 20 if len(branch_ids) >= 2 else 0,
                "evidence_txn_ids": [
                    txn["txn_id"] for txn in window_records
                ],
                "evidence_transactions": window_records,
                "window_start": window_start,
                "window_end": parse_timestamp(
                    window_records[-1]["txn_ts"]
                )
            }

            evidence_ids = set(finding["evidence_txn_ids"])

            already_found = any(
                existing["account_id"] == account_id
                and set(existing["evidence_txn_ids"]) == evidence_ids
                for existing in findings
            )

            if not already_found:
                findings.append(finding)

    return findings


def detect_velocity(transactions, accounts, customers, evaluation_date):
    """
    Detect incoming credits exceeding expected monthly turnover
    within a rolling 30-day period.

    More than 3 times turnover: score 30.
    More than 5 times turnover: score 50.

    Accounts younger than 90 days use Rs 2 lakh
    as their expected monthly turnover.
    """

    if isinstance(evaluation_date, str):
        evaluation_date = datetime.strptime(
            evaluation_date, "%Y-%m-%d"
        ).date()

    evaluation_end = datetime.combine(
        evaluation_date,
        datetime.max.time()
    )

    window_start = evaluation_end - timedelta(
        days=VELOCITY_WINDOW_DAYS
    )

    account_details = {
        account["account_id"]: account
        for account in accounts
    }

    customer_details = {
        customer["customer_id"]: customer
        for customer in customers
    }

    # Only incoming credits are considered.
    credit_types = {
        "CASH_DEPOSIT",
        "TRANSFER_IN"
    }

    grouped = defaultdict(list)

    for txn in transactions:

        if txn["txn_type"] not in credit_types:
            continue

        timestamp = parse_timestamp(txn["txn_ts"])

        if window_start <= timestamp <= evaluation_end:
            grouped[txn["account_id"]].append(txn)

    findings = []

    for account_id, records in grouped.items():

        account = account_details.get(account_id)

        if account is None:
            continue

        customer_id = account["customer_id"]
        customer = customer_details.get(customer_id)

        if customer is None:
            continue

        # Calculate account age on the evaluation date.
        open_date = datetime.strptime(
            account["open_date"], "%Y-%m-%d"
        ).date()

        account_age = (evaluation_date - open_date).days

        # Use Rs 2 lakh for accounts younger than 90 days.
        if account_age < VELOCITY_NEW_ACCOUNT_DAYS:
            expected_turnover = NEW_ACCOUNT_TURNOVER
        else:
            expected_turnover = float(
                customer["expected_monthly_turnover"]
            )

        if expected_turnover <= 0:
            continue

        total_credits = sum(
            float(txn["amount"]) for txn in records
        )

        turnover_multiple = total_credits / expected_turnover

        # Strictly greater than 5 times.
        if turnover_multiple > 5:
            raw_score = 50

        # Strictly greater than 3 times.
        elif turnover_multiple > 3:
            raw_score = 30

        else:
            continue

        records.sort(
            key=lambda txn: parse_timestamp(txn["txn_ts"])
        )

        findings.append({
            "rule_id": "BR-04",
            "customer_id": customer_id,
            "account_id": account_id,
            "raw_score": raw_score,
            "total_credits": round(total_credits, 2),
            "expected_turnover": expected_turnover,
            "turnover_multiple": round(turnover_multiple, 2),
            "evidence_txn_ids": [
                txn["txn_id"] for txn in records
            ],
            "evidence_transactions": records,
            "window_start": window_start,
            "window_end": evaluation_end
        })

    return findings

# Rapid movement thresholds
RAPID_MOVEMENT_MIN_CREDIT = 200_000
RAPID_MOVEMENT_RATIO = 0.80
RAPID_MOVEMENT_WINDOW_HOURS = 48

RAPID_MOVEMENT_SCORE = 35
ROUND_TRIP_BONUS = 25


def detect_rapid_movement(transactions):
    """
    Detect incoming credits above Rs 2 lakh where
    at least 80% is transferred out within 48 hours.

    Adds 25 points if the same counterparty is involved
    in the incoming and outgoing transactions.
    """

    grouped = defaultdict(list)

    for txn in transactions:
        grouped[txn["account_id"]].append(txn)

    findings = []

    credit_types = {
        "CASH_DEPOSIT",
        "TRANSFER_IN"
    }

    for account_id, records in grouped.items():

        records.sort(
            key=lambda txn: parse_timestamp(txn["txn_ts"])
        )

        incoming_transactions = [
            txn for txn in records
            if txn["txn_type"] in credit_types
            and float(txn["amount"]) > RAPID_MOVEMENT_MIN_CREDIT
        ]

        outgoing_transactions = [
            txn for txn in records
            if txn["txn_type"] == "TRANSFER_OUT"
        ]

        for credit in incoming_transactions:

            credit_time = parse_timestamp(credit["txn_ts"])
            credit_amount = float(credit["amount"])

            window_end = credit_time + timedelta(
                hours=RAPID_MOVEMENT_WINDOW_HOURS
            )

            matching_outgoing = []

            for outgoing in outgoing_transactions:

                outgoing_time = parse_timestamp(
                    outgoing["txn_ts"]
                )

                if credit_time < outgoing_time <= window_end:
                    matching_outgoing.append(outgoing)

            total_outgoing = sum(
                float(txn["amount"])
                for txn in matching_outgoing
            )

            if total_outgoing < credit_amount * RAPID_MOVEMENT_RATIO:
                continue

            same_counterparty = False

            incoming_counterparty = (
                credit.get("counterparty_account", "").strip()
            )

            if incoming_counterparty:
                for outgoing in matching_outgoing:
                    outgoing_counterparty = (
                        outgoing.get("counterparty_account", "").strip()
                    )

                    if outgoing_counterparty == incoming_counterparty:
                        same_counterparty = True
                        break

            raw_score = RAPID_MOVEMENT_SCORE

            if same_counterparty:
                raw_score += ROUND_TRIP_BONUS

            evidence = [credit] + matching_outgoing

            evidence.sort(
                key=lambda txn: parse_timestamp(txn["txn_ts"])
            )

            findings.append({
                "rule_id": "BR-05",
                "additional_rule_id": (
                    "BR-06" if same_counterparty else None
                ),
                "account_id": account_id,
                "customer_id": None,
                "raw_score": raw_score,
                "credit_amount": credit_amount,
                "total_outgoing": round(total_outgoing, 2),
                "outgoing_percentage": round(
                    (total_outgoing / credit_amount) * 100, 2
                ),
                "round_trip_detected": same_counterparty,
                "evidence_txn_ids": [
                    txn["txn_id"] for txn in evidence
                ],
                "evidence_transactions": evidence,
                "window_start": credit_time,
                "window_end": window_end
            })

    return findings

def detect_dormant_reactivation(
    transactions,
    prior_transactions,
    accounts,
    evaluation_date
):
    """
    BR-07: Detect dormant accounts that become active again.

    Conditions:
    1. No customer-initiated transaction for at least 365 days.
    2. More than Rs. 5,00,000 in activity within the latest 30 days.
    3. INTEREST_CREDIT does not count as customer activity.
    """

    if isinstance(evaluation_date, str):
        evaluation_date = datetime.strptime(
            evaluation_date, "%Y-%m-%d"
        ).date()
    elif isinstance(evaluation_date, datetime):
        evaluation_date = evaluation_date.date()

    end_time = datetime.combine(
        evaluation_date,
        datetime.max.time()
    )
    start_time = end_time - timedelta(days=30)

    # Combine historical and current transactions.
    combined_transactions = []
    seen_ids = set()

    for txn in list(prior_transactions) + list(transactions):
        txn_id = txn.get("txn_id")

        # Avoid counting duplicate transaction IDs twice.
        if txn_id in seen_ids:
            continue

        seen_ids.add(txn_id)
        combined_transactions.append(txn)

    # Support accounts stored as either a dictionary or a list.
    if isinstance(accounts, dict):
        account_records = list(accounts.values())
    else:
        account_records = list(accounts)

    findings = []

    for account in account_records:
        account_id = account.get("account_id")
        customer_id = account.get("customer_id")

        account_txns = []

        for txn in combined_transactions:
            if txn.get("account_id") != account_id:
                continue

            txn_time = parse_timestamp(txn.get("txn_ts"))

            if txn_time is None or txn_time > end_time:
                continue

            account_txns.append((txn_time, txn))

        account_txns.sort(key=lambda item: item[0])

        # Ignore interest credits when checking customer activity.
        customer_txns = [
            (txn_time, txn)
            for txn_time, txn in account_txns
            if txn.get("txn_type") != "INTEREST_CREDIT"
        ]

        # Activity during the latest 30-day window.
        recent_activity = [
            (txn_time, txn)
            for txn_time, txn in customer_txns
            if start_time < txn_time <= end_time
        ]

        if not recent_activity:
            continue

        first_activity_time = recent_activity[0][0]

        # Find the last customer transaction before reactivation.
        previous_activity = [
            txn_time
            for txn_time, txn in customer_txns
            if txn_time < first_activity_time
        ]

        if not previous_activity:
            continue

        last_activity_time = max(previous_activity)

        # Require at least 365 days of inactivity.
        if first_activity_time - last_activity_time < timedelta(days=365):
            continue

        total_amount = sum(
            float(txn.get("amount", 0))
            for txn_time, txn in recent_activity
        )

        # Strictly greater than Rs. 5 lakh.
        if total_amount <= 500000:
            continue

        evidence_ids = [
            txn.get("txn_id")
            for txn_time, txn in recent_activity
        ]

        findings.append({
            "rule_id": "BR-07",
            "account_id": account_id,
            "customer_id": customer_id,
            "total_amount": total_amount,
            "score": 30,
            "evaluation_date": evaluation_date.isoformat(),
            "evidence_txn_ids": evidence_ids
        })

    return findings

def detect_pep_alerts(transactions, customers, accounts):
    """
    BR-08: Detect high-value transactions involving PEP customers
    and customers linked to PEP family members.
    """

    customer_records = {
        customer["customer_id"]: customer
        for customer in customers
    }

    account_customers = {
        account["account_id"]: account["customer_id"]
        for account in accounts
    }

    pep_customers = set()

    for customer in customers:
        if str(customer.get("pep_flag", "")).strip().upper() in {
            "TRUE", "YES", "1"
        }:
            pep_customers.add(customer["customer_id"])

    # Include customers linked to a PEP.
    for customer in customers:
        linked_customer = customer.get(
            "pep_linked_customer", ""
        )

        if linked_customer in pep_customers:
            pep_customers.add(customer["customer_id"])

    findings = []

    for txn in transactions:
        customer_id = account_customers.get(
            txn.get("account_id")
        )

        if customer_id not in pep_customers:
            continue

        try:
            amount = float(txn.get("amount", 0))
        except (ValueError, TypeError):
            continue

        if amount > 500000:
            findings.append({
                "rule_id": "BR-08",
                "customer_id": customer_id,
                "account_id": txn.get("account_id"),
                "transaction_id": txn.get("txn_id"),
                "amount": amount,
                "raw_score": 20
            })

    return findings

def detect_kyc_alerts(transactions, customers, accounts):
    """
    BR-09: Detect credits above Rs. 1 lakh
    when the customer's KYC has expired.

    KYC remains valid through its expiry date.
    It is expired only after that date.
    """

    customer_records = {
        customer["customer_id"]: customer
        for customer in customers
    }

    account_customers = {
        account["account_id"]: account["customer_id"]
        for account in accounts
    }

    findings = []

    for txn in transactions:
        customer_id = account_customers.get(
            txn.get("account_id")
        )

        customer = customer_records.get(customer_id)

        if not customer:
            continue

        if txn.get("txn_type") not in {
            "CASH_DEPOSIT",
            "TRANSFER_IN"
        }:
            continue

        try:
            amount = float(txn.get("amount", 0))
            txn_date = parse_timestamp(txn["txn_ts"]).date()
            expiry_date = datetime.strptime(
                customer["kyc_expiry_date"],
                "%Y-%m-%d"
            ).date()
        except (ValueError, TypeError, KeyError):
            continue

        if txn_date > expiry_date and amount > 100000:
            findings.append({
                "rule_id": "BR-09",
                "customer_id": customer_id,
                "account_id": txn["account_id"],
                "transaction_id": txn["txn_id"],
                "amount": amount,
                "raw_score": 15
            })

    return findings

def calculate_weighted_score(raw_score, risk_rating):
    """
    BR-10: Apply customer risk multipliers.
    """

    risk_multipliers = {
        "LOW": 0.8,
        "MEDIUM": 1.0,
        "HIGH": 1.5
    }

    risk_rating = str(risk_rating).strip().upper()

    if risk_rating not in risk_multipliers:
        raise ValueError(
            f"Invalid risk rating: {risk_rating}"
        )

    multiplier = risk_multipliers[risk_rating]

    weighted_score = raw_score * multiplier

    return {
        "raw_score": raw_score,
        "risk_rating": risk_rating,
        "risk_multiplier": multiplier,
        "weighted_score": weighted_score
    }

def evaluate_alert_threshold(weighted_score):
    """
    BR-11: Determine whether an alert should be generated
    and whether it should be marked as priority.
    """
    if weighted_score >= 70:
        return {
            "alert_required": True,
            "priority": True,
            "status": "PRIORITY"
        }

    elif weighted_score >= 50:
        return {
            "alert_required": True,
            "priority": False,
            "status": "NORMAL"
        }

    else:
        return {
            "alert_required": False,
            "priority": False,
            "status": "NO ALERT"
        }


def calculate_merge_bonus(merge_count):
    """
    BR-12: Calculate bonus points for merged alerts.
    """
    bonus = min(merge_count * 5, 20)
    return bonus


def should_merge_alert(
    existing_customer_id,
    new_customer_id,
    existing_rule_id,
    new_rule_id,
    existing_date,
    new_date,
    case_state
):
    """
    BR-12: Check whether a new alert should merge
    into an existing open case.
    """
    if existing_customer_id != new_customer_id:
        return False

    if existing_rule_id != new_rule_id:
        return False

    if case_state not in ["OPEN", "UNDER_REVIEW", "ESCALATED"]:
        return False

    old_date = datetime.strptime(existing_date, "%Y-%m-%d")
    current_date = datetime.strptime(new_date, "%Y-%m-%d")

    days_difference = (current_date - old_date).days

    return 0 <= days_difference <= 7
