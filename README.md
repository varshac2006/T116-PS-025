# PS-025: AML Transaction Monitoring System
### Structuring, Velocity, Rapid Movement, Dormant Reactivation & PEP Rules

**Team:** T116  
**Domain:** BFSI Compliance & Regulatory Reporting (FIU-IND / PMLA)  
**Technology:** Python 3.10+ (Standard Library Only - Zero Third-Party Dependencies)  
**Architecture:** Deterministic, Command-File-Driven Backend Application  

---

## 1. Project Overview

This repository contains the submission-ready implementation of **PS-025 - AML Transaction Monitoring System** for BFSI regulatory compliance. The system ingests daily retail banking transactions, validates data integrity, evaluates Anti-Money Laundering (AML) typologies and business rules (BR-01 through BR-12), manages investigative cases with working-day SLA clocks, and produces regulatory reports (CTR, STR, Alert Log, Case Register) matching official FIU-IND and assignment specifications.

### Key Highlights
- **100% Native Python 3.10+**: No third-party package dependencies required (pandas, numpy, or pytest not needed). Completely self-contained and cross-platform.
- **Deterministic Evaluation**: Commands in `data/commands.txt` are executed strictly in order, guaranteeing reproducible outputs and idempotent state transitions.
- **Exhaustive Edge-Case Coverage**: Fully validates official planted edge cases (EC-01 through EC-08) including exact threshold boundaries, rolling windows, multi-branch deposits, rapid round trips, dormant reactivation with system interest exclusions, PEP family-member propagation, and Saturday working-day SLA breaches.
- **Robust Case Management**: State machine supporting `OPEN`, `UNDER_REVIEW`, `ESCALATED`, `CLOSED_NO_ACTION`, and irreversible `STR_FILED` states, integrated with the official working-day calendar.

---

## 2. Directory Structure

```
AML_PS025_OFFICIAL/
├── main.py                     # Main application entry point
├── README.md                   # Project documentation & execution guide
├── DESIGN_DOCUMENT.md          # Comprehensive technical design doc & viva guide
├── data/                       # Authoritative official sample dataset
│   ├── accounts.csv            # 44 customer accounts
│   ├── branches.csv            # 6 physical branches
│   ├── calendar.csv            # 122 working-day calendar entries (Sept-Dec 2026)
│   ├── customers.csv           # 40 customer master records
│   ├── prior_transactions.csv  # 90 historical/dormancy baseline transactions
│   ├── commands.txt            # Master command sequence
│   └── transactions/           # 60 daily CSV files (2026-09-01 to 2026-10-30; 502 total rows)
├── data_backup/                # Protected backup of official dataset
├── reports/                    # Generated regulatory reports (CSV)
│   ├── alert_log.csv           # Raised and merged AML alerts
│   ├── case_register.csv       # Investigative case lifecycle and SLA audit
│   ├── ctr_2026_09.csv         # Monthly and daily Cash Transaction Report
│   └── str_report.csv          # Filed Suspicious Transaction Reports
├── src/                        # Modular application source code
│   ├── __init__.py
│   ├── alert_manager.py        # Alert scoring, suppression, merging, and priority overrides
│   ├── case_manager.py         # Case state machine, working-day SLA clocks, and audit logging
│   ├── command_processor.py    # Command parser, day orchestrator, and report dispatcher
│   ├── data_loader.py          # Master data and transaction file loader
│   ├── report_generator.py     # CSV report builder with exact formatting and schema enforcement
│   ├── rules_engine.py         # Pure business rule detectors (BR-01 through BR-12)
│   └── transaction_processor.py# Ingestion validation, duplicate filtering, error logging
└── tests/                      # Automated test suite (28 passing tests)
    ├── __init__.py
    ├── test_rules.py           # Unit tests for BR-01 through BR-09
    ├── test_edge_cases.py      # Tests for EC-01 to EC-08 and validation traps
    ├── test_case_management.py # Case transitions, SLA breaches, and STR irreversibility
    ├── test_reports.py         # Report schemas, delimiters, and monetary formats
    └── test_integration.py     # End-to-end full pipeline execution test
```

