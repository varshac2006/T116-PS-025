
from datetime import datetime, timedelta

from src.data_loader import (
    load_all_master_data,
    load_commands,
    load_daily_transactions,
)

from src.transaction_processor import process_transactions
from src.case_manager import CaseManager

from src.rules_engine import (
    detect_daily_ctr,
    detect_monthly_ctr,
    detect_structuring,
    detect_velocity,
    detect_rapid_movement,
    detect_dormant_reactivation,
    detect_pep_alerts,
    detect_kyc_alerts,
)

from src.alert_manager import (
    build_alert_record,
    get_rule_ids,
    get_evidence_transaction_ids,
)

from src.report_generator import (
    generate_ctr_report,
    generate_alert_log,
    generate_case_register,
    generate_str_report,
)


class AMLCommandProcessor:

    def __init__(self):
        self.master_data = load_all_master_data()

        self.customers = self.master_data["customers"]
        self.accounts = self.master_data["accounts"]
        self.branches = self.master_data["branches"]
        self.calendar = self.master_data["calendar"]
        self.prior_transactions = self.master_data["prior_transactions"]

        self.valid_account_ids = {
            a["account_id"] for a in self.accounts
        }
        self.valid_branch_ids = {
            b["branch_id"] for b in self.branches
        }

        self.case_manager = CaseManager(self.calendar)

        self.all_transactions = []
        self.seen_transaction_ids = set()

        self.invalid_records = []
        self.duplicate_records = []

        self.alert_records = []
        self.ctr_records = []
        self.str_records = []

        self.next_alert_number = 1
        self.processed_finding_keys = set()
        self.finding_history = {}

        self.rule_findings = {}
        self.current_date = None

    # ---------------------------------------------------------
    # MAIN COMMAND RUNNER
    # ---------------------------------------------------------

    def run(self):
        commands = load_commands()

        for item in commands:
            command = item["command"]
            arguments = item["arguments"]

            if command == "RUN_DAY":
                self.run_day(arguments)

            elif command == "CASE_ACTION":
                self.case_action(arguments)

            elif command == "GENERATE_CTR":
                self.generate_ctr(arguments)

            elif command == "PRINT_ALERT_LOG":
                self.print_alert_log(arguments)

            elif command == "PRINT_CASES":
                self.print_cases(arguments)

            elif command == "PRINT_STR_REPORT":
                self.print_str_report(arguments)

            else:
                print(f"Unknown command: {command}")

    # ---------------------------------------------------------
    # DAILY TRANSACTION PROCESSING
    # ---------------------------------------------------------

    def run_day(self, arguments):
        if len(arguments) != 2:
            print("Invalid RUN_DAY command:", arguments)
            return

        evaluation_date, file_name = arguments
        self.current_date = evaluation_date

        daily_records = load_daily_transactions(file_name)

        result = process_transactions(
            daily_records,
            valid_account_ids=self.valid_account_ids,
            valid_branch_ids=self.valid_branch_ids,
        )

        new_records = []

        for transaction in result["valid_transactions"]:
            txn_id = transaction["txn_id"]

            if txn_id in self.seen_transaction_ids:
                self.duplicate_records.append(transaction)
                continue

            self.seen_transaction_ids.add(txn_id)
            new_records.append(transaction)

        self.invalid_records.extend(result["invalid_records"])
        self.duplicate_records.extend(result["duplicate_records"])
        self.all_transactions.extend(new_records)

        print(f"\nDate: {evaluation_date}")
        print(f"File: {file_name}")
        print(f"Transactions loaded: {len(new_records)}")
        print(f"Total accumulated: {len(self.all_transactions)}")
        print(f"Invalid records: {len(self.invalid_records)}")
        print(f"Duplicate records: {len(self.duplicate_records)}")

        self.evaluate_rules()

    # ---------------------------------------------------------
    # AML RULE EVALUATION
    # ---------------------------------------------------------

    def evaluate_rules(self):
        transactions = self.all_transactions
        evaluation_date = self.current_date

        daily_ctr = detect_daily_ctr(transactions)
        monthly_ctr = detect_monthly_ctr(transactions)

        structuring = detect_structuring(
            transactions, self.accounts
        )

        velocity = detect_velocity(
            transactions,
            self.accounts,
            self.customers,
            evaluation_date,
        )

        rapid_movement = detect_rapid_movement(transactions)

        dormant = detect_dormant_reactivation(
            transactions,
            self.prior_transactions,
            self.accounts,
            evaluation_date,
        )

        pep = detect_pep_alerts(
            transactions, self.customers, self.accounts
        )

        kyc = detect_kyc_alerts(
            transactions, self.customers, self.accounts
        )

        self.rule_findings = {
            "daily_ctr": daily_ctr,
            "monthly_ctr": monthly_ctr,
            "structuring": structuring,
            "velocity": velocity,
            "rapid_movement": rapid_movement,
            "dormant": dormant,
            "pep": pep,
            "kyc": kyc,
        }

        print("\n--- AML RULE DETECTION SUMMARY ---")

        for name, findings in self.rule_findings.items():
            print(f"{name}: {len(findings)}")

        self.process_alert_findings()

    # ---------------------------------------------------------
    # HELPER METHODS
    # ---------------------------------------------------------

    def _get_customer(self, customer_id):
        for customer in self.customers:
            if customer["customer_id"] == customer_id:
                return customer

        raise ValueError(f"Customer not found: {customer_id}")

    def _get_finding_key(self, finding):
        rule_ids = get_rule_ids(finding)
        evidence_ids = get_evidence_transaction_ids(finding)

        customer_id = finding.get("customer_id", "")

        if not customer_id:
            account_id = finding.get("account_id")

            for account in self.accounts:
                if account["account_id"] == account_id:
                    customer_id = account["customer_id"]
                    break

        return (
            customer_id,
            tuple(rule_ids),
            tuple(sorted(evidence_ids)),
        )

    def _get_existing_case(self, customer_id):
        return self.case_manager.find_open_case(customer_id)

    def _is_str_filed_customer(self, customer_id):
        current_date = datetime.strptime(
            self.current_date, "%Y-%m-%d"
        ).date()

        for case in self.case_manager.cases:
            if (
                case.get("customer_id") == customer_id
                and case.get("state") == "STR_FILED"
                and case.get("str_filed_on")
            ):
                filed_date = datetime.strptime(
                    case["str_filed_on"][:10], "%Y-%m-%d"
                ).date()

                if filed_date <= current_date <= filed_date + timedelta(days=183):
                    return True

        return False

    def _get_customer_pep_kyc_adders(self, customer, rule_name):
        pep_ids = {
            c["customer_id"]
            for c in self.customers
            if str(c.get("pep", "")).strip().lower()
            in ("true", "1", "yes")
        }

        customer_id = customer["customer_id"]

        is_pep = customer_id in pep_ids

        is_pep_linked = any(
            c.get("pep_linked_customer") == customer_id
            for c in self.customers
        )

        is_pep_linked = is_pep_linked or (
            customer.get("pep_linked_customer") in pep_ids
        )

        pep_adder = 20 if (is_pep or is_pep_linked) else 0

        expiry = customer.get("kyc_expiry_date", "")
        is_kyc_expired = bool(expiry) and (
            self.current_date > expiry
        )

        kyc_adder = 10 if is_kyc_expired else 0

        if rule_name == "pep":
            return pep_adder

        if rule_name == "kyc":
            return 0

        return pep_adder + kyc_adder

    def _collapse_structuring_findings(self, findings):
        selected = {}

        for finding in findings:
            key = (
                finding.get("customer_id"),
                finding.get("account_id"),
            )

            current = selected.get(key)

            if (
                current is None
                or finding.get("window_end", "")
                > current.get("window_end", "")
            ):
                selected[key] = finding

        return list(selected.values())

    # ---------------------------------------------------------
    # ALERT PROCESSING AND CASE CREATION
    # ---------------------------------------------------------

    def process_alert_findings(self):
        alert_rule_names = [
            "structuring",
            "velocity",
            "rapid_movement",
            "dormant",
            "pep",
            "kyc",
        ]

        new_alerts = 0
        merged_alerts = 0

        current_date = datetime.strptime(
            self.current_date, "%Y-%m-%d"
        ).date()

        for rule_name in alert_rule_names:
            findings = self.rule_findings.get(rule_name, [])

            if rule_name == "structuring":
                findings = self._collapse_structuring_findings(findings)

            for finding in findings:
                finding_key = self._get_finding_key(finding)

                if finding_key in self.processed_finding_keys:
                    continue

                customer_id = finding.get("customer_id")

                if not customer_id:
                    account_id = finding.get("account_id")

                    for account in self.accounts:
                        if account["account_id"] == account_id:
                            customer_id = account["customer_id"]
                            break

                if not customer_id:
                    continue

                customer = self._get_customer(customer_id)
                rule_ids = get_rule_ids(finding)

                existing_case = self._get_existing_case(customer_id)

                matching_previous_alert = None

                if existing_case:
                    for previous in reversed(self.alert_records):
                        if previous["customer_id"] != customer_id:
                            continue

                        if previous["case_id"] != existing_case["case_id"]:
                            continue

                        previous_rules = previous["rule_ids"].split("|")

                        if not any(r in previous_rules for r in rule_ids):
                            continue

                        previous_date = datetime.strptime(
                            previous["eval_date"], "%Y-%m-%d"
                        ).date()

                        difference = (current_date - previous_date).days

                        if 0 <= difference <= 7:
                            matching_previous_alert = previous
                            break

                is_merge = matching_previous_alert is not None

                evidence = tuple(sorted(
                    get_evidence_transaction_ids(finding)
                ))

                merge_count = 1 if is_merge else 0

                for rule_id in rule_ids:
                    history_key = (customer_id, rule_id)
                    previous = self.finding_history.get(history_key)

                    if previous:
                        previous_date = datetime.strptime(
                            previous["date"], "%Y-%m-%d"
                        ).date()

                        days_between = (current_date - previous_date).days

                        if (
                            previous["evidence"] != evidence
                            and 0 <= days_between <= 7
                        ):
                            merge_count = max(
                                merge_count,
                                previous["merge_count"] + 1,
                            )

                for rule_id in rule_ids:
                    self.finding_history[(customer_id, rule_id)] = {
                        "date": self.current_date,
                        "evidence": evidence,
                        "merge_count": merge_count,
                    }

                action = "MERGED" if is_merge else "NEW"

                case_id = (
                    existing_case["case_id"]
                    if existing_case
                    else ""
                )

                str_filed = self._is_str_filed_customer(customer_id)

                adders = self._get_customer_pep_kyc_adders(
                    customer, rule_name
                )

                alert_id = f"ALT-{self.next_alert_number:05d}"

                alert = build_alert_record(
                    finding=finding,
                    customer=customer,
                    accounts=self.accounts,
                    evaluation_date=self.current_date,
                    alert_id=alert_id,
                    case_id=case_id,
                    pep_kyc_adders=adders,
                    merge_count=merge_count,
                    str_filed=str_filed,
                    action=action,
                )

                self.processed_finding_keys.add(finding_key)

                if alert is None:
                    continue

                is_priority = (
                    alert.get("priority") is True
                    or str(alert.get("priority", "")).strip().lower()
                    in ("true", "1", "yes")
                )

                if existing_case:
                    self.case_manager.add_alert_to_case(
                        existing_case["case_id"], alert_id
                    )

                    if is_priority:
                        existing_case["priority"] = True

                    alert["case_id"] = existing_case["case_id"]

                else:
                    new_case = self.case_manager.create_case(
                        customer_id=customer_id,
                        opened_on=self.current_date + " 23:00:00",
                        priority=is_priority,
                        alert_id=alert_id,
                    )

                    alert["case_id"] = new_case["case_id"]

                self.alert_records.append(alert)
                self.next_alert_number += 1

                if is_merge:
                    merged_alerts += 1
                else:
                    new_alerts += 1

        print("\n--- ALERT PROCESSING SUMMARY ---")
        print(f"New alerts: {new_alerts}")
        print(f"Merged alerts: {merged_alerts}")
        print(f"Total alert records: {len(self.alert_records)}")

    # ---------------------------------------------------------
    # CASE ACTION HANDLER
    # ---------------------------------------------------------

    def case_action(self, arguments):
        if len(arguments) != 4:
            print("Invalid CASE_ACTION command:", arguments)
            return

        customer_id, action, action_ts, note = arguments

        case = self.case_manager.find_open_case(customer_id)

        result = self.case_manager.apply_case_action(
            customer_id=customer_id,
            action=action,
            action_ts=action_ts,
            note=note,
        )

        if not result.get("success"):
            print(
                f"\nCASE ACTION FAILED: {customer_id} | "
                f"{action} | {result.get('note', '')}"
            )
            return

        print(
            f"\nCASE ACTION SUCCESS: {customer_id} | "
            f"{action} | {result.get('case_id', '')} | "
            f"{result.get('state', '')}"
        )

        if action == "FILE_STR" and case is not None:

            evidence_ids = set()

            for alert in self.alert_records:
                if alert.get("case_id") != case["case_id"]:
                    continue

                # Read evidence IDs directly from the alert record.
                alert_evidence = alert.get("evidence_txn_ids", [])

                # Alert evidence is normally stored as a pipe-separated string.
                if isinstance(alert_evidence, str):
                    alert_evidence = [
                        txn_id.strip()
                        for txn_id in alert_evidence.split("|")
                        if txn_id.strip()
                    ]

                # Also support list-based evidence.
                elif isinstance(alert_evidence, (list, tuple, set)):
                    alert_evidence = list(alert_evidence)

                else:
                    alert_evidence = []

                # Add only complete transaction IDs.
                evidence_ids.update(alert_evidence)

            evidence_ids = sorted(evidence_ids)

            transaction_lookup = {
                transaction["txn_id"]: transaction
                for transaction in self.all_transactions
            }

            total_amount = 0.0

            for txn_id in evidence_ids:
                transaction = transaction_lookup.get(txn_id)

                if transaction is not None:
                    total_amount += float(
                        transaction.get("amount", 0)
                    )

            escalated_on = case.get("escalated_on", "")

            if escalated_on:
                working_days = self.case_manager.working_days_between(
                    escalated_on,
                    action_ts,
                )
                within_sla = working_days <= 7
            else:
                within_sla = False

            str_record = {
                "str_id": f"STR-{len(self.str_records) + 1:04d}",
                "case_id": case["case_id"],
                "customer_id": customer_id,
                "escalated_on": escalated_on,
                "filed_on": action_ts,
                "within_sla": str(within_sla).lower(),
                "total_amount": round(total_amount, 2),
                "evidence_txn_ids": "|".join(evidence_ids),
            }

            self.str_records.append(str_record)

            print(
                f"STR record created: {str_record['str_id']}"
            )

    # ---------------------------------------------------------
    # CTR REPORT GENERATION
    # ---------------------------------------------------------

    def generate_ctr(self, arguments):
        if len(arguments) != 1:
            print("Invalid GENERATE_CTR command:", arguments)
            return

        month = arguments[0]

        try:
            output_path = generate_ctr_report(
                daily_findings=self.rule_findings.get("daily_ctr", []),
                monthly_findings=self.rule_findings.get("monthly_ctr", []),
                accounts=self.accounts,
                month=month,
            )

            print(f"\nCTR report generated successfully: {output_path}")

        except (ValueError, KeyError) as error:
            print(f"\nCTR report generation failed: {error}")

    # ---------------------------------------------------------
    # ALERT LOG REPORT
    # ---------------------------------------------------------

    def print_alert_log(self, arguments):
        if len(arguments) != 2:
            print("Invalid PRINT_ALERT_LOG command:", arguments)
            return

        from_date, to_date = arguments

        try:
            output_path = generate_alert_log(
                alert_records=self.alert_records,
                from_date=from_date,
                to_date=to_date,
            )

            print(f"\nAlert log generated successfully: {output_path}")

        except (ValueError, KeyError) as error:
            print(f"\nAlert log generation failed: {error}")

    # ---------------------------------------------------------
    # CASE REGISTER REPORT
    # ---------------------------------------------------------

    def print_cases(self, arguments):
        if len(arguments) != 1:
            print("Invalid PRINT_CASES command:", arguments)
            return

        as_of_date = arguments[0]

        try:
            case_records = self.case_manager.get_case_register()

            output_path = generate_case_register(
                case_records=case_records,
                as_of_date=as_of_date,
            )

            print(f"\nCase register generated successfully: {output_path}")

        except (ValueError, KeyError) as error:
            print(f"\nCase register generation failed: {error}")

    # ---------------------------------------------------------
    # STR REPORT
    # ---------------------------------------------------------

    def print_str_report(self, arguments):
        if len(arguments) != 2:
            print("Invalid PRINT_STR_REPORT command:", arguments)
            return

        from_date, to_date = arguments

        try:
            output_path = generate_str_report(
                str_records=self.str_records,
                from_date=from_date,
                to_date=to_date,
            )

            print(f"\nSTR report generated successfully: {output_path}")

        except (ValueError, KeyError) as error:
            print(f"\nSTR report generation failed: {error}")
