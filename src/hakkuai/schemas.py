"""
Pydantic schemas and models for HakkuAI welfare assistant.
Covers worker profiles, welfare schemes, eligibility results,
injury guidance, and document checklists.
"""

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

class Language(str, Enum):
    EN = "en"
    TA = "ta"

class InjurySeverity(str, Enum):
    NONE = "none"
    MINOR = "minor"
    SERIOUS = "serious"
    SEVERE = "severe"
    CRITICAL_LIFE_THREATENING = "critical_life_threatening"

class EligibilityStatus(str, Enum):
    POTENTIALLY_ELIGIBLE = "Potentially eligible"
    MORE_INFORMATION_NEEDED = "More information needed"
    LIKELY_NOT_ELIGIBLE = "Likely not eligible"
    UNVERIFIED_DATA = "Unverified / Incomplete data"

class DocumentStatus(str, Enum):
    AVAILABLE = "Available"
    MISSING = "Missing"
    UNKNOWN = "Not sure"
    NOT_APPLICABLE = "Not applicable"

class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    NEEDS_REVIEW = "needs_review"
    UNVERIFIED = "unverified"

class WorkerProfile(BaseModel):
    """Profile data progressively collected from the worker."""
    state: str | None = None
    district: str | None = None
    occupation: str | None = None
    is_construction_worker: bool | None = None
    is_bocw_registered: bool | None = None
    accident_occurred_at_work: bool | None = None
    accident_date: str | None = None
    injury_severity: InjurySeverity | None = None
    hospital_treatment_received: bool | None = None
    lost_wages: bool | None = None
    has_disability: bool | None = None
    disability_type: str | None = None # e.g. temporary, permanent, loss of limb
    employer_assistance_provided: bool | None = None
    available_documents: list[str] = Field(default_factory=list)
    preferred_language: Language = Language.EN

class Scheme(BaseModel):
    """Schema for a welfare scheme in the verified knowledge base."""
    scheme_id: str
    name: str
    tamil_name: str
    department: str
    state_or_national: str # "National", "Tamil Nadu", "Karnataka", etc.
    target_beneficiaries: list[str]
    eligibility_criteria: list[str]
    benefit_description: str
    benefit_limits: str
    required_documents: list[str]
    application_procedure: str
    official_source_url: str
    source_verification_date: str
    verified_status: VerificationStatus
    verification_notes: str | None = None

class SchemeEligibilityResult(BaseModel):
    """Result of deterministic eligibility check for a scheme."""
    scheme_id: str
    scheme_name: str
    tamil_name: str
    status: EligibilityStatus
    explanation_en: str
    explanation_ta: str
    missing_information: list[str] = Field(default_factory=list)
    unresolved_conditions: list[str] = Field(default_factory=list)
    required_evidence: list[str] = Field(default_factory=list)
    official_source_url: str
    benefit_summary: str
    benefit_limits: str
    verified: bool = True

class DocumentItem(BaseModel):
    """Individual item in a personalized document checklist."""
    document_id: str
    name_en: str
    name_ta: str
    purpose_en: str
    purpose_ta: str
    status: DocumentStatus = DocumentStatus.UNKNOWN
    alternative_evidence_en: str
    alternative_evidence_ta: str
    official_notes: str

class DocumentChecklist(BaseModel):
    """Personalized document checklist."""
    worker_state: str | None = None
    items: list[DocumentItem] = Field(default_factory=list)
    summary_en: str
    summary_ta: str

class InjuryGuidanceResult(BaseModel):
    """Guidance generated specifically for injury and workplace accident support."""
    is_emergency: bool = False
    emergency_message_en: str = ""
    emergency_message_ta: str = ""
    records_to_preserve_en: list[str] = Field(default_factory=list)
    records_to_preserve_ta: list[str] = Field(default_factory=list)
    unregistered_worker_guidance_en: str = ""
    unregistered_worker_guidance_ta: str = ""
    next_steps_en: list[str] = Field(default_factory=list)
    next_steps_ta: list[str] = Field(default_factory=list)
    disclaimer_en: str = ""
    disclaimer_ta: str = ""

class ConversationalResponse(BaseModel):
    """Internal representation of an agent's conversational response."""
    session_id: str
    language: Language
    response_text: str
    current_step: str
    is_emergency: bool = False
    schemes_evaluated: list[SchemeEligibilityResult] = Field(default_factory=list)
    checklist: DocumentChecklist | None = None
    injury_guidance: InjuryGuidanceResult | None = None
    missing_fields: list[str] = Field(default_factory=list)