---

## 3. Quick Start & Execution

### Prerequisites
- Python 3.10+ installed.
- Zero external package requirements.

### Run Main Application
Execute from the project root directory:
```powershell
python main.py
```
This processes all 60 daily transaction files, executes case management actions, evaluates rules, and generates all 4 regulatory reports in `reports/`.

### Run Automated Test Suite
Run the test suite using Python built-in unittest runner:
```powershell
py -m unittest discover -s tests -v
```
The automated test suite contains 28 tests covering business rules, edge cases, case management, report generation, and end-to-end system execution.

---

## 4. AML Business Rules Implemented

| Rule ID | Rule Name | Description | Base Score / Threshold |
|---|---|---|---|
| **BR-01** | CTR Daily | Aggregate cash transactions (deposits + withdrawals) per account in a single calendar day > Rs 10,00,000. | Deadline: 15th of next month |
| **BR-02** | CTR Monthly | Aggregate cash transactions per account in a calendar month > Rs 10,00,000. | Deadline: 15th of next month |
| **BR-03** | Structuring | 3 or more cash deposits between Rs 9,00,000 and Rs 9,99,999 inclusive within rolling 7 calendar days. | Base: 40; Multi-branch (>=2 branches): +20 |
| **BR-04** | Velocity | Total credits in rolling 30-day window > 3x monthly turnover (score 30); > 5x turnover (score 50). Accounts < 90 days use Rs 2,00,000 default. | Score: 30 / 50 |
| **BR-05** | Rapid Movement | Credit > Rs 2,00,000 followed by >= 80% transferred out within 48 hours. | Score: 35 |
| **BR-06** | Round Trip | Outward transfer counterparty matches inward credit counterparty. | Bonus: +25 to Rapid Movement |
| **BR-07** | Dormant Reactivation | No customer activity for 365 days, followed by > Rs 5,00,000 activity within 30 days. System interest credits excluded. | Score: 30 |
| **BR-08** | PEP Activity | Any single transaction > Rs 5,00,000 by PEP customer or listed family member. PEPs receive +20 adder on all alerts. | Score: 20 (+20 adder) |
| **BR-09** | KYC Expiry | Credit > Rs 1,00,000 on account with expired KYC (txn_date > expiry). Expired KYC adds +10 to existing alerts. | Score: 15 (+10 adder) |
| **BR-10** | Risk Multiplier | LOW: 0.8x, MEDIUM: 1.0x, HIGH: 1.5x. | Multiplier |
| **BR-11** | Alert Threshold | Weighted score >= 50: NORMAL alert; Weighted score >= 70: PRIORITY alert. | Threshold |
| **BR-12** | Merging & Suppression | Same customer and rule within 7 days of previous alert merges into existing case; +5 points per merge (cap: 20). | Max bonus: 20 |

---

## 5. Output Reports Specification

All generated reports in `reports/` strictly adhere to the official sample data pack specification:
1. **`alert_log.csv`**: Contains `alert_id,eval_date,customer_id,rule_ids,raw_score,pep_kyc_adders,risk_multiplier,merge_bonus,weighted_score,priority,case_id,action,evidence_txn_ids`. Evidence IDs are space-separated in chronological order.
2. **`case_register.csv`**: Contains `case_id,customer_id,opened_on,priority,state,under_review_on,escalated_on,closed_on,str_filed_on,sla_breaches,alert_ids`. Alert IDs and SLA breaches are space-separated.
3. **`ctr_2026_09.csv`**: Contains `account_id,customer_id,ctr_type,txn_date_or_month,total_cash,txn_ids,due_date`. Due date is populated (`2026-10-15`), amounts have 2 decimals (`1050000.00`).
4. **`str_report.csv`**: Contains `str_id,case_id,customer_id,escalated_on,filed_on,within_sla,total_amount,evidence_txn_ids`. Amounts have 2 decimals, evidence IDs space-separated.

---

## 6. Viva Voce & Design Documentation

For complete architecture details, regulatory background, decision log, and viva interview preparation, refer to:
- [DESIGN_DOCUMENT.md](DESIGN_DOCUMENT.md)
