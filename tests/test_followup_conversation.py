"""
Regression Tests for HakkuAI Follow-up Conversation Handling.
Verifies intent routing, persistent document state, non-repetitive responses,
context-aware missing document guidance, and explicit reassessment.
"""

import pytest
from hakkuai.conversation import ConversationEngine, SessionManager
from hakkuai.schemas import DocumentStatus, Language

def test_initial_assessment_followed_by_missing_discharge_summary():
    """
    Test that when a worker completes initial assessment and asks:
    'No, I don't have any discharge summary. What should I do?'
    the agent provides direct practical guidance without repeating the entire initial welfare report.
    """
    engine = ConversationEngine(SessionManager())
    sender = "worker_turn_flow_001"

    # Turn 1: Initial assessment
    prompt_1 = "I am a registered construction worker in Tamil Nadu. I fractured my leg at work."
    resp_1 = engine.process_message(sender, prompt_1)

    # Initial assessment must contain greeting and welfare schemes
    assert "Hello! I am HakkuAI" in resp_1.response_text
    assert "Tamil Nadu BOCW Welfare Board" in resp_1.response_text
    assert "Identified Welfare Schemes & Statutory Compensation" in resp_1.response_text

    session = engine.session_manager.get_or_create_session(sender)
    assert session.has_assessed is True

    # Turn 2: Follow-up question about missing discharge summary
    prompt_2 = "No, I don't have any discharge summary. What should I do?"
    resp_2 = engine.process_message(sender, prompt_2)

    # 1. Must NOT repeat the greeting or entire scheme dump
    assert "Hello! I am HakkuAI" not in resp_2.response_text
    assert "Identified Welfare Schemes & Statutory Compensation" not in resp_2.response_text
    assert "Your Recorded Profile Details" not in resp_2.response_text

    # 2. Must state worker is NOT automatically disqualified
    assert "NOT automatically disqualify" in resp_2.response_text

    # 3. Must suggest contacting hospital/clinic records department or doctor
    assert "Hospital" in resp_2.response_text or "clinic" in resp_2.response_text
    assert "Medical Records Department" in resp_2.response_text or "treating doctor" in resp_2.response_text

    # 4. Must explain outpatient / OPD alternatives
    assert "Outpatient" in resp_2.response_text or "OPD" in resp_2.response_text or "Emergency Casualty Card" in resp_2.response_text

    # 5. Must suggest preserving prescriptions, bills, X-rays
    assert "prescriptions" in resp_2.response_text.lower() or "bills" in resp_2.response_text.lower()

    # 6. Must state that required documents depend on the scheme & authority
    assert "relevant authority" in resp_2.response_text.lower() or "authority" in resp_2.response_text.lower()

    # 7. Must update document status to Missing
    assert session.document_statuses.get("doc_hospital_discharge") == DocumentStatus.MISSING
    assert "hospital_discharge" not in session.profile.available_documents

    # 8. Must include single focused follow-up question
    assert "❓ Which hospital or clinic treated you" in resp_2.response_text

def test_missing_document_remains_missing_across_turns():
    """Verify that a document marked missing remains missing in subsequent turns."""
    engine = ConversationEngine(SessionManager())
    sender = "worker_persist_missing_002"

    # Turn 1: Initial statement
    engine.process_message(sender, "I am a construction worker in Tamil Nadu with an injury.")
    session = engine.session_manager.get_or_create_session(sender)

    # Turn 2: State missing discharge summary
    engine.process_message(sender, "I do not have any hospital discharge summary.")
    assert session.document_statuses.get("doc_hospital_discharge") == DocumentStatus.MISSING

    # Turn 3: Unrelated question
    resp_3 = engine.process_message(sender, "Where is the labour office located?")
    # Document must remain missing
    assert session.document_statuses.get("doc_hospital_discharge") == DocumentStatus.MISSING
    assert "hospital_discharge" not in session.profile.available_documents

    # Turn 4: Asking about compensation
    resp_4 = engine.process_message(sender, "Will my employer pay compensation?")
    assert session.document_statuses.get("doc_hospital_discharge") == DocumentStatus.MISSING

