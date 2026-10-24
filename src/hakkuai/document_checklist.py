"""
Personalized Document Checklist Generator for HakkuAI.
Constructs targeted document checklists with actionable alternatives
for missing evidence and official verification guidance.
"""

from hakkuai.schemas import (
    WorkerProfile,
    DocumentChecklist,
    DocumentItem,
    DocumentStatus,
    Language
)

# Standard catalog of documents with their purposes and legally accepted alternatives
DOCUMENT_CATALOG = [
    {
        "document_id": "doc_identity_aadhaar",
        "name_en": "Aadhaar Card or Government Photo ID",
        "name_ta": "ஆதார் அட்டை அல்லது அரசு அடையாள அட்டை",
        "purpose_en": "Primary identity verification for DBT (Direct Benefit Transfer) bank remittance.",
        "purpose_ta": "நேரடி வங்கி நிதி பரிமாற்றத்திற்கான அடிப்படை அடையாளச் சான்று.",
        "alternative_evidence_en": "Voter ID, MNREGA Job Card, or Ration Card with photo along with Aadhaar enrolment slip.",
        "alternative_evidence_ta": "வாக்காளர் அட்டை, மகாத்மா காந்தி ஊரக வேலை அட்டை, அல்லது குடும்ப அட்டை.",
        "official_notes": "Essential for identity deduplication across government welfare portals."
    },
    {
        "document_id": "doc_bocw_card",
        "name_en": "BOCW Welfare Board Membership Card / Registration Book",
        "name_ta": "கட்டுமான நல வாரிய உறுப்பினர் அடையாள அட்டை",
        "purpose_en": "Confirms active enrollment with the State Construction Workers Welfare Board.",
        "purpose_ta": "மாநில கட்டுமான நல வாரியத்தில் பதிவு செய்யப்பட்ட உறுப்பினர் என்பதை உறுதிப்படுத்த.",
        "alternative_evidence_en": "Online registration acknowledgment slip, annual subscription renewal receipt, or e-Shram UAN card verifying construction occupation.",
        "alternative_evidence_ta": "இணையதள பதிவு ஒப்புகைச் சீட்டு, கட்டண ரசீது, அல்லது இ-ஷ்ராம் அடையாள அட்டை.",
        "official_notes": "If currently unregistered, compensation can still be pursued under Employees' Compensation Act 1923."
    },
    {
        "document_id": "doc_hospital_discharge",
        "name_en": "Hospital Admission & Discharge Summary / Medical Memo",
        "name_ta": "மருத்துவமனை சிகிச்சை மற்றும் வெளியேற்றச் சான்றிதழ் (Discharge Summary)",
        "purpose_en": "Medical proof of injury severity, treatments received, and hospital stay duration.",
        "purpose_ta": "காயத்தின் தீவிரம் மற்றும் மருத்துவ சிகிச்சையை உறுதிப்படுத்தும் மருத்துவச் சான்று.",
        "alternative_evidence_en": "Emergency casualty outpatient ticket, government doctor's injury certificate, or clinical diagnostic/X-ray reports.",
        "alternative_evidence_ta": "அரசு மருத்துவமனை அவசர சிகிச்சைப் பிரிவு சீட்டு அல்லது மருத்துவர் காயம் குறிப்பு.",
        "official_notes": "Crucial evidence for both welfare board claims and statutory employer compensation."
    },
    {
        "document_id": "doc_disability_certificate",
        "name_en": "Disability Certificate from Government Medical Board",
        "name_ta": "அரசு மருத்துவக் குழு வழங்கிய மாற்றுத்திறனாளி / ஊனமுற்றோர் சான்றிதழ்",
        "purpose_en": "Certifies percentage of temporary or permanent loss of earning capacity.",
        "purpose_ta": "நிரந்தர அல்லது தற்காலிக வேலைத்திறன் இழப்பு சதவீதத்தை அதிகாரப்பூர்வமாக நிர்ணயிக்க.",
        "alternative_evidence_en": "Civil Surgeon assessment report or preliminary hospital superintendent evaluation while formal board review is pending.",
        "alternative_evidence_ta": "அரசு தலைமை மருத்துவ அலுவலர் மதிப்பீட்டு அறிக்கை.",
        "official_notes": "Mandatory specifically for permanent disability and partial loss of limbs claims."
    },
    {
        "document_id": "doc_employment_proof",
        "name_en": "Proof of Employment / Workplace Accident Incident Record",
        "name_ta": "வேலை மற்றும் விபத்துக்கான சான்று (பணிப் பதிவு / நேரடி சாட்சி)",
        "purpose_en": "Establishes that the injury arose out of and in the course of construction work.",
        "purpose_ta": "விபத்து பணியிடத்தில் அல்லது வேலையின் போது நிகழ்ந்தது என்பதை சட்டப்பூர்வமாக நிரூபிக்க.",
        "alternative_evidence_en": "Wage payment slips, contractor memo/WhatsApp instruction, site muster roll entry, or signed affidavit by two co-worker witnesses.",
        "alternative_evidence_ta": "கூலி ரசீது, சைட் மேற்பார்வையாளர் செய்தி, அல்லது சக தொழிலாளர்களின் உறுதிமொழிப் பத்திரம்.",
        "official_notes": "Vital where employers deny employment or refuse to report the accident to the Labour Department."
    },
    {
        "document_id": "doc_bank_passbook",
        "name_en": "Active Bank Passbook Copy (with IFSC Code)",
        "name_ta": "வங்கி பாஸ்புக் நகல் (IFSC குறியீட்டுடன்)",
        "purpose_en": "Account details for direct electronic disbursement of sanctioned relief funds.",
        "purpose_ta": "அரசு நிவாரணத் தொகை நேரடியாக வங்கிக் கணக்கில் வரவு வைக்கப்பட.",
        "alternative_evidence_en": "Cancelled cheque leaf or official bank account statement bearing worker's full name.",
        "alternative_evidence_ta": "வங்கி காசோலை (Cancelled Cheque) அல்லது வங்கி கணக்கு அறிக்கை.",
        "official_notes": "Account must preferably be Aadhaar-seeded to prevent DBT payment reversals."
    }
]

