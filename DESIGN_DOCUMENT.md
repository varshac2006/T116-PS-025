# AML Transaction Monitoring System
## Design Document — PS-025

**Team ID:** T116  
**Team Members:** Varsha C, Varsha R  
**Section:** ISE D  
**Domain:** Banking, Financial Services and Insurance (BFSI)  
**Technology:** Python 3.10+  
**Project Type:** Command-file-driven transaction monitoring system

---

## 1. Executive Summary

The AML Transaction Monitoring System is a Python-based application designed to analyse banking transactions and identify patterns that may require further review.

The system processes customer, account, branch, calendar and transaction data. It validates transaction records, evaluates configured monitoring rules, calculates risk scores, generates alerts, manages investigation cases and produces compliance-related reports.

The application follows a modular, command-driven architecture. It does not require a graphical user interface.

The implementation is intended for the PS-025 academic assignment and uses sample data. It is not a replacement for a bank's production compliance system or professional regulatory review.

## 2. Project Objectives

The main objectives are:

- Validate customer account and transaction information.
- Identify suspicious transaction patterns using defined business rules.
- Calculate weighted risk scores.
- Generate and manage customer alerts.
- Support investigation case workflows.
- Track review and filing deadlines using a working-day calendar.
- Generate alert, case, CTR and STR reports.
- Test business rules, validation and system integration.

## 3. System Architecture

The application is divided into modules so that each component has a specific responsibility.

```text
             Input CSV Files
                   |
                   v
              Data Loader
                   |
                   v
         Transaction Validation
                   |
                   v
          Transaction Processor
                   |
                   v
              Rules Engine
                   |
                   v
              Alert Manager
                   |
                   v
              Case Manager
                   |
                   v
            Report Generator
                   |
                   v
             Output CSV Files
```

### 3.1 Module Responsibilities

| Module | Responsibility |
|---|---|
| `main.py` | Starts the application and displays the execution summary |
| `data_loader.py` | Loads input CSV files and command instructions |
| `transaction_processor.py` | Validates and processes transaction records |
| `rules_engine.py` | Evaluates transaction monitoring rules |
| `alert_manager.py` | Calculates risk scores and prepares alert records |
| `case_manager.py` | Manages case states, actions and SLA tracking |
| `command_processor.py` | Coordinates the complete command-driven workflow |
| `report_generator.py` | Generates the required CSV reports |

## 4. Input Data

The system uses structured CSV files.

The input data includes:

- Customer details and risk ratings
- Account information
- Branch information
- Working-day calendar
- Historical transactions
- Daily transaction files
- Command instructions

The transaction records contain fields such as transaction ID, account ID, timestamp, transaction type, amount and channel.

## 5. Transaction Validation

Before rule evaluation, transaction records are checked for validity.

The validation process includes:

- Required field checks
- Account ID validation
- Transaction ID duplicate checks
- Timestamp format validation
- Transaction type validation
- Channel validation
- Positive and finite transaction amount checks
- Optional branch ID validation when a branch ID is supplied

Invalid records are recorded separately from valid transactions. Duplicate transaction IDs are prevented from being processed again.

## 6. Business Rules

The rules engine evaluates transaction activity using the configured business rules.

### Business Rules

| Rule ID | Business Rule | Description |
|---|---|---|
| BR-01 | Daily Cash Transaction Reporting | Identifies cash transactions exceeding the configured daily reporting threshold of ₹10,00,000. |
| BR-02 | Monthly Cash Transaction Reporting | Identifies customers whose monthly cash transaction total exceeds ₹10,00,000. |
| BR-03 | Structuring Detection | Detects 3 or more deposits between ₹9,00,000 and ₹9,99,999 within a rolling 7-day period. Additional scoring applies when multiple branches are involved. |
| BR-04 | Transaction Velocity | Identifies unusually high incoming transaction activity compared with the customer's historical turnover. |
| BR-05 | Rapid Movement of Funds | Detects incoming funds above INR2,00,000 followed by movement of at least 80% of the amount within 48 hours. |
| BR-06 | Round-Tripping Detection | Identifies suspicious circular movement of funds involving the same counterparty. |
| BR-07 | Dormant Account Reactivation | Flags previously inactive accounts that show significant transaction activity after 365 days of dormancy. |
| BR-08 | PEP Monitoring | Applies additional monitoring to transactions above ₹5,00,000 involving Politically Exposed Persons (PEPs). |
| BR-09 | KYC Expiry Monitoring | Flags transactions above ₹1,00,000 involving customers with expired KYC status. |
| BR-10 | Customer Risk Multipliers | Applies risk multipliers based on customer risk rating: LOW = 0.8, MEDIUM = 1.0, HIGH = 1.5. |
| BR-11 | Alert and Priority Thresholds | Generates an alert when the final risk score reaches 50 and marks it as priority when the score reaches 70. |
| BR-12 | Alert Merging Bonus | Applies an additional score when multiple suspicious findings are merged into a single alert, subject to a maximum bonus of 20 points. |

