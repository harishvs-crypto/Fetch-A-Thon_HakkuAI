"""
Tests for Injury Assistance Workflow.
"""

import pytest
from hakkuai.schemas import WorkerProfile, InjurySeverity
from hakkuai.injury_workflow import evaluate_injury_workflow

def test_emergency_medical_prioritization():
    """Verify that critical injury triggers emergency numbers 112 & 108."""
    profile = WorkerProfile(injury_severity=InjurySeverity.CRITICAL_LIFE_THREATENING)
    result = evaluate_injury_workflow(profile, raw_user_text="He is unconscious and bleeding heavily")

    assert result.is_emergency is True
    assert "112" in result.emergency_message_en
    assert "108" in result.emergency_message_en
    assert "112" in result.emergency_message_ta

def test_emergency_detection_from_tamil_keywords():
    """Verify emergency detection from Tamil phrases."""
    profile = WorkerProfile()
    result = evaluate_injury_workflow(profile, raw_user_text="உயிருக்கு ஆபத்து, அதிக ரத்தம் வெளியேறுகிறது")

    assert result.is_emergency is True
    assert "112" in result.emergency_message_ta

def test_non_emergency_workflow():
    """Regular injury should not trigger emergency alert."""
    profile = WorkerProfile(injury_severity=InjurySeverity.MINOR)
    result = evaluate_injury_workflow(profile, raw_user_text="I hurt my leg last week and have a fracture")

    assert result.is_emergency is False
    assert len(result.records_to_preserve_en) >= 4
    assert len(result.next_steps_en) >= 3

def test_records_preservation_guidance():
    """Verify evidence preservation advice is clear and comprehensive."""
    profile = WorkerProfile(accident_occurred_at_work=True)
    result = evaluate_injury_workflow(profile)

    records_text = " ".join(result.records_to_preserve_en).lower()
    assert "medical records" in records_text or "discharge summary" in records_text
    assert "bills" in records_text or "pharmacy" in records_text
    assert "muster roll" in records_text or "co-worker" in records_text or "supervisor" in records_text

def test_unregistered_worker_guidance():
    """Verify legal protections under Employees' Compensation Act 1923 are highlighted."""
    profile = WorkerProfile(is_bocw_registered=False)
    result = evaluate_injury_workflow(profile)

    assert "Employees' Compensation Act 1923" in result.unregistered_worker_guidance_en
    assert "பணியாளர் இழப்பீட்டுச் சட்டம் 1923" in result.unregistered_worker_guidance_ta
