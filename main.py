
from src.command_processor import AMLCommandProcessor


def main():
    print("=" * 60)
    print("AML TRANSACTION MONITORING SYSTEM")
    print("Problem Statement: PS-025")
    print("=" * 60)

    processor = AMLCommandProcessor()

    print("\nStarting command execution from commands.txt...\n")

    processor.run()

    print("\n" + "=" * 60)
    print("AML MONITORING EXECUTION COMPLETED")
    print("=" * 60)

    print("\nFINAL SUMMARY")
    print("-" * 40)
    print(f"Transactions processed: {len(processor.all_transactions)}")
    print(f"Invalid records: {len(processor.invalid_records)}")
    print(f"Duplicate records: {len(processor.duplicate_records)}")
    print(f"Alerts generated: {len(processor.alert_records)}")
    print(f"Cases created: {len(processor.case_manager.cases)}")
    print(f"STR records generated: {len(processor.str_records)}")

    print("\nGenerated reports:")
    print("1. reports/alert_log.csv")
    print("2. reports/case_register.csv")
    print("3. reports/str_report.csv")
    print("4. reports/ctr_2026_09.csv")


if __name__ == "__main__":
    main()
