"""
Deterministic Eligibility Assessment Engine for HakkuAI.
Evaluates worker profiles against verified government welfare schemes.
Provides honest uncertainty handling, missing information detection,
and clear bilingual explanations.
"""

from hakkuai.schemas import (
    WorkerProfile,
    Scheme,
    SchemeEligibilityResult,
    EligibilityStatus,
    InjurySeverity
)
from hakkuai.scheme_database import SchemeDatabase, scheme_db
from hakkuai.sources import SourceManager

def evaluate_tn_bocw_scheme(profile: WorkerProfile, scheme: Scheme) -> SchemeEligibilityResult:
    """Evaluates eligibility for Tamil Nadu BOCW Accident Relief Scheme."""
    norm_state = SchemeDatabase.normalize_state(profile.state)
    missing_info: list[str] = []
    unresolved: list[str] = []
    required_evidence: list[str] = [
        "TNBOCW Welfare Board membership identity card or registration receipt",
        "Hospital discharge summary and medical injury memo",
        "Police GD entry or employer accident memorandum",
        "Disability certificate from Government Medical Board (if permanent disability)"
    ]

    # Check state applicability
    if norm_state and norm_state != "Tamil Nadu":
        return SchemeEligibilityResult(
            scheme_id=scheme.scheme_id,
            scheme_name=scheme.name,
            tamil_name=scheme.tamil_name,
            status=EligibilityStatus.LIKELY_NOT_ELIGIBLE,
            explanation_en=f"This scheme only applies to construction workers in Tamil Nadu. The indicated state is '{profile.state}'.",
            explanation_ta=f"இத்திட்டம் தமிழ்நாட்டில் உள்ள கட்டுமானத் தொழிலாளர்களுக்கு மட்டுமே பொருந்தும். நீங்கள் குறிப்பிட்ட மாநிலம்: '{profile.state}'.",
            missing_information=[],
            unresolved_conditions=[],
            required_evidence=[],
            official_source_url=scheme.official_source_url,
            benefit_summary=scheme.benefit_description,
            benefit_limits=scheme.benefit_limits,
            verified=True
        )

    # Check occupation
    if profile.is_construction_worker is False:
        return SchemeEligibilityResult(
            scheme_id=scheme.scheme_id,
            scheme_name=scheme.name,
            tamil_name=scheme.tamil_name,
            status=EligibilityStatus.LIKELY_NOT_ELIGIBLE,
            explanation_en="TNBOCW benefits are specifically restricted to registered construction and civil building workers.",
            explanation_ta="தமிழ்நாடு கட்டுமான நல வாரிய நிவாரணம் கட்டுமானத் தொழிலாளர்களுக்கு மட்டுமே ஒதுக்கப்பட்டுள்ளது.",
            missing_information=[],
            unresolved_conditions=[],
            required_evidence=[],
            official_source_url=scheme.official_source_url,
            benefit_summary=scheme.benefit_description,
            benefit_limits=scheme.benefit_limits,
            verified=True
        )

    # Collect missing essential questions
    if profile.is_construction_worker is None:
        missing_info.append("Confirmation of whether worker is engaged in construction work")
    if profile.is_bocw_registered is None:
        missing_info.append("Status of registration with Tamil Nadu Construction Workers Welfare Board")
    if profile.accident_occurred_at_work is None:
        missing_info.append("Confirmation of whether injury occurred at or during work")

    # If missing core facts
    if missing_info:
        return SchemeEligibilityResult(
            scheme_id=scheme.scheme_id,
            scheme_name=scheme.name,
            tamil_name=scheme.tamil_name,
            status=EligibilityStatus.MORE_INFORMATION_NEEDED,
            explanation_en="Preliminary match for Tamil Nadu construction workers, but crucial eligibility details are pending.",
            explanation_ta="தமிழ்நாடு கட்டுமானத் தொழிலாளர்களுக்கான சாத்தியமுள்ள திட்டம், ஆனால் மேலும் சில முக்கிய விவரங்கள் தேவை.",
            missing_information=missing_info,
            unresolved_conditions=[
                "Active membership in TNBOCW Welfare Board",
                "Workplace accident connection",
                "Official medical board assessment"
            ],
            required_evidence=required_evidence,
            official_source_url=scheme.official_source_url,
            benefit_summary=scheme.benefit_description,
            benefit_limits=scheme.benefit_limits,
            verified=True
        )

    # Worker is construction worker in Tamil Nadu
    if profile.is_bocw_registered is True and profile.accident_occurred_at_work is True:
        unresolved.append("Verification of active card renewal by District Labour Officer")
        unresolved.append("Disability percentage certification by Medical Board")
        return SchemeEligibilityResult(
            scheme_id=scheme.scheme_id,
            scheme_name=scheme.name,
            tamil_name=scheme.tamil_name,
            status=EligibilityStatus.POTENTIALLY_ELIGIBLE,
            explanation_en=(
                "Worker meets the preliminary criteria as a registered construction worker in Tamil Nadu "
                "with an on-duty injury. Formal claim must be verified and sanctioned by the District Labour Officer (Social Security)."
            ),
            explanation_ta=(
                "தமிழ்நாட்டில் பதிவுசெய்த கட்டுமானத் தொழிலாளியாக இருந்து பணியில் விபத்து ஏற்பட்டுள்ளதால், "
                "இத்திட்டத்தின் கீழ் நிவாரணம் பெற சாத்தியக்கூறு உள்ளது. அதிகாரப்பூர்வ ஆவண சரிபார்ப்புக்குப் பிறகே இறுதி முடிவு எடுக்கப்படும்."
            ),
            missing_information=[],
            unresolved_conditions=unresolved,
            required_evidence=required_evidence,
            official_source_url=scheme.official_source_url,
            benefit_summary=scheme.benefit_description,
            benefit_limits=scheme.benefit_limits,
            verified=True
        )
    elif profile.is_bocw_registered is False:
        return SchemeEligibilityResult(
            scheme_id=scheme.scheme_id,
            scheme_name=scheme.name,
            tamil_name=scheme.tamil_name,
            status=EligibilityStatus.MORE_INFORMATION_NEEDED,
            explanation_en=(
                "Direct TNBOCW Board claim requires board registration. If currently unregistered, "
                "guidance is available on retroactive documentation or claiming compensation under the Central Employees' Compensation Act 1923."
            ),
            explanation_ta=(
                "வாரியத்தில் பதிவு பெறாத நிலையில் நேரடியாக நிவாரணம் கோர இயலாது. எனினும், பணியாளர் இழப்பீட்டுச் சட்டம் 1923 "
                "மூலம் முதலாளியிடம் இருந்து இழப்பீடு பெறலாம் அல்லது தாமதப் பதிவு சாத்தியங்களை அணுகலாம்."
            ),
            missing_information=["Check if past subscription or pending registration receipt exists"],
            unresolved_conditions=["Formal board membership validation"],
            required_evidence=required_evidence,
            official_source_url=scheme.official_source_url,
            benefit_summary=scheme.benefit_description,
            benefit_limits=scheme.benefit_limits,
            verified=True
        )
    else:
        return SchemeEligibilityResult(
            scheme_id=scheme.scheme_id,
            scheme_name=scheme.name,
            tamil_name=scheme.tamil_name,
            status=EligibilityStatus.LIKELY_NOT_ELIGIBLE,
            explanation_en="Accident did not occur in the course of employment or worker does not satisfy board criteria.",
            explanation_ta="விபத்து பணியின் போது ஏற்படவில்லை அல்லது வாரிய நிபந்தனைகள் பூர்த்தியாகவில்லை.",
            missing_information=[],
            unresolved_conditions=[],
            required_evidence=[],
            official_source_url=scheme.official_source_url,
            benefit_summary=scheme.benefit_description,
            benefit_limits=scheme.benefit_limits,
            verified=True
        )

