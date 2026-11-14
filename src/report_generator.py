
import csv
from pathlib import Path
from datetime import datetime


ALERT_LOG_COLUMNS = [
    "alert_id", "eval_date", "customer_id", "rule_ids",
    "raw_score", "pep_kyc_adders", "risk_multiplier",
    "merge_bonus", "weighted_score", "priority",
    "case_id", "action", "evidence_txn_ids"
]

CASE_COLUMNS = [
    "case_id", "customer_id", "opened_on", "priority",
    "state", "under_review_on", "escalated_on",
    "closed_on", "str_filed_on", "sla_breaches",
    "alert_ids"
]

CTR_COLUMNS = [
    "account_id", "customer_id", "ctr_type",
    "txn_date_or_month", "total_cash", "txn_ids", "due_date"
]

STR_COLUMNS = [
    "str_id", "case_id", "customer_id", "escalated_on",
    "filed_on", "within_sla", "total_amount",
    "evidence_txn_ids"
]


def write_csv(file_path, records, columns):
    """Write records to a CSV with an exact column order."""

    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=columns,
            extrasaction="ignore"
        )

        writer.writeheader()

        for record in records:
            writer.writerow({
                column: record.get(column, "")
                for column in columns
            })

    return path


def filter_date_range(records, date_field, from_date, to_date):
    """Filter records using inclusive date boundaries."""

    start = datetime.strptime(from_date, "%Y-%m-%d").date()
    end = datetime.strptime(to_date, "%Y-%m-%d").date()

    if end < start:
        raise ValueError("End date cannot precede start date")

    filtered = []

    for record in records:
        value = record.get(date_field)

        if not value:
            continue

        record_date = datetime.strptime(
            str(value)[:10],
            "%Y-%m-%d"
        ).date()

        if start <= record_date <= end:
            filtered.append(record)

    return filtered


def generate_alert_log(
    alert_records,
    from_date,
    to_date,
    output_dir="reports"
):
    """Generate the alert log for an inclusive date range."""

    records = filter_date_range(
        alert_records,
        "eval_date",
        from_date,
        to_date
    )

    return write_csv(
        Path(output_dir) / "alert_log.csv",
        records,
        ALERT_LOG_COLUMNS
    )


def generate_case_register(
    case_records,
    as_of_date,
    output_dir="reports"
):
    """Generate case register as of a specified date."""

    cutoff = datetime.strptime(
        as_of_date, "%Y-%m-%d"
    ).date()

    records = []

    for case in case_records:
        opened_on = case.get("opened_on", "")

        if not opened_on:
            continue

        opened_date = datetime.strptime(
            opened_on[:10], "%Y-%m-%d"
        ).date()

        if opened_date <= cutoff:
            records.append(case)

    return write_csv(
        Path(output_dir) / "case_register.csv",
        records,
        CASE_COLUMNS
    )


def build_ctr_records(
    daily_findings,
    monthly_findings,
    accounts,
    month
):
    """
    Convert daily and monthly CTR findings into report records.

    month must use YYYY-MM format.
    """

    datetime.strptime(month, "%Y-%m")

    account_to_customer = {
        account["account_id"]: account["customer_id"]
        for account in accounts
    }

    records = []

    for finding in daily_findings:
        txn_date = finding["txn_date"]

        if not txn_date.startswith(month):
            continue

        evidence = finding.get("txn_ids", [])

        transaction_ids = [
            item["txn_id"] if isinstance(item, dict) else item
            for item in evidence
        ]

        records.append({
            "account_id": finding["account_id"],
            "customer_id": account_to_customer.get(
                finding["account_id"], ""
            ),
            "ctr_type": "DAILY",
            "txn_date_or_month": txn_date,
            "total_cash": f"{float(finding['total_cash']):.2f}",
            "txn_ids": " ".join(transaction_ids),
            "due_date": finding.get("due_date", "")
        })

    for finding in monthly_findings:
        if finding["month"] != month:
            continue

        evidence = finding.get("txn_ids", [])

        transaction_ids = [
            item["txn_id"] if isinstance(item, dict) else item
            for item in evidence
        ]

        records.append({
            "account_id": finding["account_id"],
            "customer_id": account_to_customer.get(
                finding["account_id"], ""
            ),
            "ctr_type": "MONTHLY",
            "txn_date_or_month": finding["month"],
            "total_cash": f"{float(finding['total_cash']):.2f}",
            "txn_ids": " ".join(transaction_ids),
            "due_date": finding.get("due_date", "")
        })

    records.sort(
        key=lambda row: (
            row["account_id"],
            row["ctr_type"],
            row["txn_date_or_month"]
        )
    )

    return records


def generate_ctr_report(
    daily_findings,
    monthly_findings,
    accounts,
    month,
    output_dir="reports"
):
    """Generate the CTR report for a requested month."""

    records = build_ctr_records(
        daily_findings,
        monthly_findings,
        accounts,
        month
    )

    return write_csv(
        Path(output_dir) / f"ctr_{month.replace('-', '_')}.csv",
        records,
        CTR_COLUMNS
    )


def generate_str_report(
    str_records,
    from_date,
    to_date,
    output_dir="reports"
):
    """Generate the STR report for an inclusive date range."""

    filtered = filter_date_range(
        str_records,
        "filed_on",
        from_date,
        to_date
    )

    formatted_records = []
    for rec in filtered:
        evidence = rec.get("evidence_txn_ids", "")
        if isinstance(evidence, (list, tuple, set)):
            evidence_str = " ".join(evidence)
        elif isinstance(evidence, str):
            evidence_str = " ".join(evidence.replace("|", " ").split())
        else:
            evidence_str = ""

        formatted_records.append({
            "str_id": rec.get("str_id", ""),
            "case_id": rec.get("case_id", ""),
            "customer_id": rec.get("customer_id", ""),
            "escalated_on": rec.get("escalated_on", ""),
            "filed_on": rec.get("filed_on", ""),
            "within_sla": str(rec.get("within_sla", "")).lower(),
            "total_amount": f"{float(rec.get('total_amount', 0)):.2f}",
            "evidence_txn_ids": evidence_str
        })

    formatted_records.sort(key=lambda r: r["filed_on"])

    return write_csv(
        Path(output_dir) / "str_report.csv",
        formatted_records,
        STR_COLUMNS
    )
