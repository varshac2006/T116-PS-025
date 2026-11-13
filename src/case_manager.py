
from datetime import datetime, timedelta


CASE_COLUMNS = [
    "case_id",
    "customer_id",
    "opened_on",
    "priority",
    "state",
    "under_review_on",
    "escalated_on",
    "closed_on",
    "str_filed_on",
    "sla_breaches",
    "alert_ids"
]

VALID_ACTIONS = {
    "START_REVIEW",
    "ESCALATE",
    "CLOSE_NO_ACTION",
    "FILE_STR"
}

ACTIVE_STATES = {
    "OPEN",
    "UNDER_REVIEW",
    "ESCALATED"
}


class CaseManager:
    """Manage AML cases, case actions and SLA calculations."""

    def __init__(self, calendar):
        self.calendar = calendar
        self.cases = []
        self.next_case_number = 1
        self.action_errors = []

    def generate_case_id(self):
        """Generate sequential CASE identifiers."""

        case_id = f"CASE-{self.next_case_number:04d}"
        self.next_case_number += 1

        return case_id

    def working_days_between(self, start_date, end_date):
        """
        Count working days after start_date through end_date.

        The starting date is excluded.
        The ending date is included.
        """

        if isinstance(start_date, datetime):
            start_date = start_date.date()
        elif isinstance(start_date, str):
            start_date = datetime.strptime(
                start_date[:10], "%Y-%m-%d"
            ).date()

        if isinstance(end_date, datetime):
            end_date = end_date.date()
        elif isinstance(end_date, str):
            end_date = datetime.strptime(
                end_date[:10], "%Y-%m-%d"
            ).date()

        if end_date < start_date:
            raise ValueError("End date cannot precede start date")

        working_days = 0
        current_date = start_date + timedelta(days=1)

        while current_date <= end_date:
            calendar_entry = self.calendar.get(
                current_date.isoformat()
            )

            if calendar_entry is None:
                raise ValueError(
                    f"Calendar entry missing for {current_date}"
                )

            if calendar_entry["is_working_day"]:
                working_days += 1

            current_date += timedelta(days=1)

        return working_days

    def find_open_case(self, customer_id):
        """Find the customer's latest active case."""

        matching_cases = [
            case for case in self.cases
            if case["customer_id"] == customer_id
            and case["state"] in ACTIVE_STATES
        ]

        if not matching_cases:
            return None

        return matching_cases[-1]

    def create_case(
        self,
        customer_id,
        opened_on,
        priority,
        alert_id
    ):
        """Create a new AML case."""

        existing_case = self.find_open_case(customer_id)

        if existing_case:
            raise ValueError(
                f"Customer {customer_id} already has an active case"
            )

        case = {
            "case_id": self.generate_case_id(),
            "customer_id": customer_id,
            "opened_on": opened_on,
            "priority": bool(priority),
            "state": "OPEN",
            "under_review_on": "",
            "escalated_on": "",
            "closed_on": "",
            "str_filed_on": "",
            "sla_breaches": [],
            "alert_ids": [alert_id]
        }

        self.cases.append(case)

        return case

    def add_alert_to_case(self, case_id, alert_id):
        """Attach a new alert to an existing case."""

        case = self.get_case_by_id(case_id)

        if case["state"] not in ACTIVE_STATES:
            raise ValueError("Cannot add an alert to an inactive case")

        if alert_id not in case["alert_ids"]:
            case["alert_ids"].append(alert_id)

    def get_case_by_id(self, case_id):
        """Find a case using its ID."""

        for case in self.cases:
            if case["case_id"] == case_id:
                return case

        raise ValueError(f"Case not found: {case_id}")

    def record_sla_breach(self, case, breach_type):
        """Record an SLA breach only once."""

        if breach_type not in case["sla_breaches"]:
            case["sla_breaches"].append(breach_type)

    def apply_case_action(
        self,
        customer_id,
        action,
        action_ts,
        note=""
    ):
        """
        Apply a command action to the customer's active case.

        Invalid actions are rejected and recorded.
        """

        action = action.strip().upper()

        if action not in VALID_ACTIONS:
            return self.reject_action(
                customer_id,
                action,
                "Unknown action"
            )

        try:
            action_datetime = datetime.strptime(
                action_ts,
                "%Y-%m-%d %H:%M:%S"
            )
        except ValueError:
            return self.reject_action(
                customer_id,
                action,
                "Invalid action timestamp"
            )

        case = self.find_open_case(customer_id)

        if case is None:
            return self.reject_action(
                customer_id,
                action,
                "No active case exists"
            )

        action_date = action_datetime.date()
        opened_date = datetime.strptime(
            case["opened_on"][:10],
            "%Y-%m-%d"
        ).date()

        if action_datetime < datetime.strptime(
            case["opened_on"],
            "%Y-%m-%d %H:%M:%S"
        ):
            return self.reject_action(
                customer_id,
                action,
                "Action timestamp precedes case opening"
            )

        if action == "START_REVIEW":

            if case["state"] != "OPEN":
                return self.reject_action(
                    customer_id,
                    action,
                    "Case is not in OPEN state"
                )

            allowed_days = 1 if case["priority"] else 2

            elapsed_days = self.working_days_between(
                opened_date,
                action_date
            )

            if elapsed_days > allowed_days:
                self.record_sla_breach(case, "REVIEW")

            case["state"] = "UNDER_REVIEW"
            case["under_review_on"] = action_ts

        elif action == "ESCALATE":

            if case["state"] != "UNDER_REVIEW":
                return self.reject_action(
                    customer_id,
                    action,
                    "Case must be UNDER_REVIEW before escalation"
                )

            case["state"] = "ESCALATED"
            case["escalated_on"] = action_ts

        elif action == "CLOSE_NO_ACTION":

            if case["state"] not in ACTIVE_STATES:
                return self.reject_action(
                    customer_id,
                    action,
                    "Case cannot be closed from its current state"
                )

            case["state"] = "CLOSED_NO_ACTION"
            case["closed_on"] = action_ts

        elif action == "FILE_STR":

            if case["state"] != "ESCALATED":
                return self.reject_action(
                    customer_id,
                    action,
                    "Case must be ESCALATED before STR filing"
                )

            escalation_datetime = datetime.strptime(
                case["escalated_on"],
                "%Y-%m-%d %H:%M:%S"
            )

            elapsed_days = self.working_days_between(
                escalation_datetime,
                action_datetime
            )

            if elapsed_days > 7:
                self.record_sla_breach(case, "STR")

            case["state"] = "STR_FILED"
            case["str_filed_on"] = action_ts

        return {
            "success": True,
            "case_id": case["case_id"],
            "state": case["state"],
            "note": note
        }

    def reject_action(self, customer_id, action, reason):
        """Record an invalid case action."""

        error = {
            "customer_id": customer_id,
            "action": action,
            "reason": reason
        }

        self.action_errors.append(error)

        return {
            "success": False,
            "error": reason
        }

    def get_case_register(self):
        """Return case records in the required output format."""

        records = []

        for case in self.cases:
            records.append({
                "case_id": case["case_id"],
                "customer_id": case["customer_id"],
                "opened_on": case["opened_on"],
                "priority": str(case["priority"]).lower(),
                "state": case["state"],
                "under_review_on": case["under_review_on"],
                "escalated_on": case["escalated_on"],
                "closed_on": case["closed_on"],
                "str_filed_on": case["str_filed_on"],
                "sla_breaches": " ".join(
                    case["sla_breaches"]
                ),
                "alert_ids": "|".join(case["alert_ids"])
            })

        return records