def evaluate_employees_compensation_scheme(profile: WorkerProfile, scheme: Scheme) -> SchemeEligibilityResult:
    """Evaluates statutory compensation under Employees' Compensation Act 1923."""
    required_evidence = [
        "Proof of work connection (muster roll, subcontractor voucher, wage slip, supervisor call/SMS logs, or co-worker witness affidavits)",
        "Hospital admission and discharge record",
        "Disability certificate by qualified government medical practitioner",
        "Notice of accident served to employer / contractor"
    ]

    if profile.accident_occurred_at_work is None:
        return SchemeEligibilityResult(
            scheme_id=scheme.scheme_id,
            scheme_name=scheme.name,
            tamil_name=scheme.tamil_name,
            status=EligibilityStatus.MORE_INFORMATION_NEEDED,
            explanation_en="Requires confirmation of whether the injury was sustained in the course of employment.",
            explanation_ta="விபத்து வேலையின் போது அல்லது பணியின் காரணமாக ஏற்பட்டதா என்ற தகவல் தேவை.",
            missing_information=["Workplace accident occurrence"],
            unresolved_conditions=["Establishing employer-employee relationship and wage evidence"],
            required_evidence=required_evidence,
            official_source_url=scheme.official_source_url,
            benefit_summary=scheme.benefit_description,
            benefit_limits=scheme.benefit_limits,
            verified=True
        )

    if profile.accident_occurred_at_work is False:
        return SchemeEligibilityResult(
            scheme_id=scheme.scheme_id,
            scheme_name=scheme.name,
            tamil_name=scheme.tamil_name,
            status=EligibilityStatus.LIKELY_NOT_ELIGIBLE,
            explanation_en="The Employees' Compensation Act applies strictly to injuries arising out of and in the course of employment.",
            explanation_ta="பணியாளர் இழப்பீட்டுச் சட்டம் பணியிடத்தில் அல்லது வேலையின் போது ஏற்படும் விபத்துகளுக்கு மட்டுமே பொருந்தும்.",
            missing_information=[],
            unresolved_conditions=[],
            required_evidence=[],
            official_source_url=scheme.official_source_url,
            benefit_summary=scheme.benefit_description,
            benefit_limits=scheme.benefit_limits,
            verified=True
        )

    # Workplace injury confirmed: applies universally across India, even if unregistered
    unresolved = [
        "Employer acknowledgment or adjudication before Commissioner for Employees' Compensation",
        "Assessment of loss of earning capacity by registered doctor"
    ]
    return SchemeEligibilityResult(
        scheme_id=scheme.scheme_id,
        scheme_name=scheme.name,
        tamil_name=scheme.tamil_name,
        status=EligibilityStatus.POTENTIALLY_ELIGIBLE,
        explanation_en=(
            "Under Indian law (Employees' Compensation Act 1923), the employer/contractor is legally liable "
            "to compensate an injured worker. This applies regardless of whether the worker is registered with a state welfare board."
        ),
        explanation_ta=(
            "இந்தியச் சட்டப்படி (பணியாளர் இழப்பீட்டுச் சட்டம் 1923), வேலையின் போது காயமடைந்த தொழிலாளிக்கு "
            "சட்டபூர்வ இழப்பீடு வழங்க முதலாளிக்குக் கடமையுண்டு. தொழிலாளி நல வாரியத்தில் பதிவு செய்யப்படாதிருந்தாலும் இது பொருந்தும்."
        ),
        missing_information=[],
        unresolved_conditions=unresolved,
        required_evidence=required_evidence,
        official_source_url=scheme.official_source_url,
        benefit_summary=scheme.benefit_description,
        benefit_limits=scheme.benefit_limits,
        verified=True
    )