def test_document_changes_status_only_after_user_confirmation():
    """Verify that a missing document becomes available ONLY after explicit user confirmation."""
    engine = ConversationEngine(SessionManager())
    sender = "worker_confirm_doc_003"

    # Initial assessment
    engine.process_message(sender, "I work in construction in Tamil Nadu and hurt my hand.")
    session = engine.session_manager.get_or_create_session(sender)

    # User says missing
    engine.process_message(sender, "I don't have any discharge summary.")
    assert session.document_statuses.get("doc_hospital_discharge") == DocumentStatus.MISSING

    # Asking a casual question containing the words 'discharge summary' must NOT make it available
    engine.process_message(sender, "What is a discharge summary?")
    assert session.document_statuses.get("doc_hospital_discharge") == DocumentStatus.MISSING

    # Now user explicitly confirms having obtained it
    engine.process_message(sender, "I went to the hospital and got the discharge summary from the records office.")
    assert session.document_statuses.get("doc_hospital_discharge") == DocumentStatus.AVAILABLE
    assert "hospital_discharge" in session.profile.available_documents

def test_followup_question_does_not_trigger_initial_assessment():
    """Verify follow-up questions do NOT regenerate the full initial report."""
    engine = ConversationEngine(SessionManager())
    sender = "worker_no_repeat_004"

    # Turn 1: Initial assessment
    resp_1 = engine.process_message(sender, "I am a registered construction worker in Tamil Nadu with a fracture.")
    assert "Identified Welfare Schemes & Statutory Compensation" in resp_1.response_text

    # Turn 2: Application steps question
    resp_2 = engine.process_message(sender, "How do I apply and where do I go?")
    assert "Identified Welfare Schemes & Statutory Compensation" not in resp_2.response_text
    assert "Hello! I am HakkuAI" not in resp_2.response_text
    assert "District Labour Office" in resp_2.response_text

    # Turn 3: Eligibility question
    resp_3 = engine.process_message(sender, "How much compensation will I get?")
    assert "Identified Welfare Schemes & Statutory Compensation" not in resp_3.response_text
    assert "Hello! I am HakkuAI" not in resp_3.response_text
    assert "Benefit & Compensation Limits" in resp_3.response_text or "கட்டுமான நல வாரிய" in resp_3.response_text

def test_explicit_request_to_repeat_or_refresh_assessment():
    """Verify explicit request for reassessment re-displays the full initial report."""
    engine = ConversationEngine(SessionManager())
    sender = "worker_refresh_005"

    # Turn 1: Initial assessment
    engine.process_message(sender, "I work in construction in Tamil Nadu and got injured at work.")

    # Turn 2: Follow-up
    engine.process_message(sender, "I do not have a discharge summary.")

    # Turn 3: Explicit reassessment request
    resp_3 = engine.process_message(sender, "Please show assessment again with all schemes")

    # Should re-display full assessment report with updated status
    assert "Identified Welfare Schemes & Statutory Compensation" in resp_3.response_text
    assert "Tamil Nadu BOCW" in resp_3.response_text
    assert "Your Recorded Profile Details" in resp_3.response_text

def test_correct_document_counts_derived_from_checklist_state():
    """Verify checklist counts are dynamically derived from actual document statuses."""
    engine = ConversationEngine(SessionManager())
    sender = "worker_counts_006"

    # Turn 1: Initial with 2 confirmed documents
    resp_1 = engine.process_message(sender, "I have my Aadhaar card and bank passbook. I work in construction in Tamil Nadu.")
    checklist_1 = resp_1.checklist
    avail_1 = sum(1 for i in checklist_1.items if i.status == DocumentStatus.AVAILABLE)
    assert avail_1 >= 2
    assert "doc_identity_aadhaar" in [i.document_id for i in checklist_1.items if i.status == DocumentStatus.AVAILABLE]
    assert "doc_bank_passbook" in [i.document_id for i in checklist_1.items if i.status == DocumentStatus.AVAILABLE]

    # Turn 2: Explicitly state missing discharge summary
    resp_2 = engine.process_message(sender, "No, I don't have any discharge summary.")
    checklist_2 = resp_2.checklist
    missing_2 = sum(1 for i in checklist_2.items if i.status == DocumentStatus.MISSING)
    assert missing_2 >= 1
    discharge_item = next(i for i in checklist_2.items if i.document_id == "doc_hospital_discharge")
    assert discharge_item.status == DocumentStatus.MISSING

