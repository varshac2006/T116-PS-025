import unittest
import csv
import os
import tempfile
from pathlib import Path
from src.report_generator import (
    generate_alert_log,
    generate_case_register,
    generate_ctr_report,
    generate_str_report,
    ALERT_LOG_COLUMNS,
    CASE_COLUMNS,
    CTR_COLUMNS,
    STR_COLUMNS
)

class TestReports(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.out_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_alert_log_schema_and_delimiters(self):
        alerts = [{
            'alert_id': 'ALT-00001',
            'eval_date': '2026-09-04',
            'customer_id': 'CUST-023',
            'rule_ids': 'BR-03',
            'raw_score': 40.0,
            'pep_kyc_adders': 0,
            'risk_multiplier': 1.5,
            'merge_bonus': 0,
            'weighted_score': 60.0,
            'priority': 'false',
            'case_id': 'CASE-0001',
            'action': 'NEW',
            'evidence_txn_ids': 'TXN-000010 TXN-000019 TXN-000029'
        }]
        path = generate_alert_log(alerts, '2026-09-01', '2026-09-30', output_dir=self.out_dir)
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            self.assertEqual(header, ALERT_LOG_COLUMNS)
            row = next(reader)
            self.assertEqual(row[0], 'ALT-00001')
            self.assertEqual(row[9], 'false')
            self.assertEqual(row[12], 'TXN-000010 TXN-000019 TXN-000029')

    def test_case_register_schema(self):
        cases = [{
            'case_id': 'CASE-0001',
            'customer_id': 'CUST-023',
            'opened_on': '2026-09-04 23:00:00',
            'priority': 'true',
            'state': 'STR_FILED',
            'under_review_on': '2026-09-07 09:40:00',
            'escalated_on': '2026-09-08 15:00:00',
            'closed_on': '',
            'str_filed_on': '2026-09-16 17:30:00',
            'sla_breaches': 'UNDER_REVIEW',
            'alert_ids': 'ALT-00001 ALT-00003'
        }]
        path = generate_case_register(cases, '2026-10-30', output_dir=self.out_dir)
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            self.assertEqual(header, CASE_COLUMNS)
            row = next(reader)
            self.assertEqual(row[9], 'UNDER_REVIEW')
            self.assertEqual(row[10], 'ALT-00001 ALT-00003')

    def test_ctr_report_schema_and_due_date(self):
        daily = [{
            'account_id': 'ACC-1',
            'txn_date': '2026-09-17',
            'total_cash': 1050000.0,
            'txn_ids': ['TXN-1', 'TXN-2'],
            'due_date': '2026-10-15'
        }]
        accounts = [{'account_id': 'ACC-1', 'customer_id': 'CUST-1'}]
        path = generate_ctr_report(daily, [], accounts, '2026-09', output_dir=self.out_dir)
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            self.assertEqual(header, CTR_COLUMNS)
            row = next(reader)
            self.assertEqual(row[4], '1050000.00', 'Amount must be formatted to 2 decimals')
            self.assertEqual(row[5], 'TXN-1 TXN-2', 'IDs must be space-separated')
            self.assertEqual(row[6], '2026-10-15', 'Due date must be 15th of next month')

    def test_str_report_schema_and_amount(self):
        strs = [{
            'str_id': 'STR-0001',
            'case_id': 'CASE-0001',
            'customer_id': 'CUST-023',
            'escalated_on': '2026-09-08 15:00:00',
            'filed_on': '2026-09-16 17:30:00',
            'within_sla': 'true',
            'total_amount': 5725000.0,
            'evidence_txn_ids': ['TXN-1', 'TXN-2']
        }]
        path = generate_str_report(strs, '2026-09-01', '2026-10-30', output_dir=self.out_dir)
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            self.assertEqual(header, STR_COLUMNS)
            row = next(reader)
            self.assertEqual(row[5], 'true')
            self.assertEqual(row[6], '5725000.00', 'Amount must be formatted to 2 decimals')
            self.assertEqual(row[7], 'TXN-1 TXN-2', 'IDs must be space-separated')

if __name__ == '__main__':
    unittest.main()