def evaluate_pmjay_scheme(profile: WorkerProfile, scheme: Scheme) -> SchemeEligibilityResult:
    """Evaluates Ayushman Bharat / CMCHIS hospitalization support."""
    required_evidence = [
        "Ayushman Card / State Health Card (e.g., CMCHIS card in Tamil Nadu)",
        "Priority Household (PHH) Ration Card or BPL Food Security Card",
        "Aadhaar card of patient"
    ]

    status = EligibilityStatus.POTENTIALLY_ELIGIBLE
    explanation_en = (
        "Provides cashless emergency trauma surgery and secondary/tertiary hospital care up to ₹5,00,000/year "
        "at empanelled government and private hospitals for eligible unorganized worker families."
    )
    explanation_ta = (
        "அங்கீகரிக்கப்பட்ட அரசு மற்றும் தனியார் மருத்துவமனைகளில் ₹5,00,000 வரை கட்டணமில்லா உள்நோயாளி "
        "சிகிச்சை மற்றும் அறுவை சிகிச்சை பெற இத்திட்டம் உதவும்."
    )
    missing: list[str] = []
    if profile.hospital_treatment_received is None:
        missing.append("Confirmation of hospital admission or requirement for inpatient treatment")

    return SchemeEligibilityResult(
        scheme_id=scheme.scheme_id,
        scheme_name=scheme.name,
        tamil_name=scheme.tamil_name,
        status=status if not missing else EligibilityStatus.MORE_INFORMATION_NEEDED,
        explanation_en=explanation_en,
        explanation_ta=explanation_ta,
        missing_information=missing,
        unresolved_conditions=["Verification of beneficiary status at hospital Ayushman Mitra kiosk"],
        required_evidence=required_evidence,
        official_source_url=scheme.official_source_url,
        benefit_summary=scheme.benefit_description,
        benefit_limits=scheme.benefit_limits,
        verified=True
    )

