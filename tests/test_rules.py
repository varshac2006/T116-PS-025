import unittest
from datetime import datetime, date, timedelta
from src.rules_engine import (
    detect_daily_ctr,
    detect_monthly_ctr,
    detect_structuring,
    detect_velocity,
    detect_rapid_movement,
    detect_dormant_reactivation,
    detect_pep_alerts,
    detect_kyc_alerts,
    calculate_weighted_score,
    evaluate_alert_threshold,
    calculate_merge_bonus
)
from src.alert_manager import calculate_alert_score, build_alert_record

class TestRulesEngine(unittest.TestCase):

    def test_br01_daily_ctr(self):
        # Daily CTR: cash transactions > 10,00,000 in a day for an account
        txns_below = [
            {'txn_id': 'TXN-1', 'account_id': 'ACC-1', 'txn_ts': '2026-09-01 10:00:00', 'txn_type': 'CASH_DEPOSIT', 'amount': '1000000.00'}
        ]
        self.assertEqual(len(detect_daily_ctr(txns_below)), 0, 'Exact 10,00,000 should not trigger daily CTR')

        txns_above = [
            {'txn_id': 'TXN-1', 'account_id': 'ACC-1', 'txn_ts': '2026-09-01 10:00:00', 'txn_type': 'CASH_DEPOSIT', 'amount': '600000.00'},
            {'txn_id': 'TXN-2', 'account_id': 'ACC-1', 'txn_ts': '2026-09-01 14:00:00', 'txn_type': 'CASH_WITHDRAWAL', 'amount': '450000.00'}
        ]
        res = detect_daily_ctr(txns_above)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]['total_cash'], 1050000.00)
        self.assertEqual(res[0]['due_date'], '2026-10-15')
        self.assertEqual(res[0]['txn_ids'], ['TXN-1', 'TXN-2'])

    def test_br02_monthly_ctr(self):
        txns = [
            {'txn_id': 'TXN-1', 'account_id': 'ACC-1', 'txn_ts': '2026-09-05 10:00:00', 'txn_type': 'CASH_DEPOSIT', 'amount': '500000.00'},
            {'txn_id': 'TXN-2', 'account_id': 'ACC-1', 'txn_ts': '2026-09-20 10:00:00', 'txn_type': 'CASH_DEPOSIT', 'amount': '550000.00'}
        ]
        res = detect_monthly_ctr(txns)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]['total_cash'], 1050000.00)
        self.assertEqual(res[0]['due_date'], '2026-10-15')

    def test_br03_structuring(self):
        accounts = [{'account_id': 'ACC-1', 'customer_id': 'CUST-1'}]
        # 3 deposits within band 9,00,000 - 9,99,999 within 7 days, single branch -> score 40
        txns_single_branch = [
            {'txn_id': 'T1', 'account_id': 'ACC-1', 'branch_id': 'BR-01', 'txn_ts': '2026-09-01 10:00:00', 'txn_type': 'CASH_DEPOSIT', 'amount': '900000.00'},
            {'txn_id': 'T2', 'account_id': 'ACC-1', 'branch_id': 'BR-01', 'txn_ts': '2026-09-03 10:00:00', 'txn_type': 'CASH_DEPOSIT', 'amount': '950000.00'},
            {'txn_id': 'T3', 'account_id': 'ACC-1', 'branch_id': 'BR-01', 'txn_ts': '2026-09-05 10:00:00', 'txn_type': 'CASH_DEPOSIT', 'amount': '999999.00'}
        ]
        res = detect_structuring(txns_single_branch, accounts)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]['raw_score'], 40)

        # Multi-branch (>= 2 branches) -> score 60
        txns_multi_branch = [
            {'txn_id': 'T1', 'account_id': 'ACC-1', 'branch_id': 'BR-01', 'txn_ts': '2026-09-01 10:00:00', 'txn_type': 'CASH_DEPOSIT', 'amount': '900000.00'},
            {'txn_id': 'T2', 'account_id': 'ACC-1', 'branch_id': 'BR-02', 'txn_ts': '2026-09-03 10:00:00', 'txn_type': 'CASH_DEPOSIT', 'amount': '950000.00'},
            {'txn_id': 'T3', 'account_id': 'ACC-1', 'branch_id': 'BR-01', 'txn_ts': '2026-09-05 10:00:00', 'txn_type': 'CASH_DEPOSIT', 'amount': '999999.00'}
        ]
        res_multi = detect_structuring(txns_multi_branch, accounts)
        self.assertEqual(len(res_multi), 1)
        self.assertEqual(res_multi[0]['raw_score'], 60)

    def test_br04_velocity(self):
        accounts = [{'account_id': 'ACC-1', 'customer_id': 'CUST-1', 'open_date': '2026-01-01'}]
        customers = [{'customer_id': 'CUST-1', 'expected_monthly_turnover': '100000.00', 'risk_rating': 'MEDIUM'}]
        
        # Exact 3x -> no alert (must be strictly > 3x)
        txns_3x = [{'txn_id': 'T1', 'account_id': 'ACC-1', 'txn_ts': '2026-09-10 10:00:00', 'txn_type': 'TRANSFER_IN', 'amount': '300000.00'}]
        res_3x = detect_velocity(txns_3x, accounts, customers, '2026-09-15')
        self.assertEqual(len(res_3x), 0)

        # 3.5x -> score 30
        txns_over_3x = [{'txn_id': 'T1', 'account_id': 'ACC-1', 'txn_ts': '2026-09-10 10:00:00', 'txn_type': 'TRANSFER_IN', 'amount': '350000.00'}]
        res_over_3x = detect_velocity(txns_over_3x, accounts, customers, '2026-09-15')
        self.assertEqual(len(res_over_3x), 1)
        self.assertEqual(res_over_3x[0]['raw_score'], 30)

        # 5.5x -> score 50
        txns_over_5x = [{'txn_id': 'T1', 'account_id': 'ACC-1', 'txn_ts': '2026-09-10 10:00:00', 'txn_type': 'TRANSFER_IN', 'amount': '550000.00'}]
        res_over_5x = detect_velocity(txns_over_5x, accounts, customers, '2026-09-15')
        self.assertEqual(len(res_over_5x), 1)
        self.assertEqual(res_over_5x[0]['raw_score'], 50)

    def test_br05_br06_rapid_movement_and_round_trip(self):
        # Credit > 2,00,000 followed by transfer out >= 80% within 48h
        txns = [
            {'txn_id': 'T1', 'account_id': 'ACC-1', 'txn_ts': '2026-09-10 10:00:00', 'txn_type': 'TRANSFER_IN', 'amount': '500000.00', 'counterparty_account': 'ACC-X'},
            {'txn_id': 'T2', 'account_id': 'ACC-1', 'txn_ts': '2026-09-11 12:00:00', 'txn_type': 'TRANSFER_OUT', 'amount': '400000.00', 'counterparty_account': 'ACC-Y'}
        ]
        res = detect_rapid_movement(txns)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]['raw_score'], 35)
        self.assertFalse(res[0]['round_trip_detected'])

        # Same counterparty -> round trip +25 = score 60
        txns[1]['counterparty_account'] = 'ACC-X'
        res_rt = detect_rapid_movement(txns)
        self.assertEqual(len(res_rt), 1)
        self.assertEqual(res_rt[0]['raw_score'], 60)
        self.assertTrue(res_rt[0]['round_trip_detected'])

    def test_br07_dormant_reactivation(self):
        prior = [
            {'txn_id': 'P1', 'account_id': 'ACC-1', 'txn_ts': '2025-06-01 10:00:00', 'txn_type': 'CASH_DEPOSIT', 'amount': '10000.00'},
            {'txn_id': 'P2', 'account_id': 'ACC-1', 'txn_ts': '2025-12-31 10:00:00', 'txn_type': 'INTEREST_CREDIT', 'amount': '250.00'}
        ]
        daily = [
            {'txn_id': 'D1', 'account_id': 'ACC-1', 'txn_ts': '2026-09-15 10:00:00', 'txn_type': 'TRANSFER_IN', 'amount': '550000.00'}
        ]
        accounts = [{'account_id': 'ACC-1', 'customer_id': 'CUST-1'}]
        res = detect_dormant_reactivation(daily, prior, accounts, '2026-09-15')
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]['raw_score'], 30)

    def test_br08_pep(self):
        customers = [
            {'customer_id': 'CUST-P', 'pep_flag': 'true', 'pep_linked_customer': '', 'risk_rating': 'HIGH'},
            {'customer_id': 'CUST-F', 'pep_flag': 'false', 'pep_linked_customer': 'CUST-P', 'risk_rating': 'HIGH'}
        ]
        accounts = [
            {'account_id': 'ACC-P', 'customer_id': 'CUST-P'},
            {'account_id': 'ACC-F', 'customer_id': 'CUST-F'}
        ]
        txns = [
            {'txn_id': 'T1', 'account_id': 'ACC-P', 'txn_ts': '2026-09-01 10:00:00', 'txn_type': 'CASH_DEPOSIT', 'amount': '600000.00'},
            {'txn_id': 'T2', 'account_id': 'ACC-F', 'txn_ts': '2026-09-01 11:00:00', 'txn_type': 'TRANSFER_IN', 'amount': '550000.00'}
        ]
        res = detect_pep_alerts(txns, customers, accounts)
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0]['customer_id'], 'CUST-P')
        self.assertEqual(res[1]['customer_id'], 'CUST-F')

    def test_br09_kyc_expiry(self):
        customers = [{'customer_id': 'CUST-1', 'kyc_expiry_date': '2026-09-10'}]
        accounts = [{'account_id': 'ACC-1', 'customer_id': 'CUST-1'}]
        
        # Credit on expiry date itself -> valid (no alert)
        txns_on_date = [{'txn_id': 'T1', 'account_id': 'ACC-1', 'txn_ts': '2026-09-10 15:00:00', 'txn_type': 'TRANSFER_IN', 'amount': '200000.00'}]
        self.assertEqual(len(detect_kyc_alerts(txns_on_date, customers, accounts)), 0)

        # Credit after expiry date -> expired -> score 15
        txns_after = [{'txn_id': 'T2', 'account_id': 'ACC-1', 'txn_ts': '2026-09-11 10:00:00', 'txn_type': 'TRANSFER_IN', 'amount': '200000.00'}]
        res = detect_kyc_alerts(txns_after, customers, accounts)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]['raw_score'], 15)

    def test_scoring_precedence(self):
        # 1. raw 40 + pep adder 20 = 60 -> * 1.5 (HIGH) = 90.0 + merge 5 = 95.0 -> PRIORITY
        score_info = calculate_alert_score(raw_score=40, risk_rating='HIGH', pep_kyc_adders=20, merge_count=1)
        self.assertEqual(score_info['weighted_score'], 95.0)
        self.assertTrue(score_info['priority'])

if __name__ == '__main__':
    unittest.main()
