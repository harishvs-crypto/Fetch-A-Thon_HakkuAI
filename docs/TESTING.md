# HakkuAI Testing & Verification Guide

This document describes the automated test architecture, coverage metrics, and execution instructions for the HakkuAI project.

---

## 1. Running the Automated Test Suite

HakkuAI includes a comprehensive, 100% passing automated test suite with **28 automated tests** covering all modules.

To execute the test suite:

```bash
# Run all tests with verbose output
python -m pytest tests/ -v

# Run with test coverage (if pytest-cov is installed)
python -m pytest tests/ -v --tb=short
```

### Test Suite Execution Output
```
tests/test_conversation.py::test_language_detection PASSED               [  3%]
tests/test_conversation.py::test_progressive_intake PASSED               [  7%]
tests/test_conversation.py::test_session_isolation_between_workers PASSED [ 10%]
tests/test_conversation.py::test_tamil_conversational_response PASSED    [ 14%]
tests/test_document_checklist.py::test_document_checklist_generation PASSED [ 17%]
tests/test_document_checklist.py::test_missing_document_alternatives PASSED [ 21%]
tests/test_document_checklist.py::test_tamil_document_checklist PASSED   [ 25%]
tests/test_eligibility.py::test_registered_tamil_nadu_construction_worker_injury PASSED [ 28%]
tests/test_eligibility.py::test_unregistered_worker_statutory_rights PASSED [ 32%]
tests/test_eligibility.py::test_non_construction_worker PASSED           [ 35%]
tests/test_eligibility.py::test_missing_eligibility_information PASSED   [ 39%]
tests/test_eligibility.py::test_unverified_state_coverage_honest_uncertainty PASSED [ 42%]
tests/test_injury_workflow.py::test_emergency_medical_prioritization PASSED [ 46%]
tests/test_injury_workflow.py::test_emergency_detection_from_tamil_keywords PASSED [ 50%]
tests/test_injury_workflow.py::test_non_emergency_workflow PASSED        [ 53%]
tests/test_injury_workflow.py::test_records_preservation_guidance PASSED [ 57%]
tests/test_injury_workflow.py::test_unregistered_worker_guidance PASSED  [ 60%]
tests/test_protocol.py::test_acp_chat_message_flow PASSED                [ 64%]
tests/test_protocol.py::test_structured_welfare_rpc_flow PASSED          [ 67%]
tests/test_protocol.py::test_e2e_scenario_1_registered_worker_with_injury PASSED [ 71%]
tests/test_protocol.py::test_e2e_scenario_2_unregistered_worker_injury_assistance PASSED [ 75%]
tests/test_protocol.py::test_e2e_scenario_3_incomplete_state_database_honest_uncertainty PASSED [ 78%]
tests/test_schemes.py::test_scheme_database_loading PASSED               [ 82%]
tests/test_schemes.py::test_state_specific_scheme_filtering PASSED       [ 85%]
tests/test_schemes.py::test_karnataka_specific_scheme_filtering PASSED   [ 89%]
tests/test_schemes.py::test_national_schemes_only PASSED                 [ 92%]
tests/test_schemes.py::test_has_state_specific_coverage PASSED           [ 96%]
tests/test_schemes.py::test_official_government_domain_validation PASSED [100%]

============================= 28 passed in 2.13s ==============================
```

---

## 2. Test Architecture Breakdown

| Test File | Focus Areas | Key Assertions |
|---|---|---|
| `test_schemes.py` | Knowledge Base & Domain Validation | Verifies verified schemes load, ensures state filtering (TN vs Karnataka), validates official `.gov.in` domain security |
| `test_eligibility.py` | Deterministic Rules Engine | Validates state matching, occupation filtering, missing info detection, and honest uncertainty for unindexed states |
| `test_injury_workflow.py` | Medical Emergency & Next Steps | Emergency 112/108 prioritization, evidence preservation lists, and unregistered worker legal remedies |
| `test_document_checklist.py` | Personalized Checklist | Mappings of available vs missing documents, fallback evidence for each missing item, bilingual generation |
| `test_conversation.py` | Progressive Intake & Privacy | Tamil vs English language detection, progressive profile extraction, session isolation between senders |
| `test_protocol.py` | ACP & Hackathon E2E Scenarios | Full `ChatMessage` / `ChatAcknowledgement` lifecycle, structured RPC models, and 3 mandatory E2E scenarios |

---

## 3. Mandatory Demonstration Scenarios Walkthrough

### Scenario 1: Registered Construction Worker with Workplace Injury
- **File**: `tests/test_protocol.py::test_e2e_scenario_1_registered_worker_with_injury`
- **Input**: *"I am a registered construction worker in Tamil Nadu. I broke my leg at the construction site."*
- **Verification**:
  - `profile.state == "Tamil Nadu"`
  - `profile.is_bocw_registered == True`
  - Evaluates `tn_bocw_accident_relief` as `POTENTIALLY_ELIGIBLE`.
  - Evaluates `central_employees_compensation_1923` as `POTENTIALLY_ELIGIBLE`.
  - Generates personalized document checklist including TNBOCW Membership Card, Hospital Discharge Summary, and Bank Passbook.
  - Suggests visiting District Labour Officer (Social Security).

### Scenario 2: Unregistered Worker / Contractor Refusal
- **File**: `tests/test_protocol.py::test_e2e_scenario_2_unregistered_worker_injury_assistance`
- **Input**: *"I work in construction in Tamil Nadu and got injured at work. My contractor never registered me with any welfare board."*
- **Verification**:
  - `profile.is_bocw_registered == False`
  - Correctly flags direct board claim as `MORE_INFORMATION_NEEDED`.
  - Immediately activates Central statutory liability under `central_employees_compensation_1923` (`POTENTIALLY_ELIGIBLE`).
  - Output provides specific guidance: employer's statutory duty to pay, filing Form F before the Commissioner for Employees' Compensation, and using alternative evidence (muster roll, co-worker affidavits).

### Scenario 3: Incomplete Local Database & Honest Uncertainty
- **File**: `tests/test_protocol.py::test_e2e_scenario_3_incomplete_state_database_honest_uncertainty`
- **Input**: *"I am a construction worker in Nagaland. I was hurt in a site accident."*
- **Verification**:
  - `profile.state == "Nagaland"`
  - Flags local state scheme as `UNVERIFIED_DATA`.
  - Explicitly informs the user: *"HakkuAI's local verified database does not currently contain verified state-specific benefit schedules for Nagaland. We do NOT fabricate benefit amounts."*
  - Refuses to guess fake compensation figures.
  - Evaluates universal national schemes (Employees' Compensation Act 1923).
  - Directs worker to the official Nagaland Labour Commissioner Office.

---

## 4. Interactive CLI Mode

To test HakkuAI interactively in the terminal:

```bash
python src/hakkuai/agent.py --cli
```

Type conversational questions in English or Tamil, simulate worker profiles, and inspect generated checklists in real-time.
