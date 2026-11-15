# PS-025: AML Transaction Monitoring System
## Engineering Design Document & Technical Viva Reference

**Problem Statement:** PS-025 – AML Transaction Monitoring with Structuring, Velocity and PEP Rules  
**Team:** T116  
**Domain:** Banking, Financial Services & Insurance (BFSI) Compliance  
**Author:** Senior Software Engineer, AML Domain Expert & QA Lead  
**Submission Date:** November 2026  

---

## 1. Executive Summary

This document details the architectural design, mathematical models, regulatory foundations, and verification results for the Anti-Money Laundering (AML) Transaction Monitoring engine developed for Problem Statement **PS-025**.

The engine processes retail banking transactions, identifies illicit typologies (structuring, velocity abuse, rapid movements, round-tripping, dormant account reactivation, PEP exposure, and expired-KYC credits), orchestrates investigation workflows under strict regulatory Service Level Agreements (SLAs), and produces submission-grade regulatory returns (CTR and STR) complying with Financial Intelligence Unit – India (FIU-IND) and Prevention of Money Laundering Act (PMLA) norms.

---

## 2. Regulatory & Business Context

### 2.1 Prevention of Money Laundering Act (PMLA) & FIU-IND Guidelines
In banking operations, financial institutions must maintain a record of all transactions and report specified cash and suspicious activities to FIU-IND:
1. **Cash Transaction Report (CTR)**:
   - **Daily CTR (BR-01)**: All cash transactions (deposits and withdrawals) where the day’s aggregate cash exceeds ₹10,00,000 for an individual account.
   - **Monthly CTR (BR-02)**: Series of integrally connected cash transactions totalling more than ₹10,00,000 in a calendar month.
   - **Statutory Deadline**: 15th day of the succeeding month (e.g., September CTR is due by October 15).
2. **Suspicious Transaction Report (STR)**:
   - Mandatory filing for transactions giving rise to reasonable suspicion of being proceeds of crime, unusually complex, or lacking economic rationale.
   - **Statutory SLA**: Filed within 7 working days of principal officer escalation.
3. **Politically Exposed Persons (PEPs)**:
   - Senior public officials, political figures, and their immediate family members/close associates present elevated corruption and money laundering risk. Enhanced Due Diligence (EDD) applies, including lower alert thresholds and familial linkage.

---

## 3. System Architecture & Component Design

The application follows a **deterministic, command-file-driven pipeline** architecture built entirely on Python 3.10+ standard libraries with zero external dependencies.

```
                  ┌───────────────────────────────┐
                  │          commands.txt         │
                  └───────────────┬───────────────┘
                                  │ (Strict File Order)
                                  ▼
                     ┌────────────────────────┐
                     │  AMLCommandProcessor   │
                     └────────────┬───────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          ▼                       ▼                       ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   Data Loader    │    │ Transaction Proc │    │   Rules Engine   │
│ (Master & Daily) │    │ (Validate & Dedup│    │ (BR-01 to BR-12) │
└──────────────────┘    └──────────────────┘    └─────────┬────────┘
                                                          │
                                                          ▼
                                                ┌──────────────────┐
                                                │  Alert Manager   │
                                                │ (Scoring BR-16)  │
                                                └─────────┬────────┘
                                                          │
                                                          ▼
                                                ┌──────────────────┐
                                                │   Case Manager   │
                                                │ (SLA Clocks)     │
                                                └─────────┬────────┘
                                                          │
                                                          ▼
                                                ┌──────────────────┐
                                                │ Report Generator │
                                                │ (CTR, STR, Logs) │
                                                └──────────────────┘
```

### 3.1 Component Responsibilities
- `src.data_loader`: Loads master entities (`customers.csv`, `accounts.csv`, `branches.csv`, `calendar.csv`, `prior_transactions.csv`) and parses `commands.txt` ignoring comments and whitespace.
- `src.transaction_processor`: Validates required fields, timestamp formats, positive finite amounts, known accounts, known branches, and filters duplicate transaction IDs (internal and cross-day).
- `src.rules_engine`: Implements pure, isolated detection algorithms for BR-01 through BR-12.
- `src.alert_manager`: Executes the prescribed BR-16 multi-step scoring pipeline, applies customer risk multipliers, suppression windows, merge bonuses, and 6-month STR priority overrides.
- `src.case_manager`: Manages the case state machine (`OPEN` -> `UNDER_REVIEW` -> `ESCALATED` -> `STR_FILED` / `CLOSED_NO_ACTION`), enforces working-day SLA clocks using `calendar.csv`, and prevents duplicate alerts.
- `src.report_generator`: Exports official evaluation CSVs (`alert_log.csv`, `case_register.csv`, `ctr_2026_09.csv`, `str_report.csv`) conforming to exact schemas and column formats.

