import unittest
from src.case_manager import CaseManager

class TestCaseManagement(unittest.TestCase):

    def setUp(self):
        # Setup a simple working calendar
        self.calendar = {}
        # 2026-09-01 (Tue) through 2026-09-30 (Wed)
        for day in range(1, 31):
            date_str = f'2026-09-{day:02d}'
            # Sundays: 6, 13, 20, 27
            # 2nd Sat: 12, 4th Sat: 26
            is_off = day in (6, 12, 13, 20, 26, 27)
            self.calendar[date_str] = {
                'day_name': 'Day',
                'is_working_day': not is_off,
                'reason': 'Weekend' if is_off else ''
            }
        self.cm = CaseManager(self.calendar)

    def test_valid_case_lifecycle(self):
        case = self.cm.create_case('CUST-1', '2026-09-01 23:00:00', priority=False, alert_id='ALT-1')
        self.assertEqual(case['state'], 'OPEN')

        # START_REVIEW
        res1 = self.cm.apply_case_action('CUST-1', 'START_REVIEW', '2026-09-02 10:00:00')
        self.assertTrue(res1['success'])
        self.assertEqual(case['state'], 'UNDER_REVIEW')

        # ESCALATE
        res2 = self.cm.apply_case_action('CUST-1', 'ESCALATE', '2026-09-03 14:00:00')
        self.assertTrue(res2['success'])
        self.assertEqual(case['state'], 'ESCALATED')

        # FILE_STR
        res3 = self.cm.apply_case_action('CUST-1', 'FILE_STR', '2026-09-08 11:00:00')
        self.assertTrue(res3['success'])
        self.assertEqual(case['state'], 'STR_FILED')

    def test_irreversible_str_filing(self):
        case = self.cm.create_case('CUST-2', '2026-09-01 23:00:00', priority=False, alert_id='ALT-2')
        self.cm.apply_case_action('CUST-2', 'START_REVIEW', '2026-09-02 10:00:00')
        self.cm.apply_case_action('CUST-2', 'ESCALATE', '2026-09-03 14:00:00')
        self.cm.apply_case_action('CUST-2', 'FILE_STR', '2026-09-08 11:00:00')

        # Attempt to act on already STR_FILED case
        res_fail = self.cm.apply_case_action('CUST-2', 'CLOSE_NO_ACTION', '2026-09-09 10:00:00')
        self.assertFalse(res_fail['success'])
        self.assertEqual(case['state'], 'STR_FILED')

    def test_invalid_state_transitions(self):
        # 1. Cannot ESCALATE directly from OPEN
        case = self.cm.create_case('CUST-3', '2026-09-01 23:00:00', priority=False, alert_id='ALT-3')
        res1 = self.cm.apply_case_action('CUST-3', 'ESCALATE', '2026-09-02 10:00:00')
        self.assertFalse(res1['success'])
        self.assertEqual(case['state'], 'OPEN')

        # 2. Cannot FILE_STR directly from OPEN
        res2 = self.cm.apply_case_action('CUST-3', 'FILE_STR', '2026-09-02 10:00:00')
        self.assertFalse(res2['success'])
        self.assertEqual(case['state'], 'OPEN')

        # 3. Action on non-existent case
        res3 = self.cm.apply_case_action('CUST-UNKNOWN', 'START_REVIEW', '2026-09-02 10:00:00')
        self.assertFalse(res3['success'])

    def test_sla_breach_detection(self):
        # Normal case (priority=False): review within 2 working days.
        # Opened 2026-09-01 (Tue).
        # Wed 02 = 1 wd, Thu 03 = 2 wd.
        # Review on Fri 04 (3 working days) -> BREACH!
        case_normal = self.cm.create_case('CUST-4', '2026-09-01 23:00:00', priority=False, alert_id='ALT-4')
        self.cm.apply_case_action('CUST-4', 'START_REVIEW', '2026-09-04 10:00:00')
        self.assertIn('UNDER_REVIEW', case_normal['sla_breaches'])

        # Priority case (priority=True): review within 1 working day.
        # Opened 2026-09-01 (Tue). Review Thu 03 (2 working days) -> BREACH!
        case_prio = self.cm.create_case('CUST-5', '2026-09-01 23:00:00', priority=True, alert_id='ALT-5')
        self.cm.apply_case_action('CUST-5', 'START_REVIEW', '2026-09-03 10:00:00')
        self.assertIn('UNDER_REVIEW', case_prio['sla_breaches'])

if __name__ == '__main__':
    unittest.main()
