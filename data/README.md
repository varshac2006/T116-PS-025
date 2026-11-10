# PS-025 – AML Transaction Monitoring with Structuring, Velocity and PEP Rules — Sample Data Pack

Prepared by 10 SECONDS for Team T116.

Monitoring window: 60 calendar days, 2026-09-01 to 2026-10-30, one transaction file per day under `transactions/`. SLA clocks use `calendar.csv`.

## Files

| File | What it holds | Row count |
|---|---|---|
| `branches.csv` | 6 branches | 6 data rows |
| `calendar.csv` | Working-day calendar 2026-09-01 .. 2026-12-31 (Sundays, 2nd/4th Saturdays, holidays off) | 122 data rows |
| `customers.csv` | 40 customers with risk rating, PEP flag / PEP link, occupation, expected turnover and KYC expiry | 40 data rows |
| `accounts.csv` | Accounts (some customers hold two) with open date and home branch | 44 data rows |
| `prior_transactions.csv` | Last transactions before 2026-09-01 per account (full 12-month history for the dormant accounts) | 90 data rows |
| `transactions/txn_2026_09_01.csv` | Transactions posted on 2026-09-01 | 7 data rows |
| `transactions/txn_2026_09_02.csv` | Transactions posted on 2026-09-02 | 9 data rows |
| `transactions/txn_2026_09_03.csv` | Transactions posted on 2026-09-03 | 9 data rows |
| `transactions/txn_2026_09_04.csv` | Transactions posted on 2026-09-04 | 10 data rows |
| `transactions/txn_2026_09_05.csv` | Transactions posted on 2026-09-05 | 7 data rows |
| `transactions/txn_2026_09_06.csv` | Transactions posted on 2026-09-06 | 8 data rows |
| `transactions/txn_2026_09_07.csv` | Transactions posted on 2026-09-07 | 8 data rows |
| `transactions/txn_2026_09_08.csv` | Transactions posted on 2026-09-08 | 8 data rows |
| `transactions/txn_2026_09_09.csv` | Transactions posted on 2026-09-09 | 11 data rows |
| `transactions/txn_2026_09_10.csv` | Transactions posted on 2026-09-10 | 8 data rows |
| `transactions/txn_2026_09_11.csv` | Transactions posted on 2026-09-11 | 12 data rows |
| `transactions/txn_2026_09_12.csv` | Transactions posted on 2026-09-12 | 7 data rows |
| `transactions/txn_2026_09_13.csv` | Transactions posted on 2026-09-13 | 8 data rows |
| `transactions/txn_2026_09_14.csv` | Transactions posted on 2026-09-14 | 9 data rows |
| `transactions/txn_2026_09_15.csv` | Transactions posted on 2026-09-15 | 9 data rows |
| `transactions/txn_2026_09_16.csv` | Transactions posted on 2026-09-16 | 9 data rows |
| `transactions/txn_2026_09_17.csv` | Transactions posted on 2026-09-17 | 9 data rows |
| `transactions/txn_2026_09_18.csv` | Transactions posted on 2026-09-18 | 9 data rows |
| `transactions/txn_2026_09_19.csv` | Transactions posted on 2026-09-19 | 9 data rows |
| `transactions/txn_2026_09_20.csv` | Transactions posted on 2026-09-20 | 7 data rows |
| `transactions/txn_2026_09_21.csv` | Transactions posted on 2026-09-21 | 10 data rows |
| `transactions/txn_2026_09_22.csv` | Transactions posted on 2026-09-22 | 7 data rows |
| `transactions/txn_2026_09_23.csv` | Transactions posted on 2026-09-23 | 9 data rows |
| `transactions/txn_2026_09_24.csv` | Transactions posted on 2026-09-24 | 9 data rows |
| `transactions/txn_2026_09_25.csv` | Transactions posted on 2026-09-25 | 9 data rows |
| `transactions/txn_2026_09_26.csv` | Transactions posted on 2026-09-26 | 9 data rows |
| `transactions/txn_2026_09_27.csv` | Transactions posted on 2026-09-27 | 7 data rows |
| `transactions/txn_2026_09_28.csv` | Transactions posted on 2026-09-28 | 8 data rows |
| `transactions/txn_2026_09_29.csv` | Transactions posted on 2026-09-29 | 8 data rows |
| `transactions/txn_2026_09_30.csv` | Transactions posted on 2026-09-30 | 8 data rows |
| `transactions/txn_2026_10_01.csv` | Transactions posted on 2026-10-01 | 10 data rows |
| `transactions/txn_2026_10_02.csv` | Transactions posted on 2026-10-02 | 7 data rows |
| `transactions/txn_2026_10_03.csv` | Transactions posted on 2026-10-03 | 8 data rows |
| `transactions/txn_2026_10_04.csv` | Transactions posted on 2026-10-04 | 7 data rows |
| `transactions/txn_2026_10_05.csv` | Transactions posted on 2026-10-05 | 9 data rows |
| `transactions/txn_2026_10_06.csv` | Transactions posted on 2026-10-06 | 8 data rows |
| `transactions/txn_2026_10_07.csv` | Transactions posted on 2026-10-07 | 9 data rows |
| `transactions/txn_2026_10_08.csv` | Transactions posted on 2026-10-08 | 11 data rows |
| `transactions/txn_2026_10_09.csv` | Transactions posted on 2026-10-09 | 8 data rows |
| `transactions/txn_2026_10_10.csv` | Transactions posted on 2026-10-10 | 8 data rows |
| `transactions/txn_2026_10_11.csv` | Transactions posted on 2026-10-11 | 7 data rows |
| `transactions/txn_2026_10_12.csv` | Transactions posted on 2026-10-12 | 9 data rows |
| `transactions/txn_2026_10_13.csv` | Transactions posted on 2026-10-13 | 9 data rows |
| `transactions/txn_2026_10_14.csv` | Transactions posted on 2026-10-14 | 8 data rows |
| `transactions/txn_2026_10_15.csv` | Transactions posted on 2026-10-15 | 10 data rows |
| `transactions/txn_2026_10_16.csv` | Transactions posted on 2026-10-16 | 7 data rows |
| `transactions/txn_2026_10_17.csv` | Transactions posted on 2026-10-17 | 8 data rows |
| `transactions/txn_2026_10_18.csv` | Transactions posted on 2026-10-18 | 7 data rows |
| `transactions/txn_2026_10_19.csv` | Transactions posted on 2026-10-19 | 9 data rows |
| `transactions/txn_2026_10_20.csv` | Transactions posted on 2026-10-20 | 8 data rows |
| `transactions/txn_2026_10_21.csv` | Transactions posted on 2026-10-21 | 8 data rows |
| `transactions/txn_2026_10_22.csv` | Transactions posted on 2026-10-22 | 10 data rows |
| `transactions/txn_2026_10_23.csv` | Transactions posted on 2026-10-23 | 7 data rows |
| `transactions/txn_2026_10_24.csv` | Transactions posted on 2026-10-24 | 8 data rows |
| `transactions/txn_2026_10_25.csv` | Transactions posted on 2026-10-25 | 8 data rows |
| `transactions/txn_2026_10_26.csv` | Transactions posted on 2026-10-26 | 7 data rows |
| `transactions/txn_2026_10_27.csv` | Transactions posted on 2026-10-27 | 8 data rows |
| `transactions/txn_2026_10_28.csv` | Transactions posted on 2026-10-28 | 7 data rows |
| `transactions/txn_2026_10_29.csv` | Transactions posted on 2026-10-29 | 8 data rows |
| `transactions/txn_2026_10_30.csv` | Transactions posted on 2026-10-30 | 7 data rows |
| `commands.txt` | Daily RUN_DAY commands, case actions, CTR generation and print requests | 79 command lines (excluding comments) |