*Note: Thresholds and scoring values describe this project's implemented monitoring configuration. They should not be interpreted as universal regulatory requirements.*

### 6.1 Important Rule Parameters

### 6.1 Important Rule Parameters

The implementation uses the following configured conditions:

- Daily and monthly cash transaction reporting threshold: more than ₹10,00,000.
- Structuring: at least three cash deposits in the ₹9,00,000 to ₹9,99,999 range within a rolling seven-day window.
- Velocity: incoming credits are compared against expected monthly turnover over a rolling 30-day window.
- Rapid movement: qualifying incoming credits above ₹2,00,000 are checked for at least 80% outgoing movement within 48 hours.
- Dormant account activity: checks a 365-day inactive period followed by qualifying recent activity.
- PEP monitoring: checks qualifying transactions above ₹5,00,000.
- Expired KYC: checks qualifying credits above ₹1,00,000 after the KYC expiry date.

## 7. Risk Scoring and Alert Generation

The alert manager combines rule scores and customer risk information to calculate a weighted score.

The scoring sequence is:

1. Calculate the raw rule score.
2. Add applicable PEP or KYC score adjustments.
3. Apply the customer risk multiplier.
4. Add the applicable alert merge bonus.
5. Evaluate the final weighted score against the alert thresholds.

### 7.1 Customer Risk Multipliers

| Customer Risk | Multiplier |
|---|---:|
| LOW | 0.8 |
| MEDIUM | 1.0 |
| HIGH | 1.5 |

### 7.2 Alert Thresholds

| Weighted Score | Classification |
|---|---|
| Below 50 | No normal alert |
| 50 to below 70 | Alert |
| 70 or above | Priority alert |

The implementation also includes alert merging and suppression logic to reduce repeated alert generation for qualifying findings.

The system maintains evidence transaction IDs to support review of generated alerts.

## 8. Case Management

When an alert requires investigation, the case manager supports the case lifecycle.

```text
OPEN
  |
  v
UNDER_REVIEW
  |
  v
ESCALATED
  |
  v
STR_FILED
```

A case may also be closed with no further action when the permitted workflow conditions are satisfied.

### 8.1 Case Management Features

- Sequential case identification
- Customer-based active case management
- Alert association with cases
- Validation of permitted case actions
- Tracking of review and escalation dates
- Working-day SLA calculations
- Recording of SLA breaches
- Prevention of invalid transitions after STR filing

### 8.2 SLA Tracking

The configured workflow uses:

| Activity | SLA |
|---|---|
| Normal-priority review | 2 working days |
| Priority review | 1 working day |
| STR filing after escalation | 7 working days |

Working-day calculations use the supplied calendar rather than assuming every weekday is a working day.

## 9. Reports Generated

The system generates the following CSV reports:

| Report | Purpose |
|---|---|
| `alert_log.csv` | Records generated alerts, scoring details and evidence |
| `case_register.csv` | Records investigation cases, states and SLA information |
| `ctr_YYYY_MM.csv` | Records applicable cash transaction reporting findings |
| `str_report.csv` | Records suspicious transaction reporting information |

The report generator uses defined column orders to maintain consistent output formats.

## 10. Testing and Validation

The project includes automated unit tests and integration tests.

The test suite covers:

- Customer and transaction processing
- Transaction validation
- Duplicate record handling
- Business rule evaluation
- Risk score calculation
- Alert generation
- Case lifecycle transitions
- SLA calculations
- Report schemas and generated records
- Complete command-driven execution
- Selected boundary and edge cases

### Test Execution

Run the following command from the project root:

```powershell
python -m unittest discover -s tests -v
```

**Latest recorded result:** 28 tests passed.

The integration test also checks expected processing counts and the generated report files for the current project dataset.

## 11. Design Decisions

The main design decisions include:

- Python was selected for its readability and standard-library support.
- CSV files were used for structured input and output.
- The application was divided into independent modules.
- Command-file execution was used instead of a graphical interface.
- Validation is performed before transaction rule evaluation.
- A working-day calendar is used for SLA calculations.
- Automated tests are used to check business rules and system behaviour.
- Reports use consistent column names and ordering.

Further implementation details and rationale are recorded in `decision_log.md`.

## 12. Limitations and Future Enhancements

Possible future enhancements include:

- Additional integration tests for repeated execution and report date filtering.
- More comprehensive boundary testing for SLA deadlines.
- Additional monitoring rules if required by the assignment.
- Improved report presentation.
- Sanctions name screening and transaction network analysis as optional extensions, subject to assignment scope.

## 13. Conclusion

The AML Transaction Monitoring System demonstrates a modular approach to transaction validation, rule-based monitoring, risk scoring, alert management, case workflows and report generation.

The project combines business-rule implementation with automated testing to provide a structured academic demonstration of an AML monitoring workflow.

---

**Team T116**  
Atria Institute of Technology  
PS-025 — AML Transaction Monitoring