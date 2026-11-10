
from pathlib import Path

from src.data_loader import (
    load_accounts,
    load_customers,
    load_daily_transactions,
    load_prior_transactions
)

from src.transaction_processor import process_transactions

from src.rules_engine import (
    detect_daily_ctr,
    detect_monthly_ctr,
    detect_structuring,
    detect_velocity,
    detect_rapid_movement,
    detect_dormant_reactivation,
    detect_pep_alerts,
    detect_kyc_alerts
)


# Load master data
accounts = load_accounts()
customers = load_customers()
prior_transactions = load_prior_transactions()

account_ids = {
    account["account_id"] for account in accounts
}

# Load all daily transaction files
all_transactions = []

for file_path in sorted(Path("data/transactions").glob("*.csv")):

    relative_path = file_path.relative_to("data")

    transactions = load_daily_transactions(
        relative_path.as_posix()
    )

    result = process_transactions(
        transactions,
        account_ids
    )

    all_transactions.extend(result["valid_transactions"])


# Run the first four rules
daily_ctr = detect_daily_ctr(all_transactions)

monthly_ctr = detect_monthly_ctr(all_transactions)

structuring = detect_structuring(
    all_transactions,
    accounts
)

velocity_sep21 = detect_velocity(
    all_transactions,
    accounts,
    customers,
    "2026-09-21"
)

velocity_oct15 = detect_velocity(
    all_transactions,
    accounts,
    customers,
    "2026-10-15"
)

velocity_oct30 = detect_velocity(
    all_transactions,
    accounts,
    customers,
    "2026-10-30"
)
rapid_movement = detect_rapid_movement(all_transactions)
dormant_oct15 = detect_dormant_reactivation(
    all_transactions,
    prior_transactions,
    accounts,
    "2026-10-15"
)

dormant_oct30 = detect_dormant_reactivation(
    all_transactions,
    prior_transactions,
    accounts,
    "2026-10-30"
)
pep_findings = detect_pep_alerts(
    all_transactions,
    customers,
    accounts
)
kyc_findings = detect_kyc_alerts(
    all_transactions,
    customers,
    accounts
)
# Display results
print("AML RULES ENGINE TEST")
print("---------------------")

print("Valid transactions:", len(all_transactions))
print("Daily CTR findings:", len(daily_ctr))
print("Monthly CTR findings:", len(monthly_ctr))
print("Structuring findings:", len(structuring))
print("Velocity findings on Sep 21:", len(velocity_sep21))
print("Velocity findings on Oct 15:", len(velocity_oct15))
print("Velocity findings on Oct 30:", len(velocity_oct30))


print("\nVELOCITY FINDINGS - SEP 21, 2026")
print("--------------------------------")

for finding in velocity_sep21:
    print(
        finding["customer_id"],
        finding["account_id"],
        "Score:", finding["raw_score"],
        "Credits:", finding["total_credits"],
        "Expected:", finding["expected_turnover"],
        "Multiple:", finding["turnover_multiple"]
    )


print("\nVELOCITY FINDINGS - OCT 15, 2026")
print("--------------------------------")

for finding in velocity_oct15:
    print(
        finding["customer_id"],
        finding["account_id"],
        "Score:", finding["raw_score"],
        "Credits:", finding["total_credits"],
        "Expected:", finding["expected_turnover"],
        "Multiple:", finding["turnover_multiple"]
    )


print("\nVELOCITY FINDINGS - OCT 30, 2026")
print("--------------------------------")

for finding in velocity_oct30:
    print(
        finding["customer_id"],
        finding["account_id"],
        "Score:", finding["raw_score"],
        "Credits:", finding["total_credits"],
        "Expected:", finding["expected_turnover"],
        "Multiple:", finding["turnover_multiple"]
    )


print("\nVelocity detection test completed!")
print("\nRAPID MOVEMENT FINDINGS")
print("-----------------------")

print("Total findings:", len(rapid_movement))

for finding in rapid_movement:
    print(
        finding["account_id"],
        "Score:", finding["raw_score"],
        "Outgoing:", finding["total_outgoing"],
        "Percentage:", finding["outgoing_percentage"],
        "Round trip:", finding["round_trip_detected"]
    )
print("\nDORMANT ACCOUNT FINDINGS - OCT 15")
print("---------------------------------")

for finding in dormant_oct15:
    print(
        finding["customer_id"],
        finding["account_id"],
        "Amount:", finding["total_amount"],
        "Score:", finding["score"]
    )

print("\nDORMANT ACCOUNT FINDINGS - OCT 30")
print("---------------------------------")

for finding in dormant_oct30:
    print(
        finding["customer_id"],
        finding["account_id"],
        "Amount:", finding["total_amount"],
        "Score:", finding["score"]
    )
print("\nPEP DETECTION FINDINGS")
print("----------------------")

print("Total findings:", len(pep_findings))

for finding in pep_findings:
    print(
        finding["customer_id"],
        finding["account_id"],
        "Transaction:", finding["transaction_id"],
        "Amount:", finding["amount"],
        "Score:", finding["raw_score"]
    )
print("\nKYC DETECTION FINDINGS")
print("----------------------")

print("Total findings:", len(kyc_findings))

for finding in kyc_findings:
    print(
        finding["customer_id"],
        finding["account_id"],
        "Transaction:", finding["transaction_id"],
        "Amount:", finding["amount"],
        "Score:", finding["raw_score"]
    )   