def evaluate_pmsby_scheme(profile: WorkerProfile, scheme: Scheme) -> SchemeEligibilityResult:
    """Evaluates Pradhan Mantri Suraksha Bima Yojana."""
    required_evidence = [
        "Bank passbook page showing ₹20 PMSBY premium auto-debit deduction",
        "Medical hospital discharge summary & disability certificate",
        "Police GD / FIR copy (for accidental verification)"
    ]

    return SchemeEligibilityResult(
        scheme_id=scheme.scheme_id,
        scheme_name=scheme.name,
        tamil_name=scheme.tamil_name,
        status=EligibilityStatus.MORE_INFORMATION_NEEDED,
        explanation_en=(
            "Provides ₹1,00,000 to ₹2,00,000 accidental disability insurance if worker's bank savings account "
            "had the annual ₹20 PMSBY auto-debit active prior to the accident."
        ),
        explanation_ta=(
            "விபத்துக்கு முன் உங்கள் வங்கிக் கணக்கில் ₹20 காப்பீட்டுக் கட்டணம் பிடித்தம் செய்யப்பட்டிருந்தால், "
            "விபத்து ஊனத்திற்கு ₹1,00,000 முதல் ₹2,00,000 வரை காப்பீடு கிடைக்க வாய்ப்புள்ளது."
        ),
        missing_information=["Verification of ₹20 PMSBY debit in bank passbook"],
        unresolved_conditions=["Timely claim submission through bank branch within 30 days"],
        required_evidence=required_evidence,
        official_source_url=scheme.official_source_url,
        benefit_summary=scheme.benefit_description,
        benefit_limits=scheme.benefit_limits,
        verified=True
    )

def evaluate_eshram_scheme(profile: WorkerProfile, scheme: Scheme) -> SchemeEligibilityResult:
    """Evaluates e-Shram National Unorganised Worker Registry."""
    required_evidence = [
        "e-Shram 12-digit UAN Card",
        "Aadhaar Card linked to active mobile",
        "Bank passbook details"
    ]
    return SchemeEligibilityResult(
        scheme_id=scheme.scheme_id,
        scheme_name=scheme.name,
        tamil_name=scheme.tamil_name,
        status=EligibilityStatus.POTENTIALLY_ELIGIBLE,
        explanation_en=(
            "Universal portable identification for informal workers offering integrated accidental insurance "
            "and national social security scheme linkage."
        ),
        explanation_ta=(
            "அமைப்புசாரா தொழிலாளர்களுக்கான தேசிய அடையாள அட்டை (UAN). விபத்துக் காப்பீடு மற்றும் அரசு நலத்திட்டங்களை பெற உதவும்."
        ),
        missing_information=[],
        unresolved_conditions=["e-Shram portal registration status"],
        required_evidence=required_evidence,
        official_source_url=scheme.official_source_url,
        benefit_summary=scheme.benefit_description,
        benefit_limits=scheme.benefit_limits,
        verified=True
    )

def evaluate_karnataka_bocw_scheme(profile: WorkerProfile, scheme: Scheme) -> SchemeEligibilityResult:
    """Evaluates Karnataka BOCW Accident Benefit Scheme."""
    norm_state = SchemeDatabase.normalize_state(profile.state)
    if norm_state and norm_state != "Karnataka":
        return SchemeEligibilityResult(
            scheme_id=scheme.scheme_id,
            scheme_name=scheme.name,
            tamil_name=scheme.tamil_name,
            status=EligibilityStatus.LIKELY_NOT_ELIGIBLE,
            explanation_en=f"Restricted to Karnataka construction workers. Worker indicated state: '{profile.state}'.",
            explanation_ta=f"கர்நாடக கட்டுமானத் தொழிலாளர்களுக்கு மட்டுமே பொருந்தும். தற்போதைய மாநிலம்: '{profile.state}'.",
            missing_information=[],
            unresolved_conditions=[],
            required_evidence=[],
            official_source_url=scheme.official_source_url,
            benefit_summary=scheme.benefit_description,
            benefit_limits=scheme.benefit_limits,
            verified=True
        )

    required_evidence = [
        "KBOCW Identity Card",
        "90-day construction work certificate",
        "Hospital discharge summary and Medical Board disability certificate"
    ]
    missing = []
    if profile.is_bocw_registered is None:
        missing.append("Karnataka BOCW board registration status")
    if profile.accident_occurred_at_work is None:
        missing.append("On-duty accident confirmation")

    status = EligibilityStatus.POTENTIALLY_ELIGIBLE if (profile.is_bocw_registered and profile.accident_occurred_at_work) else EligibilityStatus.MORE_INFORMATION_NEEDED

    return SchemeEligibilityResult(
        scheme_id=scheme.scheme_id,
        scheme_name=scheme.name,
        tamil_name=scheme.tamil_name,
        status=status,
        explanation_en="Applicable for construction workers in Karnataka registered with KBOCWWB with 90 days certified work.",
        explanation_ta="கர்நாடக கட்டுமான நல வாரியத்தில் பதிவு செய்து 90 நாட்கள் பணியாற்றிய தொழிலாளர்களுக்கு பொருந்தும்.",
        missing_information=missing,
        unresolved_conditions=["Official submission to Karnataka Labour Officer via Seva Sindhu"],
        required_evidence=required_evidence,
        official_source_url=scheme.official_source_url,
        benefit_summary=scheme.benefit_description,
        benefit_limits=scheme.benefit_limits,
        verified=True
    )