Volumes in this sample are reduced for email delivery; the hidden evaluation set is larger and uses the same schema.

Row numbers quoted below are 1-based data-row numbers (the header is row 0). Line numbers for `commands.txt` are physical line numbers including comment lines.

## Column reference

Conventions: dates `YYYY-MM-DD`; timestamps `YYYY-MM-DD HH:MM:SS` (24h, IST, no timezone suffix); money in Rs as plain decimals with 2 places (no commas, no symbol); percentages as plain numbers (12.5 means 12.5%); booleans `true`/`false`; IDs uppercase with a fixed prefix.

### `branches.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| branch_id | string | BR-nn | — | — |
| branch_name | string | — | — | — |
| city | string | — | — | — |

### `calendar.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| date | date | — | — | — |
| day_name | string | Mon..Sun | — | — |
| is_working_day | bool | — | — | SLA clocks count only working days |
| reason | string | — | — | why the day is off; empty on working days |

### `customers.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| customer_id | string | CUST-nnn | — | — |
| name | string | — | — | — |
| gender | enum | — | M, F | — |
| risk_rating | enum | — | LOW, MEDIUM, HIGH | multiplier 0.8 / 1.0 / 1.5 |
| pep_flag | bool | — | — | — |
| pep_linked_customer | string | — | customers.csv | set for listed family members of a PEP; empty otherwise |
| occupation | string | — | — | — |
| expected_monthly_turnover | decimal | Rs | — | ignored for accounts < 90 days old (use 200000) |
| kyc_expiry_date | date | — | — | KYC valid up to and including? — your call, state it |
| mobile | string | 10 digits | — | — |