---

## 4. AML Business Rules Specification

### BR-01 & BR-02: Cash Transaction Reports (CTR)
- **Daily CTR (BR-01)**: Identifies accounts where total cash (`CASH_DEPOSIT` + `CASH_WITHDRAWAL`) strictly exceeds ₹10,00,000 on a single date.
- **Monthly CTR (BR-02)**: Identifies accounts where total cash transactions across a calendar month strictly exceed ₹10,00,000.
- **Due Date**: Computed dynamically as the 15th of the subsequent month (e.g., `2026-10-15` for September transactions).

### BR-03: Structuring (Smurfing)
- Detects deliberate evasion of the ₹10 lakh CTR threshold via 3 or more cash deposits, each between ₹9,00,000 and ₹9,99,999 inclusive, within any rolling 7-day window.
- **Base Score**: 40.
- **Branch Dispersion Adder**: If deposits occur across 2 or more distinct branch IDs, adds +20 points (total raw score = 60).
- **Window Boundary**: Strictly inclusive of $7 \times 24$ hours from the initial deposit timestamp.

### BR-04: Velocity Abuse
- Identifies rapid credit accumulation disproportionate to customer declared profile within a rolling 30-day window (`evaluation_date - 30 days` to `evaluation_date 23:59:59`).
- Considers incoming credits (`CASH_DEPOSIT`, `TRANSFER_IN`).
- **Account Age Rule**: If account age on the evaluation date is $< 90$ days, expected monthly turnover is overridden to ₹2,00,000 regardless of master data.
- **Thresholds**:
  - Credits $> 5 \times$ Expected Turnover: Raw Score = 50.
  - Credits $> 3 \times$ Expected Turnover (and $\le 5\times$): Raw Score = 30.
  - Credits $\le 3 \times$ Expected Turnover: No score (0).

### BR-05 & BR-06: Rapid Movement & Round Trip
- **Rapid Movement (BR-05)**: An incoming credit $> ₹2,00,000$ where $\ge 80\%$ is transferred out via `TRANSFER_OUT` within 48 hours ($t_{\text{credit}} < t_{\text{debit}} \le t_{\text{credit}} + 48\,\text{hours}$). Raw Score = 35.
- **Round Trip (BR-06)**: If the outward transfer's counterparty account matches the inward transfer's counterparty account, an additional +25 points are added (total raw score = 60).

### BR-07: Dormant Account Reactivation
- Identifies accounts with no customer-initiated transactions for $\ge 365$ days, followed by aggregate activity $> ₹5,00,000$ within a 30-day window.
- **Exclusion**: System interest credits (`INTEREST_CREDIT`) during the 12 months do **not** break dormancy. Raw Score = 30.

### BR-08: Politically Exposed Persons (PEP)
- Any single transaction $> ₹5,00,000$ by a PEP customer (or a family member linked via `pep_linked_customer`) independently generates an alert with base score 20.
- PEP status also adds a mandatory +20 adder to **every** alert raised for that customer.

### BR-09: Expired KYC
- A credit $> ₹1,00,000$ on an account with expired KYC independently generates an alert with score 15.
- KYC is valid on the expiry date itself; it is expired strictly when $\text{txn\_date} > \text{kyc\_expiry\_date}$.
- Expired KYC adds +10 points to any existing alert.

---

## 5. Scoring & Precedence Order (BR-16)

The engine implements strict scoring precedence:
1. **Base Rule Score**: $S_{\text{raw}}$ computed from detected typology (e.g., 40, 50, 35, 30, 20, 15).
2. **PEP & KYC Adders**:
   $$S_{\text{adjusted}} = S_{\text{raw}} + A_{\text{PEP}} + A_{\text{KYC}}$$
   where $A_{\text{PEP}} = 20$ (if PEP or linked family member) and $A_{\text{KYC}} = 10$ (if KYC expired on transaction date).
3. **Customer Risk Multiplier**:
   $$S_{\text{weighted}} = S_{\text{adjusted}} \times M_{\text{risk}}$$
   Multipliers: `HIGH` = 1.5, `MEDIUM` = 1.0, `LOW` = 0.8.
4. **Suppression & Merge Bonus**:
   If the same customer and same rule fired within 7 days of a previous alert:
   - Merged into the existing case (`action: MERGED`).
   - Adds +5 points per merge event, capped at +20:
     $$S_{\text{final}} = S_{\text{weighted}} + \min(\text{merge\_count} \times 5, 20)$$
