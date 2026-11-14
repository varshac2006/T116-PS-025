import unittest
import csv
import os
from pathlib import Path
from src.command_processor import AMLCommandProcessor

class TestIntegration(unittest.TestCase):

    def test_full_pipeline_execution(self):
        processor = AMLCommandProcessor()
        processor.run()

        # Check transaction volumes
        self.assertEqual(len(processor.all_transactions), 500, '500 valid daily transactions accumulated')
        self.assertEqual(len(processor.invalid_records), 1, 'Planted 0.00 withdrawal invalid')
        self.assertEqual(len(processor.duplicate_records), 1, 'Planted duplicate TXN-000084')
        self.assertEqual(len(processor.alert_records), 22, '22 alerts raised')
        self.assertEqual(len(processor.case_manager.cases), 12, '12 cases created')
        self.assertEqual(len(processor.str_records), 2, '2 STRs filed')

        # Check generated report files exist
        reports_dir = Path('reports')
        self.assertTrue((reports_dir / 'alert_log.csv').exists())
        self.assertTrue((reports_dir / 'case_register.csv').exists())
        self.assertTrue((reports_dir / 'ctr_2026_09.csv').exists())
        self.assertTrue((reports_dir / 'str_report.csv').exists())

        # Verify alert_log.csv has space-separated evidence
        with open(reports_dir / 'alert_log.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 22)
            for r in rows:
                self.assertNotIn('|', r['evidence_txn_ids'], 'Evidence IDs must be space-separated')
                self.assertIn(r['priority'], ('true', 'false'), 'Priority must be lowercase')

        # Verify case_register.csv has space-separated alerts
        with open(reports_dir / 'case_register.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 12)
            for r in rows:
                self.assertNotIn('|', r['alert_ids'], 'Alert IDs must be space-separated')
                self.assertIn(r['priority'], ('true', 'false'), 'Priority must be lowercase')

        # Verify ctr_2026_09.csv has due_date
        with open(reports_dir / 'ctr_2026_09.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 7)
            for r in rows:
                self.assertEqual(r['due_date'], '2026-10-15')
                self.assertNotIn('|', r['txn_ids'])

        # Verify str_report.csv has 2 records
        with open(reports_dir / 'str_report.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]['customer_id'], 'CUST-023')
            self.assertEqual(rows[0]['within_sla'], 'true')
            self.assertEqual(rows[1]['customer_id'], 'CUST-010')
            self.assertEqual(rows[1]['within_sla'], 'false')

if __name__ == '__main__':
    unittest.main()