def generate_document_checklist(
    profile: WorkerProfile,
    language: Language = Language.EN
) -> DocumentChecklist:
    """
    Constructs a personalized document checklist mapped to the worker's
    current situation, highlighting available items, missing items,
    and acceptable fallback evidence.
    """
    available_docs_lower = [d.lower() for d in profile.available_documents]
    items: list[DocumentItem] = []

    for catalog_item in DOCUMENT_CATALOG:
        doc_id = catalog_item["document_id"]
        
        # Determine status
        is_available = any(
            doc_id.replace("doc_", "") in avail or avail in doc_id
            for avail in available_docs_lower
        )
        
        if is_available:
            status = DocumentStatus.AVAILABLE
        else:
            # If not explicitly marked available, check if needed
            if doc_id == "doc_disability_certificate" and not profile.has_disability:
                status = DocumentStatus.NOT_APPLICABLE
            elif doc_id == "doc_bocw_card" and profile.is_bocw_registered is False:
                status = DocumentStatus.MISSING
            else:
                status = DocumentStatus.MISSING if profile.available_documents else DocumentStatus.UNKNOWN

        items.append(
            DocumentItem(
                document_id=doc_id,
                name_en=catalog_item["name_en"],
                name_ta=catalog_item["name_ta"],
                purpose_en=catalog_item["purpose_en"],
                purpose_ta=catalog_item["purpose_ta"],
                status=status,
                alternative_evidence_en=catalog_item["alternative_evidence_en"],
                alternative_evidence_ta=catalog_item["alternative_evidence_ta"],
                official_notes=catalog_item["official_notes"]
            )
        )

    available_count = sum(1 for i in items if i.status == DocumentStatus.AVAILABLE)
    missing_count = sum(1 for i in items if i.status == DocumentStatus.MISSING)

    summary_en = (
        f"Document Readiness Summary: {available_count} available, {missing_count} missing or requiring alternative evidence. "
        "Missing documents do not automatically disqualify you from legal compensation."
    )
    summary_ta = (
        f"ஆவணங்கள் தயார் நிலை: {available_count} தயார், {missing_count} தேவைப்படுகிறது. "
        "ஆவணம் இல்லாவிட்டாலும் மாற்று வழிகள் மூலம் சட்டப்பூர்வ நிவாரணம் பெற வாய்ப்புள்ளது."
    )

    return DocumentChecklist(
        worker_state=profile.state,
        items=items,
        summary_en=summary_en,
        summary_ta=summary_ta
    )