### `accounts.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| account_id | string | ACC-nnnnn | — | — |
| customer_id | string | — | customers.csv | — |
| account_type | enum | — | SAVINGS, CURRENT | — |
| open_date | date | — | — | account age for the new-account rule |
| home_branch_id | string | — | branches.csv | — |

### `prior_transactions.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| txn_id | string | TXN-nnnnnn (PTX-nnnnn in prior file) | — | unique except the planted duplicate |
| account_id | string | — | accounts.csv | — |
| txn_ts | timestamp | — | — | event time; use this for every window |
| txn_type | enum | — | CASH_DEPOSIT, CASH_WITHDRAWAL, TRANSFER_IN, TRANSFER_OUT, INTEREST_CREDIT | — |
| amount | decimal | Rs | — | > 0 (the 0.00 row is a planted invalid record) |
| channel | enum | — | BRANCH, ATM, NEFT, RTGS, IMPS, UPI, SYSTEM | — |
| branch_id | string | — | branches.csv | cash and branch transactions only |
| counterparty_account | string | IFSC-account | — | transfers only; equality = same counterparty |
| counterparty_name | string | — | — | transfers only |
| narration | string | — | — | free text |

### `transactions/txn_YYYY_MM_DD.csv (all 60 daily files, same columns)`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| txn_id | string | TXN-nnnnnn (PTX-nnnnn in prior file) | — | unique except the planted duplicate |
| account_id | string | — | accounts.csv | — |
| txn_ts | timestamp | — | — | event time; use this for every window |
| txn_type | enum | — | CASH_DEPOSIT, CASH_WITHDRAWAL, TRANSFER_IN, TRANSFER_OUT, INTEREST_CREDIT | — |
| amount | decimal | Rs | — | > 0 (the 0.00 row is a planted invalid record) |
| channel | enum | — | BRANCH, ATM, NEFT, RTGS, IMPS, UPI, SYSTEM | — |
| branch_id | string | — | branches.csv | cash and branch transactions only |
| counterparty_account | string | IFSC-account | — | transfers only; equality = same counterparty |
| counterparty_name | string | — | — | transfers only |
| narration | string | — | — | free text |

## Command file format

`commands.txt` holds one command per line in the form `COMMAND_NAME|arg1|arg2|...`. Commands must be processed strictly in file order. Lines starting with `#` are comments and blank lines are ignored. An empty argument (two pipes in a row) means "not supplied". Every command used in this pack:

| Command | Arguments (in order) | Meaning |
|---|---|---|
| `RUN_DAY` | `date\|file_name` | Load the day's transaction file and run all rules for that date (end-of-day evaluation) |
| `CASE_ACTION` | `customer_id\|action\|action_ts\|note` | Move the customer's open case: START_REVIEW, ESCALATE, CLOSE_NO_ACTION, FILE_STR |
| `GENERATE_CTR` | `month` | Produce the CTR for the month (YYYY-MM); due by the 15th of the following month |
| `PRINT_ALERT_LOG` | `from_date\|to_date` | Print all alerts raised in the range |
| `PRINT_CASES` | `as_of_date` | Print the case register with states and SLA flags |
| `PRINT_STR_REPORT` | `from_date\|to_date` | Print STRs filed in the range |

## Planted scenarios

Every edge case in the brief, mapped to the exact record where it occurs, followed by extra traps.

- **EC-01 Cash deposit of exactly Rs 9,00,000 and Rs 10,00,000**
  - CUST-032: deposits of exactly 9,00,000 and 9,99,999 (both band edges) plus 9,45,000 within 5 days — the 9,00,000 one is inside the band; CUST-009: single cash deposit of exactly 10,00,000 — not 'more than Rs 10 lakh', so no daily CTR on its own — `transactions/txn_2026_09_21.csv TXN-000179; transactions/txn_2026_09_25.csv TXN-000213; transactions/txn_2026_10_06.csv TXN-000300`