5. **Threshold Evaluation**:
   - $S_{\text{final}} \ge 50.0 \implies$ Alert Generated.
   - $S_{\text{final}} \ge 70.0 \implies$ `PRIORITY` Case.
   - **STR Priority Override**: Any customer who had an STR filed within the preceding 6 months (183 days) is automatically tagged `PRIORITY` on all new alerts regardless of score.

---

## 6. Case Management State Machine & SLA Clocks

```
           [Alert Raised]
                 │
                 ▼
             ┌───────┐
             │ OPEN  │
             └───┬───┘
                 │ START_REVIEW
                 ▼
         ┌───────────────┐
         │ UNDER_REVIEW  │
         └───┬───────┬───┘
             │       │
    ESCALATE │       │ CLOSE_NO_ACTION
             ▼       ▼
       ┌───────────┐ ┌──────────────────┐
       │ ESCALATED │ │ CLOSED_NO_ACTION │
       └───┬───┬───┘ └──────────────────┘
           │   │
  FILE_STR │   │ CLOSE_NO_ACTION
           ▼   ▼
     ┌───────────┐
     │ STR_FILED │ (Irreversible State)
     └───────────┘
```

### 6.1 Regulatory SLA Audit Clocks
SLA clocks calculate elapsed **working days** using `calendar.csv`. The trigger date is day 0; counting begins at $t + 1$ day:
1. **Initial Review SLA**:
   - `NORMAL` Case: Must be reviewed (`START_REVIEW`) within **2 working days**.
   - `PRIORITY` Case: Must be reviewed (`START_REVIEW`) within **1 working day**.
   - If elapsed working days exceeds the limit, the transition breach is recorded as `UNDER_REVIEW`.
2. **STR Filing SLA**:
   - Must be filed (`FILE_STR`) within **7 working days** of escalation (`ESCALATED`).
   - If elapsed working days $> 7$, the transition breach is recorded as `STR_FILED`.

---

## 7. Edge-Case Verification Log

The system was verified against all 8 planted scenarios and extra traps documented in the official sample pack:

| Scenario | Customer | Planted Behavior | Engine Result | Status |
|---|---|---|---|---|
| **EC-01** | CUST-032 / CUST-009 | Deposit exactly ₹9,00,000 inside band; deposit exactly ₹10,00,000 does not trigger daily CTR. | CUST-032 triggers BR-03; CUST-009 does not trigger BR-01. | PASS |
| **EC-02** | CUST-018 | Third deposit exactly 7 days ($7 \times 24\,\text{h}$) after first; deposits across BR-01 and BR-02. | Triggers BR-03 with raw score 60 (40 base + 20 multi-branch); weighted score 90.0 (`PRIORITY`). | PASS |
| **EC-03** | CUST-007 | RTGS credit ₹5,00,000 followed by ₹4,00,000 out at exact hour 48. | Triggers BR-05 with raw score 35; hour 48 inclusive. | PASS |
| **EC-04** | CUST-015 | Account dormant for 451 days with only SB interest credits; reactivated with ₹5,90,000 credits. | Interest credits excluded from customer activity; dormancy correctly identified. | PASS |
| **EC-05** | CUST-030 | LOW-risk customer with velocity credits; sub-threshold on day 1 (40.0) merges twice to reach exactly 50.0. | ALT-00019 raised on 2026-10-15 with weighted score 50.0. | PASS |
| **EC-06** | CUST-023 | Second structuring set occurs on day 7 after prior alert. | Merged into CASE-0001 on exact 7-day boundary with +5 merge bonus. | PASS |
| **EC-07** | CUST-010 | PRIORITY case opened Friday 2026-09-18; Sat 2026-09-19 is marked working in calendar. | Review on Monday 2026-09-21 breaches 1-working-day SLA; logged as `UNDER_REVIEW`. | PASS |
| **EC-08** | CUST-013 | KYC expiry date 2026-10-07; credit on 2026-10-07 valid; credit on 2026-10-08 expired. | Credit on 10-07 does not alert; credit on 10-08 scores 15. | PASS |
| **Trap: PEP Link** | CUST-021 | Family member linked to PEP (CUST-020) via `pep_linked_customer`. | Triggers BR-08 on ₹5,50,000 deposit; receives +20 PEP adder (score 60.0). | PASS |
| **Trap: STR Tag** | CUST-023 | After STR filed on 2026-09-16, subsequent rapid movement alert occurs on 2026-10-22. | Overridden to `priority: true` due to 6-month STR tag. | PASS |
| **Trap: New Account** | CUST-019 | Account opened 2026-08-10 ($< 90$ days old); turnover declared as ₹8,00,000. | Turnover overridden to ₹2,00,000; credits $> 5\times$ trigger BR-04 with score 50. | PASS |
| **Trap: Duplicate** | N/A | Duplicate transaction `TXN-000084` planted in `txn_2026_09_10.csv`. | Counted once; exactly 1 duplicate recorded. | PASS |
| **Trap: Invalid Row** | N/A | `TXN-000330` with `amount = 0.00` in `txn_2026_10_09.csv`. | Rejected and recorded in invalid records; not evaluated in rules. | PASS |

