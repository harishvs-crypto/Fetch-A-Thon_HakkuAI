"""
Tests for Scheme Database and Official Sources Management.
"""

import pytest
from hakkuai.scheme_database import SchemeDatabase, scheme_db
from hakkuai.sources import SourceManager

def test_scheme_database_loading():
    """Verify schemes load properly and contain required verified fields."""
    schemes = scheme_db.get_all_schemes()
    assert len(schemes) >= 6, "Expected at least 6 verified welfare schemes in database"

    for scheme in schemes:
        assert scheme.scheme_id, "Scheme must have non-empty ID"
        assert scheme.name, "Scheme must have English name"
        assert scheme.tamil_name, "Scheme must have Tamil translation"
        assert scheme.official_source_url.startswith("http"), "Must have valid official URL"
        assert scheme.source_verification_date, "Must have source verification date"
        assert scheme.benefit_limits, "Must specify verified benefit limits"

def test_state_specific_scheme_filtering():
    """Verify that Tamil Nadu query only returns Tamil Nadu and National schemes, NOT Karnataka."""
    tn_schemes = scheme_db.query_schemes(state="Tamil Nadu", include_national=True)
    scheme_ids = [s.scheme_id for s in tn_schemes]

    assert "tn_bocw_accident_relief" in scheme_ids
    assert "central_employees_compensation_1923" in scheme_ids
    assert "karnataka_bocw_accident_benefit" not in scheme_ids, (
        "Tamil Nadu query must never include Karnataka-specific schemes"
    )

def test_karnataka_specific_scheme_filtering():
    """Verify that Karnataka query only returns Karnataka and National schemes, NOT Tamil Nadu."""
    ka_schemes = scheme_db.query_schemes(state="Karnataka", include_national=True)
    scheme_ids = [s.scheme_id for s in ka_schemes]

    assert "karnataka_bocw_accident_benefit" in scheme_ids
    assert "tn_bocw_accident_relief" not in scheme_ids, (
        "Karnataka query must never include Tamil Nadu-specific schemes"
    )

def test_national_schemes_only():
    """Verify querying with no state returns only national schemes."""
    nat_schemes = scheme_db.query_schemes(state=None, include_national=True)
    for s in nat_schemes:
        assert s.state_or_national.lower() == "national"

def test_has_state_specific_coverage():
    """Check states with verified coverage vs unverified states."""
    assert scheme_db.has_state_specific_coverage("Tamil Nadu") is True
    assert scheme_db.has_state_specific_coverage("Karnataka") is True
    assert scheme_db.has_state_specific_coverage("Nagaland") is False
    assert scheme_db.has_state_specific_coverage("Sikkim") is False

def test_official_government_domain_validation():
    """Verify trusted government domain matching logic."""
    assert SourceManager.is_official_gov_domain("https://tnuwwb.tn.gov.in/portal") is True
    assert SourceManager.is_official_gov_domain("https://labour.gov.in/schemes") is True
    assert SourceManager.is_official_gov_domain("https://pmjay.gov.in/") is True
    assert SourceManager.is_official_gov_domain("https://indiacode.nic.in/handle/1234") is True
    assert SourceManager.is_official_gov_domain("https://unverified-private-blog.com/welfare") is False
    assert SourceManager.is_official_gov_domain("invalid-url") is False
