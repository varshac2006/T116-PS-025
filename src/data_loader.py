
import csv
from pathlib import Path


# Find the main project folder
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def read_csv_file(file_path):
    """Read a CSV file and return its rows as dictionaries."""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with path.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        return list(reader)


def load_customers():
    """Load customer information."""
    return read_csv_file(DATA_DIR / "customers.csv")


def load_accounts():
    """Load account information."""
    return read_csv_file(DATA_DIR / "accounts.csv")


def load_branches():
    """Load branch information."""
    return read_csv_file(DATA_DIR / "branches.csv")


def load_calendar():
    """Load working-day calendar."""
    rows = read_csv_file(DATA_DIR / "calendar.csv")

    calendar = {}

    for row in rows:
        calendar[row["date"]] = {
            "day_name": row["day_name"],
            "is_working_day": row["is_working_day"].strip().lower() == "true",
            "reason": row["reason"]
        }

    return calendar


def load_prior_transactions():
    """Load historical transactions."""
    return read_csv_file(DATA_DIR / "prior_transactions.csv")


def load_daily_transactions(file_name):
    """Load transactions from a daily transaction file."""
    file_path = DATA_DIR / file_name
    return read_csv_file(file_path)


def load_commands():
    """Read commands in their original order."""

    command_file = DATA_DIR / "commands.txt"
    commands = []

    if not command_file.exists():
        raise FileNotFoundError("commands.txt was not found.")

    with command_file.open("r", encoding="utf-8-sig") as file:
        for line_number, line in enumerate(file, start=1):

            line = line.strip()

            if not line or line.startswith("#"):
                continue

            parts = [part.strip() for part in line.split("|")]

            commands.append({
                "line_number": line_number,
                "command": parts[0],
                "arguments": parts[1:]
            })

    return commands


def load_all_master_data():
    """Load all master data required by the AML system."""

    return {
        "customers": load_customers(),
        "accounts": load_accounts(),
        "branches": load_branches(),
        "calendar": load_calendar(),
        "prior_transactions": load_prior_transactions()
    }


if __name__ == "__main__":
    print("AML DATA LOADER TEST")
    print("--------------------")

    data = load_all_master_data()
    commands = load_commands()

    print("Customers loaded:", len(data["customers"]))
    print("Accounts loaded:", len(data["accounts"]))
    print("Branches loaded:", len(data["branches"]))
    print("Calendar entries:", len(data["calendar"]))
    print("Prior transactions:", len(data["prior_transactions"]))
    print("Commands loaded:", len(commands))
    first_run = next(
        command for command in commands
        if command["command"] == "RUN_DAY"
    )

    first_file = first_run["arguments"][1]
    daily_transactions = load_daily_transactions(first_file)

    print("First daily file:", first_file)
    print("Transactions in first daily file:", len(daily_transactions))    

    print("\nData loader completed successfully!")