- **EC-02 Third structuring deposit at day 7 boundary of the rolling window**
  - CUST-018 (HIGH): cash deposits of 9,40,000 / 9,75,000 / 9,10,000 at BR-01, BR-02, BR-01; the third is at 2026-09-15 11:00:00, exactly 7 x 24 h after the first — decide whether it is inside the rolling 7-day window (score 40 + 20 multi-branch) — `transactions/txn_2026_09_08.csv TXN-000060; transactions/txn_2026_09_11.csv TXN-000092; transactions/txn_2026_09_15.csv TXN-000126`
- **EC-03 Outward transfer at hour 48 exactly after the credit**
  - CUST-007: RTGS credit 5,00,000 at 2026-09-24 14:00:00 and RTGS out 4,00,000 (exactly 80%) at 2026-09-26 14:00:00 — exactly hour 48 (inclusive?)  — `transactions/txn_2026_09_24.csv TXN-000204; transactions/txn_2026_09_26.csv TXN-000220`
- **EC-04 Dormant account with only bank interest credits during the 12 months**
  - CUST-015: last customer-initiated transaction 2025-07-14, then only SB interest credits (2025-09-30 .. 2026-06-30); reactivated with 5,90,000 of credits between 2026-10-08 and 2026-10-19 — do system interest credits break dormancy? Control: CUST-039 has no transactions since 2025-06-02 and receives 5,20,001 within 30 days — `prior_transactions.csv rows for ACC-10018; transactions/txn_2026_10_08.csv TXN-000318; transactions/txn_2026_10_19.csv TXN-000410; control transactions/txn_2026_09_29.csv TXN-000243, transactions/txn_2026_10_12.csv TXN-000353`
- **EC-05 Weighted score exactly 50.0 for a LOW risk customer**
  - CUST-030 (LOW, expected turnover 1,00,000): 5,10,000 credit on 2026-10-13 pushes rolling-30-day credits above 5x -> velocity raw 50 x 0.8 = 40.0; the same rule fires again on 10-14 and 10-15 (new credits each day) and each merge adds +5 after the multiplier, giving exactly 50.0 on 2026-10-15 — alert at the >= 50 threshold — `transactions/txn_2026_10_13.csv TXN-000359; transactions/txn_2026_10_14.csv TXN-000368; transactions/txn_2026_10_15.csv TXN-000380`
- **EC-06 Alert on day 7 after a prior alert of the same rule**
  - CUST-023 (HIGH): structuring set on 2026-09-02/03/04 (alert on 2026-09-04), then three more band deposits all on 2026-09-11 — the same rule fires exactly 7 days after the prior alert (merge into the open case or new alert?) — `transactions/txn_2026_09_02.csv..transactions/txn_2026_09_04.csv TXN-000010, TXN-000019, TXN-000029; transactions/txn_2026_09_11.csv TXN-000086, TXN-000091, TXN-000094`
- **EC-07 PRIORITY case opened on Friday with Saturday a working day in the calendar**
  - CUST-010 (HIGH): 8,00,000 in from SBIN0284514-203817805780 on Wed 2026-09-16 and 7,00,000 (87.5%) back to the same account on Fri 2026-09-18 — (35 + 25) x 1.5 = 90, PRIORITY case opened Friday; calendar.csv marks Sat 2026-09-19 as a working day, so START_REVIEW on Mon 2026-09-21 breaches the 1-working-day SLA — `transactions/txn_2026_09_16.csv TXN-000132; transactions/txn_2026_09_18.csv TXN-000148; calendar.csv 2026-09-19; commands.txt line 29`
- **EC-08 KYC expiring on the transaction date**
  - CUST-013: kyc_expiry_date 2026-10-07 and a 1,50,000 credit on 2026-10-07 16:20 (expired or not on the expiry date?), then 1,25,000 on 2026-10-08 (clearly expired, scores 15) — `customers.csv CUST-013; transactions/txn_2026_10_07.csv TXN-000311; transactions/txn_2026_10_08.csv TXN-000316`
