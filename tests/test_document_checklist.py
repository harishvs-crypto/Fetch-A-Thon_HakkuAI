"""
Tests for Document Checklist Generator.
"""

import pytest
from hakkuai.schemas import WorkerProfile, DocumentStatus, Language
from hakkuai.document_checklist import generate_document_checklist

def test_document_checklist_generation():
    """Verify document items are generated with alternatives."""
    profile = WorkerProfile(
        state="Tamil Nadu",
        available_documents=["aadhaar", "bank_passbook"]
    )
    checklist = generate_document_checklist(profile, language=Language.EN)

    assert len(checklist.items) >= 5
    doc_map = {item.document_id: item for item in checklist.items}

    # Aadhaar should be Available
    assert doc_map["doc_identity_aadhaar"].status == DocumentStatus.AVAILABLE

    # Bank passbook should be Available
    assert doc_map["doc_bank_passbook"].status == DocumentStatus.AVAILABLE

    # Hospital discharge should be marked Missing
    assert doc_map["doc_hospital_discharge"].status == DocumentStatus.MISSING
    assert doc_map["doc_hospital_discharge"].alternative_evidence_en, "Must provide fallback alternative"

def test_missing_document_alternatives():
    """Verify that every missing document has actionable alternative evidence."""
    profile = WorkerProfile(available_documents=[])
    checklist = generate_document_checklist(profile, language=Language.EN)

    for item in checklist.items:
        assert item.alternative_evidence_en, f"Document {item.name_en} must have alternative evidence instructions"
        assert item.purpose_en, f"Document {item.name_en} must state why it may be needed"

def test_tamil_document_checklist():
    """Verify Tamil summary and field generation."""
    profile = WorkerProfile(state="Tamil Nadu", available_documents=["aadhaar"])
    checklist = generate_document_checklist(profile, language=Language.TA)

    assert "ஆவணங்கள்" in checklist.summary_ta
    for item in checklist.items:
        assert item.name_ta, "Tamil document name must not be empty"
        assert item.purpose_ta, "Tamil document purpose must not be empty"