---

## 8. Decision Log & Design Rationale

1. **Space-Separated Multi-Value Fields**:
   - *Rationale*: Section 212 of the authoritative `README.md` explicitly specifies: *"evidence IDs space-separated in chronological order."* Using spaces prevents CSV parsing collisions and complies with automated evaluation test fixtures.
2. **Representation of SLA Breaches**:
   - *Rationale*: Section 234 dictates: *"`sla_breaches` lists the breached transitions separated by spaces (e.g. `UNDER_REVIEW`), empty if none."* Transition target states (`UNDER_REVIEW`, `STR_FILED`) are recorded rather than informal verbs (`REVIEW`, `STR`).
3. **Idempotent Day Execution**:
   - *Rationale*: Added `self.processed_days` tracking to `AMLCommandProcessor` to guarantee that executing `RUN_DAY` twice on the same date will not duplicate alerts or re-ingest records.
4. **Zero-Dependency Architecture**:
   - *Rationale*: Built exclusively with Python's built-in `csv`, `datetime`, `collections`, and `unittest` packages. Guarantees 100% portable evaluation in any Python 3.10+ environment without environment version mismatches.

---

## 9. Comprehensive Viva Voce Preparation Guide

### Q1: What is the primary difference between a CTR and an STR?
**Answer:** A Cash Transaction Report (CTR) is an objective, threshold-based regulatory filing for all cash transactions exceeding ₹10,00,000 in a day or calendar month per account, regardless of whether any wrongdoing is suspected. A Suspicious Transaction Report (STR) is subjective and risk-based, filed whenever transactions exhibit patterns indicative of money laundering, structuring, or illicit origin regardless of amount.

### Q2: How does the system prevent structuring (smurfing)?
**Answer:** Under BR-03, the system maintains rolling 7-day chronological windows per account and identifies deposits between ₹9,00,000 and ₹9,99,999. If 3 or more such deposits occur, an alert is raised with base score 40. If the customer distributed these deposits across 2 or more physical branches to avoid local scrutiny, the system adds +20 points.

### Q3: Explain how the working-day SLA calculation handles bank holidays and weekends.
**Answer:** The `CaseManager.working_days_between(start_date, end_date)` function iterates day-by-day excluding the start date through the end date, looking up each date in `calendar.csv`. A day increments the SLA clock if and only if `is_working_day == True`. This automatically skips Sundays, second/fourth Saturdays, and gazetted holidays, while counting working Saturdays (such as Saturday 2026-09-19 in EC-07).

### Q4: Why are interest credits excluded from dormancy calculations?
**Answer:** Under RBI and PMLA guidelines, bank-initiated interest postings (`INTEREST_CREDIT`) are system-generated and do not represent customer-initiated activity. An account remains dormant if the customer has not actively transacted for 365 days. Counting interest credits as activity would improperly reset the dormancy clock.

### Q5: What is the exact mathematical scoring formula under BR-16?
**Answer:**
$$\text{Score} = \left(\left(\text{Raw Score} + \text{PEP Adder} + \text{KYC Adder}\right) \times \text{Risk Multiplier}\right) + \text{Merge Bonus}$$
- PEP Adder = +20 (for PEPs and family members).
- KYC Adder = +10 (if KYC expired on transaction date).
- Risk Multiplier: HIGH (1.5x), MEDIUM (1.0x), LOW (0.8x).
- Merge Bonus: +5 for each repeat finding within 7 days, capped at +20.
- Alert Threshold: $\ge 50.0$ for Normal alert; $\ge 70.0$ for Priority alert.
- STR Override: Customers with an STR filed in the last 6 months are automatically marked `priority: true`.

---

## 10. Test Execution Verification

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

### Verification Output:
- **Total Tests:** 28
- **Passed:** 28
- **Failed:** 0
- **Errors:** 0
- **Execution Time:** ~0.9 seconds
