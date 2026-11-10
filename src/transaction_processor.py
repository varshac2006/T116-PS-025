
import math
from datetime import datetime


VALID_TRANSACTION_TYPES = {
    "CASH_DEPOSIT",
    "CASH_WITHDRAWAL",
    "TRANSFER_IN",
    "TRANSFER_OUT",
    "INTEREST_CREDIT"
}

VALID_CHANNELS = {
    "BRANCH",
    "ATM",
    "NEFT",
    "RTGS",
    "IMPS",
    "UPI",
    "SYSTEM"
}


REQUIRED_FIELDS = [
    "txn_id",
    "account_id",
    "txn_ts",
    "txn_type",
    "amount",
    "channel"
]


def validate_transaction(transaction, valid_account_ids=None,
                         valid_branch_ids=None):
    """Validate one transaction and return its errors."""

    errors = []

    # Check required fields
    for field in REQUIRED_FIELDS:
        if not str(transaction.get(field, "")).strip():
            errors.append(f"Missing {field}")

    if errors:
        return errors

    # Check transaction ID
    txn_id = transaction["txn_id"].strip()

    if not txn_id:
        errors.append("Invalid transaction ID")

    # Check account ID
    account_id = transaction["account_id"].strip()

    if valid_account_ids is not None:
        if account_id not in valid_account_ids:
            errors.append("Unknown account ID")

    # Check transaction timestamp
    try:
        datetime.strptime(
            transaction["txn_ts"].strip(),
            "%Y-%m-%d %H:%M:%S"
        )
    except ValueError:
        errors.append("Invalid transaction timestamp")

    # Check transaction type
    txn_type = transaction["txn_type"].strip().upper()

    if txn_type not in VALID_TRANSACTION_TYPES:
        errors.append("Invalid transaction type")

    # Check amount
    try:
        amount = float(transaction["amount"])

        if not math.isfinite(amount):
            errors.append("Amount must be finite")
        elif amount <= 0:
            errors.append("Amount must be greater than zero")

    except (ValueError, TypeError):
        errors.append("Invalid transaction amount")

    # Check channel
    channel = transaction["channel"].strip().upper()

    if channel not in VALID_CHANNELS:
        errors.append("Invalid transaction channel")

    # Check branch ID when supplied
    branch_id = str(transaction.get("branch_id", "")).strip()

    if branch_id and valid_branch_ids is not None:
        if branch_id not in valid_branch_ids:
            errors.append("Unknown branch ID")

    return errors


def process_transactions(transactions, valid_account_ids=None,
                         valid_branch_ids=None):
    """
    Validate transactions and remove duplicate transaction IDs.

    Returns valid transactions, invalid records, and duplicates.
    """

    valid_transactions = []
    invalid_records = []
    duplicate_records = []

    seen_transaction_ids = set()

    for transaction in transactions:

        txn_id = str(transaction.get("txn_id", "")).strip()

        # Detect duplicate transaction IDs
        if txn_id and txn_id in seen_transaction_ids:
            duplicate_records.append({
                "txn_id": txn_id,
                "reason": "Duplicate transaction ID"
            })
            continue

        if txn_id:
            seen_transaction_ids.add(txn_id)

        # Validate transaction
        errors = validate_transaction(
            transaction,
            valid_account_ids,
            valid_branch_ids
        )

        if errors:
            invalid_records.append({
                "txn_id": txn_id,
                "errors": errors,
                "transaction": transaction
            })
        else:
            valid_transactions.append(dict(transaction))

    return {
        "valid_transactions": valid_transactions,
        "invalid_records": invalid_records,
        "duplicate_records": duplicate_records
    }