def test_session_isolation_in_followup_and_document_state():
    """Ensure two workers' follow-up document states remain completely independent."""
    engine = ConversationEngine(SessionManager())
    worker_1 = "worker_iso_alpha"
    worker_2 = "worker_iso_beta"

    # Worker 1 states missing discharge summary
    engine.process_message(worker_1, "I work in construction in Tamil Nadu. I broke my leg.")
    engine.process_message(worker_1, "I don't have any discharge summary.")

    # Worker 2 confirms having discharge summary
    engine.process_message(worker_2, "I work in construction in Karnataka. I got my discharge summary.")

    session_1 = engine.session_manager.get_or_create_session(worker_1)
    session_2 = engine.session_manager.get_or_create_session(worker_2)

    assert session_1.document_statuses.get("doc_hospital_discharge") == DocumentStatus.MISSING
    assert session_2.document_statuses.get("doc_hospital_discharge") == DocumentStatus.AVAILABLE

    assert "hospital_discharge" not in session_1.profile.available_documents
    assert "hospital_discharge" in session_2.profile.available_documents

def test_exact_4_step_user_sequence():
    """
    Directly tests the sequence requested:
    - Turn 1: 'I am a construction worker in Tamil Nadu. I fractured my leg at work and cannot earn. I am registered with the welfare board.'
    - Turn 2: 'No, I don't have any discharge summary. What should I do?'
    - Turn 3: 'What alternative documents can I provide?'
    - Turn 4: 'What should I do next?'
    """
    engine = ConversationEngine(SessionManager())
    sender = "worker_4_step_user_sequence"

    # Turn 1: Initial Assessment
    r1 = engine.process_message(
        sender,
        "I am a construction worker in Tamil Nadu. I fractured my leg at work and cannot earn. I am registered with the welfare board."
    )
    assert "Hello! I am HakkuAI" in r1.response_text
    assert "Identified Welfare Schemes & Statutory Compensation" in r1.response_text
    s1 = engine.session_manager.get_or_create_session(sender)
    assert s1.has_assessed is True
    assert s1.profile.state == "Tamil Nadu"
    assert s1.profile.is_construction_worker is True
    assert s1.profile.is_bocw_registered is True

    # Turn 2: Follow-up on missing discharge summary
    r2 = engine.process_message(
        sender,
        "No, I don't have any discharge summary. What should I do?"
    )
    assert "Hello! I am HakkuAI" not in r2.response_text
    assert "Identified Welfare Schemes & Statutory Compensation" not in r2.response_text
    assert "NOT automatically disqualify" in r2.response_text
    assert "Medical Records Department" in r2.response_text or "hospital" in r2.response_text.lower()
    assert s1.document_statuses.get("doc_hospital_discharge") == DocumentStatus.MISSING
    assert "hospital_discharge" not in s1.profile.available_documents

    # Turn 3: Follow-up on alternative documents
    r3 = engine.process_message(
        sender,
        "What alternative documents can I provide?"
    )
    assert "Hello! I am HakkuAI" not in r3.response_text
    assert "Identified Welfare Schemes & Statutory Compensation" not in r3.response_text
    assert "Medical Alternatives" in r3.response_text or "Emergency Casualty Card" in r3.response_text
    assert "BOCW" in r3.response_text
    assert "Employment & Accident Proof Alternatives" in r3.response_text or "Affidavit" in r3.response_text
    # Document status remains Missing across subsequent turns
    assert s1.document_statuses.get("doc_hospital_discharge") == DocumentStatus.MISSING
    assert "hospital_discharge" not in s1.profile.available_documents

    # Turn 4: Follow-up on next application actions
    r4 = engine.process_message(
        sender,
        "What should I do next?"
    )
    assert "Hello! I am HakkuAI" not in r4.response_text
    assert "Identified Welfare Schemes & Statutory Compensation" not in r4.response_text
    assert "District Labour Office" in r4.response_text
    assert "Written Notice of Accident to Employer" in r4.response_text
    # Document status still strictly preserved as Missing
    assert s1.document_statuses.get("doc_hospital_discharge") == DocumentStatus.MISSING
    assert "hospital_discharge" not in s1.profile.available_documents
