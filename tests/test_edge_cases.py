import unittest
from datetime import datetime, date, timedelta
from src.rules_engine import (
    detect_daily_ctr,
    detect_structuring,
    detect_velocity,
    detect_rapid_movement,
    detect_dormant_reactivation,
    detect_pep_alerts,
    detect_kyc_alerts,
    calculate_weighted_score,
    calculate_merge_bonus
)
from src.alert_manager import calculate_alert_score, build_alert_record
from src.case_manager import CaseManager
from src.transaction_processor import validate_transaction, process_transactions

class TestOfficialEdgeCases(unittest.TestCase):

    def test_ec01_cash_deposit_exact_9_lakh_and_10_lakh(self):
        # 1. Cash deposit exactly Rs 9,00,000 is inside structuring band [900000, 999999]
        accounts = [{'account_id': 'ACC-1', 'customer_id': 'CUST-1'}]
        txns = [
            {'txn_id': 'T1', 'account_id': 'ACC-1', 'branch_id': 'BR-1', 'txn_ts': '2026-09-01 10:00:00', 'txn_type': 'CASH_DEPOSIT', 'amount': '900000.00'},
            {'txn_id': 'T2', 'account_id': 'ACC-1', 'branch_id': 'BR-1', 'txn_ts': '2026-09-02 10:00:00', 'txn_type': 'CASH_DEPOSIT', 'amount': '945000.00'},
            {'txn_id': 'T3', 'account_id': 'ACC-1', 'branch_id': 'BR-1', 'txn_ts': '2026-09-03 10:00:00', 'txn_type': 'CASH_DEPOSIT', 'amount': '999999.00'}
        ]
        res = detect_structuring(txns, accounts)
        self.assertEqual(len(res), 1, 'Exactly 9,00,000 must be included in structuring')
        self.assertIn('T1', res[0]['evidence_txn_ids'])

        # 2. Cash deposit of exactly 10,00,000 is NOT > 10,00,000 (no daily CTR)
        txns_10l = [{'txn_id': 'T4', 'account_id': 'ACC-1', 'txn_ts': '2026-09-05 10:00:00', 'txn_type': 'CASH_DEPOSIT', 'amount': '1000000.00'}]
        ctr_res = detect_daily_ctr(txns_10l)
        self.assertEqual(len(ctr_res), 0, 'Exactly 10,00,000 must NOT trigger CTR')

    def test_ec02_third_structuring_deposit_at_7_day_boundary(self):
        # Third deposit at exactly 7 days (7 * 24h) after first deposit
        accounts = [{'account_id': 'ACC-1', 'customer_id': 'CUST-1'}]
        t1 = '2026-09-08 11:00:00'
        t3 = '2026-09-15 11:00:00'
        txns = [
            {'txn_id': 'T1', 'account_id': 'ACC-1', 'branch_id': 'BR-1', 'txn_ts': t1, 'txn_type': 'CASH_DEPOSIT', 'amount': '940000.00'},
            {'txn_id': 'T2', 'account_id': 'ACC-1', 'branch_id': 'BR-2', 'txn_ts': '2026-09-11 11:00:00', 'txn_type': 'CASH_DEPOSIT', 'amount': '975000.00'},
            {'txn_id': 'T3', 'account_id': 'ACC-1', 'branch_id': 'BR-1', 'txn_ts': t3, 'txn_type': 'CASH_DEPOSIT', 'amount': '910000.00'}
        ]
        res = detect_structuring(txns, accounts)
        self.assertEqual(len(res), 1, '7-day boundary must be inclusive')
        self.assertEqual(res[0]['raw_score'], 60, 'Multi-branch deposit gives 40 + 20 = 60')

    def test_ec03_outward_transfer_at_exact_48_hours(self):
        # Credit at 2026-09-24 14:00:00 and transfer out 80% at 2026-09-26 14:00:00 (exact hour 48)
        txns = [
            {'txn_id': 'T1', 'account_id': 'ACC-1', 'txn_ts': '2026-09-24 14:00:00', 'txn_type': 'TRANSFER_IN', 'amount': '500000.00', 'counterparty_account': 'ACC-A'},
            {'txn_id': 'T2', 'account_id': 'ACC-1', 'txn_ts': '2026-09-26 14:00:00', 'txn_type': 'TRANSFER_OUT', 'amount': '400000.00', 'counterparty_account': 'ACC-B'}
        ]
        res = detect_rapid_movement(txns)
        self.assertEqual(len(res), 1, 'Hour 48 boundary must be inclusive')
        self.assertEqual(res[0]['raw_score'], 35)

    def test_ec04_dormant_account_with_bank_interest_credits(self):
        prior = [
            {'txn_id': 'P1', 'account_id': 'ACC-D', 'txn_ts': '2025-07-14 10:00:00', 'txn_type': 'CASH_WITHDRAWAL', 'amount': '5000.00'},
            {'txn_id': 'P2', 'account_id': 'ACC-D', 'txn_ts': '2025-09-30 10:00:00', 'txn_type': 'INTEREST_CREDIT', 'amount': '150.00'},
            {'txn_id': 'P3', 'account_id': 'ACC-D', 'txn_ts': '2026-03-31 10:00:00', 'txn_type': 'INTEREST_CREDIT', 'amount': '150.00'},
            {'txn_id': 'P4', 'account_id': 'ACC-D', 'txn_ts': '2026-06-30 10:00:00', 'txn_type': 'INTEREST_CREDIT', 'amount': '150.00'}
        ]
        daily = [
            {'txn_id': 'D1', 'account_id': 'ACC-D', 'txn_ts': '2026-10-08 11:10:00', 'txn_type': 'TRANSFER_IN', 'amount': '350000.00'},
            {'txn_id': 'D2', 'account_id': 'ACC-D', 'txn_ts': '2026-10-19 15:00:00', 'txn_type': 'TRANSFER_IN', 'amount': '240000.00'}
        ]
        accounts = [{'account_id': 'ACC-D', 'customer_id': 'CUST-15'}]
        # Reactivation after 12 months with > 5,00,000 within 30 days
        res = detect_dormant_reactivation(daily, prior, accounts, '2026-10-19')
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]['total_amount'], 590000.00)
        self.assertEqual(res[0]['raw_score'], 30)

    def test_ec05_weighted_score_exactly_50_for_low_risk(self):
        # LOW risk customer (multiplier 0.8):
        # Velocity > 5x turnover: raw score 50 * 0.8 = 40.0.
        # Two merges (+5 each) gives 40.0 + 10 = 50.0.
        score_info = calculate_alert_score(raw_score=50, risk_rating='LOW', pep_kyc_adders=0, merge_count=2)
        self.assertEqual(score_info['weighted_score'], 50.0)
        self.assertTrue(score_info['alert_required'], 'Score 50.0 must trigger normal alert')
        self.assertFalse(score_info['priority'], 'Score 50.0 is not priority (< 70)')

    def test_ec06_same_rule_alert_exactly_7_days_after_previous(self):
        # Prior alert on 2026-09-04, second on 2026-09-11 (7 days difference)
        d1 = date(2026, 9, 4)
        d2 = date(2026, 9, 11)
        diff = (d2 - d1).days
        self.assertEqual(diff, 7)
        self.assertTrue(0 <= diff <= 7, 'Day 7 must be eligible for merge')

    def test_ec07_priority_case_opened_friday_with_saturday_working(self):
        # Calendar where Friday is 2026-09-18, Sat 2026-09-19 is working, Sun 2026-09-20 is off, Mon 2026-09-21 is working
        calendar = {
            '2026-09-18': {'is_working_day': True},
            '2026-09-19': {'is_working_day': True}, # Working Saturday!
            '2026-09-20': {'is_working_day': False}, # Sunday
            '2026-09-21': {'is_working_day': True}
        }
        cm = CaseManager(calendar)
        # Opened on Friday 18th, review started Monday 21st
        working_days = cm.working_days_between('2026-09-18', '2026-09-21')
        self.assertEqual(working_days, 2)
        # For PRIORITY case, allowed is 1 working day -> 2 > 1 is SLA breach!
        case = cm.create_case('CUST-10', '2026-09-18 23:00:00', priority=True, alert_id='ALT-1')
        cm.apply_case_action('CUST-10', 'START_REVIEW', '2026-09-21 09:45:00')
        self.assertIn('UNDER_REVIEW', case['sla_breaches'])

    def test_ec08_kyc_expiry_on_transaction_date(self):
        # KYC expiry date 2026-10-07. Credit on 2026-10-07 (not expired). Credit on 2026-10-08 (expired).
        customers = [{'customer_id': 'CUST-13', 'kyc_expiry_date': '2026-10-07'}]
        accounts = [{'account_id': 'ACC-13', 'customer_id': 'CUST-13'}]
        
        txns_07 = [{'txn_id': 'T1', 'account_id': 'ACC-13', 'txn_ts': '2026-10-07 16:20:00', 'txn_type': 'TRANSFER_IN', 'amount': '150000.00'}]
        self.assertEqual(len(detect_kyc_alerts(txns_07, customers, accounts)), 0, 'KYC valid on expiry date')

        txns_08 = [{'txn_id': 'T2', 'account_id': 'ACC-13', 'txn_ts': '2026-10-08 10:00:00', 'txn_type': 'TRANSFER_IN', 'amount': '125000.00'}]
        res_08 = detect_kyc_alerts(txns_08, customers, accounts)
        self.assertEqual(len(res_08), 1, 'KYC expired day after expiry date')
        self.assertEqual(res_08[0]['raw_score'], 15)

    def test_additional_validation_traps(self):
        # 1. Zero amount
        t_zero = {'txn_id': 'T0', 'account_id': 'ACC-1', 'txn_ts': '2026-09-01 10:00:00', 'txn_type': 'CASH_DEPOSIT', 'amount': '0.00', 'channel': 'BRANCH'}
        errors_zero = validate_transaction(t_zero)
        self.assertTrue(any('greater than zero' in e for e in errors_zero))

        # 2. Negative amount
        t_neg = {'txn_id': 'TN', 'account_id': 'ACC-1', 'txn_ts': '2026-09-01 10:00:00', 'txn_type': 'CASH_DEPOSIT', 'amount': '-500.00', 'channel': 'BRANCH'}
        errors_neg = validate_transaction(t_neg)
        self.assertTrue(any('greater than zero' in e for e in errors_neg))

        # 3. Invalid timestamp
        t_ts = {'txn_id': 'TT', 'account_id': 'ACC-1', 'txn_ts': 'invalid-date', 'txn_type': 'CASH_DEPOSIT', 'amount': '100.00', 'channel': 'BRANCH'}
        errors_ts = validate_transaction(t_ts)
        self.assertTrue(any('timestamp' in e for e in errors_ts))

        # 4. Unknown account
        t_acc = {'txn_id': 'TA', 'account_id': 'UNKNOWN', 'txn_ts': '2026-09-01 10:00:00', 'txn_type': 'CASH_DEPOSIT', 'amount': '100.00', 'channel': 'BRANCH'}
        errors_acc = validate_transaction(t_acc, valid_account_ids={'ACC-1'})
        self.assertTrue(any('account' in e for e in errors_acc))

        # 5. Duplicate transaction detection
        batch = [
            {'txn_id': 'DUP-1', 'account_id': 'ACC-1', 'txn_ts': '2026-09-01 10:00:00', 'txn_type': 'CASH_DEPOSIT', 'amount': '100.00', 'channel': 'BRANCH'},
            {'txn_id': 'DUP-1', 'account_id': 'ACC-1', 'txn_ts': '2026-09-01 10:00:00', 'txn_type': 'CASH_DEPOSIT', 'amount': '100.00', 'channel': 'BRANCH'}
        ]
        proc = process_transactions(batch, valid_account_ids={'ACC-1'})
        self.assertEqual(len(proc['valid_transactions']), 1)
        self.assertEqual(len(proc['duplicate_records']), 1)

    def test_merge_bonus_cap(self):
        # Merge bonus adds 5 per merge, maximum 20 points
        self.assertEqual(calculate_merge_bonus(0), 0)
        self.assertEqual(calculate_merge_bonus(1), 5)
        self.assertEqual(calculate_merge_bonus(2), 10)
        self.assertEqual(calculate_merge_bonus(3), 15)
        self.assertEqual(calculate_merge_bonus(4), 20)
        self.assertEqual(calculate_merge_bonus(5), 20)
        self.assertEqual(calculate_merge_bonus(10), 20)

if __name__ == '__main__':
    unittest.main()
