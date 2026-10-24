"""
Tests for Conversational Engine and Session Management.
"""

import pytest
from hakkuai.conversation import ConversationEngine, SessionManager
from hakkuai.schemas import Language

def test_language_detection():
    """Verify language detection for Tamil and English."""
    engine = ConversationEngine()
    assert engine.detect_language("I am a construction worker in Chennai") == Language.EN
    assert engine.detect_language("நான் சென்னையில் ஒரு கட்டுமானத் தொழிலாளி") == Language.TA
    assert engine.detect_language("Help me in Tamil please") == Language.TA

def test_progressive_intake():
    """Verify progressive attribute extraction without forcing all answers at once."""
    engine = ConversationEngine(SessionManager())
    sender = "test_worker_progressive"

    # Turn 1: State and occupation
    resp1 = engine.process_message(sender, "I work in construction in Tamil Nadu")
    assert resp1.response_text
    session = engine.session_manager.get_or_create_session(sender)
    assert session.profile.state == "Tamil Nadu"
    assert session.profile.is_construction_worker is True
    assert session.profile.is_bocw_registered is None # Still not asked/answered

    # Turn 2: Injury and registration status
    resp2 = engine.process_message(sender, "I fell and fractured my leg at the site. I am not registered with the board.")
    assert session.profile.accident_occurred_at_work is True
    assert session.profile.is_bocw_registered is False

    # Turn 3: Documents
    resp3 = engine.process_message(sender, "I have my Aadhaar and bank passbook with me")
    assert "aadhaar" in session.profile.available_documents
    assert "bank_passbook" in session.profile.available_documents

def test_session_isolation_between_workers():
    """Ensure two workers' sessions remain completely isolated."""
    engine = ConversationEngine(SessionManager())

    worker_a = "worker_tamil_nadu_address_001"
    worker_b = "worker_karnataka_address_002"

    engine.process_message(worker_a, "I am a registered construction worker in Tamil Nadu")
    engine.process_message(worker_b, "I am an unregistered painter in Karnataka")

    session_a = engine.session_manager.get_or_create_session(worker_a)
    session_b = engine.session_manager.get_or_create_session(worker_b)

    assert session_a.profile.state == "Tamil Nadu"
    assert session_a.profile.is_bocw_registered is True

    assert session_b.profile.state == "Karnataka"
    assert session_b.profile.is_bocw_registered is False

    # Ensure worker A's details did not leak to worker B
    assert session_b.profile.state != session_a.profile.state
    assert session_b.profile.is_bocw_registered != session_a.profile.is_bocw_registered

def test_tamil_conversational_response():
    """Verify Tamil response formatting and greetings."""
    engine = ConversationEngine(SessionManager())
    sender = "tamil_worker_test"

    resp = engine.process_message(sender, "வணக்கம், நான் தமிழ்நாட்டில் கட்டுமான வேலை செய்கிறேன். எனக்கு விபத்து ஏற்பட்டது.")
    assert resp.language == Language.TA
    assert "வணக்கம்" in resp.response_text
    assert "தமிழ்நாடு" in resp.response_text