def build_unverified_state_result(state_name: str) -> SchemeEligibilityResult:
    """
    Constructs an explicit, honest uncertainty result when a worker's state
    has no verified state-specific BOCW schemes in our local database.
    Does NOT fabricate benefits or rules!
    """
    norm_state = SchemeDatabase.normalize_state(state_name) or state_name
    return SchemeEligibilityResult(
        scheme_id=f"state_bocw_{norm_state.lower().replace(' ', '_')}_unverified",
        scheme_name=f"{norm_state} Building & Other Construction Workers Welfare Board (Unverified in Local DB)",
        tamil_name=f"{norm_state} கட்டுமானத் தொழிலாளர் நல வாரியம் (உள் தரவுத்தளத்தில் சரிபார்க்கப்படவில்லை)",
        status=EligibilityStatus.UNVERIFIED_DATA,
        explanation_en=(
            f"Notice of Incomplete Local Rules: HakkuAI's local verified database does not currently contain "
            f"verified state-specific benefit schedules for {norm_state}. To ensure absolute honesty, "
            f"we do NOT fabricate benefit amounts or eligibility criteria. Please contact the {norm_state} "
            f"Labour Commissioner Office or District Labour Welfare Board directly."
        ),
        explanation_ta=(
            f"குறிப்பு: {norm_state} மாநிலத்திற்கான குறிப்பிட்ட நலவாரிய விதிகள் தற்போதைய தரவுத்தளத்தில் "
            f"முழுமையாக சரிபார்க்கப்படவில்லை. நாங்கள் பொய்யான தகவல்களை வழங்குவதில்லை. தயவுசெய்து உங்கள் மாவட்ட தொழிலாளர் "
            f"துறை அலுவலரை நேரடியாக அணுகவும்."
        ),
        missing_information=[f"Official {norm_state} state government benefit schedule"],
        unresolved_conditions=["Contact local Labour Commissioner for state-specific welfare rules"],
        required_evidence=["Local state labor registration card", "Hospital injury certificate"],
        official_source_url="https://labour.gov.in",
        benefit_summary="State-specific welfare board ex-gratia relief (requires local department verification)",
        benefit_limits="Subject to state-specific board notification (unverified locally)",
        verified=False
    )

def assess_worker_eligibility(
    profile: WorkerProfile,
    db: SchemeDatabase | None = None
) -> list[SchemeEligibilityResult]:
    """
    Main deterministic eligibility assessment engine.
    Pure testable function evaluating schemes for the given profile.
    """
    active_db = db or scheme_db
    results: list[SchemeEligibilityResult] = []

    # 1. Evaluate known schemes from database
    relevant_schemes = active_db.query_schemes(state=profile.state, include_national=True)

    for scheme in relevant_schemes:
        if scheme.scheme_id == "tn_bocw_accident_relief":
            results.append(evaluate_tn_bocw_scheme(profile, scheme))
        elif scheme.scheme_id == "central_employees_compensation_1923":
            results.append(evaluate_employees_compensation_scheme(profile, scheme))
        elif scheme.scheme_id == "ayushman_bharat_pmjay":
            results.append(evaluate_pmjay_scheme(profile, scheme))
        elif scheme.scheme_id == "central_pmsby":
            results.append(evaluate_pmsby_scheme(profile, scheme))
        elif scheme.scheme_id == "central_eshram_registry":
            results.append(evaluate_eshram_scheme(profile, scheme))
        elif scheme.scheme_id == "karnataka_bocw_accident_benefit":
            results.append(evaluate_karnataka_bocw_scheme(profile, scheme))

    # 2. Check if worker provided a state for which we have NO state-specific BOCW coverage
    norm_state = SchemeDatabase.normalize_state(profile.state)
    if norm_state and norm_state not in ("Tamil Nadu", "Karnataka"):
        # Local database lacks verified state-specific BOCW scheme for this state
        results.append(build_unverified_state_result(norm_state))

    return results
