"""
Tests for Deterministic Eligibility Assessment Engine.
"""

import pytest
from hakkuai.schemas import WorkerProfile, EligibilityStatus, InjurySeverity
from hakkuai.eligibility import assess_worker_eligibility

def test_registered_tamil_nadu_construction_worker_injury():
    """Registered construction worker in Tamil Nadu injured at work."""
    profile = WorkerProfile(
        state="Tamil Nadu",
        occupation="Construction Worker",
        is_construction_worker=True,
        is_bocw_registered=True,
        accident_occurred_at_work=True,
        injury_severity=InjurySeverity.SEVERE,
        hospital_treatment_received=True,
        lost_wages=True
    )
    results = assess_worker_eligibility(profile)
    res_map = {r.scheme_id: r for r in results}

    # Should be Potentially Eligible for TN BOCW
    assert "tn_bocw_accident_relief" in res_map
    assert res_map["tn_bocw_accident_relief"].status == EligibilityStatus.POTENTIALLY_ELIGIBLE
    assert "District Labour Officer" in res_map["tn_bocw_accident_relief"].explanation_en

    # Should be Potentially Eligible for Employees' Compensation Act 1923
    assert "central_employees_compensation_1923" in res_map
    assert res_map["central_employees_compensation_1923"].status == EligibilityStatus.POTENTIALLY_ELIGIBLE

    # Karnataka scheme should NOT be present
    assert "karnataka_bocw_accident_benefit" not in res_map

def test_unregistered_worker_statutory_rights():
    """Unregistered worker should still receive guidance on Employees' Compensation Act."""
    profile = WorkerProfile(
        state="Tamil Nadu",
        is_construction_worker=True,
        is_bocw_registered=False, # Unregistered
        accident_occurred_at_work=True
    )
    results = assess_worker_eligibility(profile)
    res_map = {r.scheme_id: r for r in results}

    # TN BOCW should require registration or alternate handling
    assert "tn_bocw_accident_relief" in res_map
    assert res_map["tn_bocw_accident_relief"].status == EligibilityStatus.MORE_INFORMATION_NEEDED

    # Employees' Compensation Act applies regardless of board registration
    assert "central_employees_compensation_1923" in res_map
    assert res_map["central_employees_compensation_1923"].status == EligibilityStatus.POTENTIALLY_ELIGIBLE

def test_non_construction_worker():
    """Non-construction worker is likely not eligible for BOCW schemes."""
    profile = WorkerProfile(
        state="Tamil Nadu",
        occupation="IT Office Assistant",
        is_construction_worker=False,
        is_bocw_registered=False,
        accident_occurred_at_work=True
    )
    results = assess_worker_eligibility(profile)
    res_map = {r.scheme_id: r for r in results}

    assert "tn_bocw_accident_relief" in res_map
    assert res_map["tn_bocw_accident_relief"].status == EligibilityStatus.LIKELY_NOT_ELIGIBLE

def test_missing_eligibility_information():
    """When crucial fields are absent, engine flags MORE_INFORMATION_NEEDED."""
    profile = WorkerProfile(
        state="Tamil Nadu",
        is_construction_worker=True,
        is_bocw_registered=None, # Missing
        accident_occurred_at_work=None # Missing
    )
    results = assess_worker_eligibility(profile)
    res_map = {r.scheme_id: r for r in results}

    assert res_map["tn_bocw_accident_relief"].status == EligibilityStatus.MORE_INFORMATION_NEEDED
    assert len(res_map["tn_bocw_accident_relief"].missing_information) >= 2

def test_unverified_state_coverage_honest_uncertainty():
    """Worker from state with no local verified schemes (e.g., Nagaland) receives honest UNVERIFIED_DATA."""
    profile = WorkerProfile(
        state="Nagaland",
        is_construction_worker=True,
        is_bocw_registered=True,
        accident_occurred_at_work=True
    )
    results = assess_worker_eligibility(profile)
    unverified = [r for r in results if r.status == EligibilityStatus.UNVERIFIED_DATA]

    assert len(unverified) >= 1, "Must communicate uncertainty for states with incomplete local data"
    assert "Nagaland" in unverified[0].scheme_name
    assert "incomplete" in unverified[0].explanation_en.lower() or "not currently contain" in unverified[0].explanation_en.lower()
    assert unverified[0].verified is False