- **Extra traps (not in the brief, but realistic):**
  - CUST-023: after FILE_STR on 2026-09-16 the customer is tagged STR_FILED — its later rapid-movement alert (4,20,000 in, 3,50,000 = 83% out within 29 h) must be PRIORITY regardless of score (6-month tag) — `commands.txt line 22; transactions/txn_2026_10_21.csv TXN-000425; transactions/txn_2026_10_22.csv TXN-000439`
  - CUST-020 (PEP): single 6,00,000 credit alerts on its own (20 + 20 PEP adder) x 1.5 = 60; START_REVIEW on 2026-09-15 is more than 2 working days after (SLA breach). CUST-021 is a listed family member (pep_linked_customer) — PEP rules apply to its 5,50,000 cash deposit — `transactions/txn_2026_09_09.csv TXN-000069; transactions/txn_2026_10_01.csv TXN-000263; commands.txt line 19`
  - CUST-019: account opened 2026-08-10 (< 90 days) — declared turnover 8,00,000 is ignored, Rs 2 lakh used; 10,50,000 credited by 2026-09-21 is > 5x -> score 50 — `accounts.csv ACC-10022; transactions/txn_2026_09_03.csv TXN-000018 .. transactions/txn_2026_09_21.csv TXN-000178`
  - CUST-002: two cash deposits on 2026-09-17 (6,00,000 + 4,50,000 = 10,50,000) — daily CTR although neither is > 10 lakh; CUST-033: five 2,20,000 cash deposits in September (11,00,000) — integrally connected monthly CTR — `transactions/txn_2026_09_17.csv TXN-000142, TXN-000145; transactions/txn_2026_09_04.csv TXN-000032 .. transactions/txn_2026_09_24.csv TXN-000207`
  - CUST-022: credits of exactly 6,00,000 in 30 days against expected 2,00,000 — exactly 3x, which is not '> 3x' (no velocity score) — `transactions/txn_2026_10_01.csv TXN-000260 .. transactions/txn_2026_10_22.csv TXN-000433`
  - CASE_ACTION START_REVIEW for CUST-022, who has no open case — reject the action and log it — `commands.txt line 73`
  - Duplicate transaction row in transactions/txn_2026_09_10.csv: TXN-000084 appears twice with identical fields — count it once — `transactions/txn_2026_09_10.csv rows 7 and 8`
  - Late-posted row: TXN-000289 has txn_ts 2026-10-04 23:58:30 but arrives in the 2026-10-05 file — windows use txn_ts, not the file date — `transactions/txn_2026_10_05.csv TXN-000289`
  - Invalid amount: TXN-000330 is a CASH_WITHDRAWAL of 0.00 — reject it and log it, do not evaluate rules on it — `transactions/txn_2026_10_09.csv TXN-000330`

## What is NOT in this pack

Expected outputs are not provided for this set. Validate your engine with your own test suite against the rules in your brief (BR-01 … BR-nn). A separate hidden input set with the same schema will be used at final evaluation; outputs are compared field-for-field, so follow the column formats above exactly in your own output.

## Output format expected at evaluation

Produce these CSV files (header row, same conventions as above, rows sorted as stated). Where the brief is silent on a format detail the choice below is binding for evaluation.

### `alert_log.csv`

One row per alert (or merge event) in evaluation order; evidence IDs space-separated in chronological order.

Columns, in order: `alert_id`, `eval_date`, `customer_id`, `rule_ids`, `raw_score`, `pep_kyc_adders`, `risk_multiplier`, `merge_bonus`, `weighted_score`, `priority`, `case_id`, `action`, `evidence_txn_ids`

### `case_register.csv`

One row per case as of the PRINT_CASES date.

Columns, in order: `case_id`, `customer_id`, `opened_on`, `priority`, `state`, `under_review_on`, `escalated_on`, `closed_on`, `str_filed_on`, `sla_breaches`, `alert_ids`

### `ctr_2026_09.csv`

One row per account and reason.

Columns, in order: `account_id`, `customer_id`, `ctr_type`, `txn_date_or_month`, `total_cash`, `txn_ids`, `due_date`

### `str_report.csv`

One row per STR filed.

Columns, in order: `str_id`, `case_id`, `customer_id`, `escalated_on`, `filed_on`, `within_sla`, `total_amount`, `evidence_txn_ids`

Binding choices: alert_id ALT-nnnnn and case_id CASE-nnnn are sequential in creation order; `action` is NEW or MERGED; `priority` is true/false; `ctr_type` is DAILY or MONTHLY; `sla_breaches` lists the breached transitions separated by spaces (e.g. `UNDER_REVIEW`), empty if none. Rule ids are your BR-nn numbers. Scores are printed with 1 decimal (e.g. 50.0).
