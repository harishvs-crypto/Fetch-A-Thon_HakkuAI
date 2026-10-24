"""
Dedicated Injury Assistance Workflow for HakkuAI.
Prioritizes immediate emergency medical safety (National Emergency 112),
guides evidence preservation, details steps for unregistered workers,
and maps out structured next actions.
"""

from hakkuai.config import settings
from hakkuai.schemas import (
    WorkerProfile,
    InjuryGuidanceResult,
    InjurySeverity,
    Language
)

def evaluate_injury_workflow(
    profile: WorkerProfile,
    raw_user_text: str = ""
) -> InjuryGuidanceResult:
    """
    Evaluates worker's injury condition, checks for immediate life-threatening
    emergencies, outlines vital medical & employment records to preserve,
    and constructs clear next steps.
    """
    is_emergency = False
    
    # Check severity or emergency keywords in user input
    emergency_keywords = [
        "emergency", "unconscious", "heavy bleeding", "severe bleeding", 
        "head injury", "chest crush", "cannot breathe", "dying", 
        "உயிருக்கு ஆபத்து", "அவசரம்", "அதிக ரத்தம்", "மயக்கம்"
    ]
    
    if profile.injury_severity == InjurySeverity.CRITICAL_LIFE_THREATENING:
        is_emergency = True
    elif any(kw in raw_user_text.lower() for kw in emergency_keywords):
        is_emergency = True

    emergency_msg_en = (
        f"🚨 **IMMEDIATE EMERGENCY MEDICAL ALERT**:\n"
        f"If the injured worker requires urgent emergency medical care or is in critical condition, "
        f"please contact emergency services immediately!\n"
        f"• **National Emergency Helpline**: Dial **{settings.EMERGENCY_NATIONAL_NUMBER}**\n"
        f"• **Government Ambulance Service**: Dial **{settings.EMERGENCY_AMBULANCE_NUMBER}**\n"
        f"Ensure immediate hospital admission first. Welfare paperwork and claims can be submitted after emergency stabilization."
    )

    emergency_msg_ta = (
        f"🚨 **அவசர மருத்துவ எச்சரிக்கை**:\n"
        f"காயமடைந்த தொழிலாளிக்கு உடனடி தீவிர சிகிச்சை தேவைப்பட்டால், தாமதிக்காமல் அவசர உதவிக்கு அழைக்கவும்!\n"
        f"• **தேசிய அவசர உதவி எண்**: **{settings.EMERGENCY_NATIONAL_NUMBER}**\n"
        f"• **இலவச ஆம்புலன்ஸ் சேவை**: **{settings.EMERGENCY_AMBULANCE_NUMBER}**\n"
        f"முதலில் மருத்துவ சிகிச்சைக்கு முன்னுரிமை அளியுங்கள். நலத்திட்ட விண்ணப்பங்களை சிகிச்சை தொடங்கிய பிறகும் சமர்ப்பிக்கலாம்."
    )

    records_en = [
        "Medical Records: Preserve all doctor prescriptions, clinical diagnostic reports, X-rays, and the formal Hospital Discharge Summary.",
        "Treatment Expense Bills: Retain all original pharmacy receipts, surgery invoices, and hospital payment vouchers.",
        "Accident Scene Evidence: Record date, exact site location, type of machinery/scaffolding involved, and take photos if safely possible.",
        "Employment Relationship Evidence: Preserve supervisor WhatsApp messages, subcontractor wage receipts, muster roll entries, or co-worker contact numbers.",
        "Police / Official Intimation: Secure a copy of the General Diary (GD) entry or FIR if a police intimation was registered at the hospital."
    ]

    records_ta = [
        "மருத்துவ ஆவணங்கள்: மருந்து சீட்டுகள், எக்ஸ்-ரே, ஸ்கேன் அறிக்கைகள் மற்றும் மருத்துவமனை வெளியேற்றச் சான்றிதழை (Discharge Summary) பத்திரமாக வைக்கவும்.",
        "சிகிச்சை ரசீதுகள்: மருந்து வாங்கிய அசல் ரசீதுகள் மற்றும் மருத்துவமனை கட்டண ரசீதுகளைப் பாதுகாக்கவும்.",
        "விபத்து விவரங்கள்: விபத்து நடந்த தேதி, நேரம், இடம், பணி வகை மற்றும் முடிந்தால் விபத்து நிகழ்ந்த இடத்தின் புகைப்படம்.",
        "வேலை செய்ததற்கான ஆதாரம்: சைட் மேற்பார்வையாளரின் குறுஞ்செய்திகள், கூலி வழங்கிய விவரம், அல்லது சக தொழிலாளர்களின் தொடர்பு எண்கள்.",
        "காவல்துறை குறிப்பு: மருத்துவமனையில் பதிவு செய்யப்பட்ட GD குறிப்பு அல்லது FIR நகல் (இருப்பின்)."
    ]

    unregistered_guidance_en = (
        "**Guidance When Unregistered with the Welfare Board**:\n"
        "Even if your employer or contractor did not register you with the State BOCW Welfare Board:\n"
        "1. **Statutory Employer Liability**: Under the Employees' Compensation Act 1923, the employer/principal contractor is legally obligated to compensate on-duty injuries regardless of board registration.\n"
        "2. **Retroactive Registration & Proof**: In many states, legal aid or trade unions can assist in submitting registration with evidence of 90 days continuous construction work.\n"
        "3. **Labour Commissioner Approach**: You can file a formal grievance before the District Labour Officer or Commissioner for Employees' Compensation."
    )

    unregistered_guidance_ta = (
        "**நல வாரியத்தில் பதிவு செய்யப்படாத தொழிலாளர்களுக்கான வழிகாட்டல்**:\n"
        "முதலாளி அல்லது ஒப்பந்ததாரர் உங்களை நல வாரியத்தில் பதிவு செய்யவில்லை என்றாலும்:\n"
        "1. **முதலாளியின் சட்டபூர்வ பொறுப்பு**: பணியாளர் இழப்பீட்டுச் சட்டம் 1923-ன் கீழ், வாரியத்தில் பதிவு இல்லாவிட்டாலும் காயமடைந்த தொழிலாளிக்கு இழப்பீடு வழங்க முதலாளி கடமைப்பட்டவர்.\n"
        "2. **தாமதப் பதிவு**: கடந்த 90 நாட்கள் கட்டுமானப் பணி செய்ததற்கான சான்றுகளுடன் தொழிலாளர் உதவி மையம் அல்லது தொழிற்சங்கம் மூலம் பதிவு பெற முயற்சிக்கலாம்.\n"
        "3. **தொழிலாளர் ஆணையர் அலுவலகம்**: மாவட்ட தொழிலாளர் அலுவலரிடம் எழுத்துப்பூர்வமாக மனு அளிக்கலாம்."
    )

    next_steps_en = [
        "Step 1: Obtain a certified Discharge Summary and injury memo from the treating government or accredited hospital.",
        "Step 2: If permanent loss of earning capacity occurred, schedule an evaluation before the District Government Medical Board for a Disability Certificate.",
        "Step 3: Issue a formal written notice of accident to the employer/principal contractor requesting statutory support.",
        "Step 4: Visit the District Labour Officer (Social Security Scheme) or local e-Sevai / Common Service Centre (CSC) to submit the welfare board application.",
        "Step 5: If the employer denies compensation, approach the District Legal Services Authority (DLSA) for free legal aid to file before the Labour Court."
    ]

    next_steps_ta = [
        "படி 1: சிகிச்சை பெற்ற மருத்துவமனையிலிருந்து முறையான Discharge Summary மற்றும் காயம் குறித்த மருத்துவச் சான்றிதழைப் பெறவும்.",
        "படி 2: நிரந்தர ஊனம் ஏற்பட்டிருந்தால், மாவட்ட அரசு மருத்துவக் குழுவிடம் மாற்றுத்திறனாளி சான்றிதழ் பெற அணுகவும்.",
        "படி 3: விபத்து குறித்து ஒப்பந்ததாரர்/முதலாளிக்கு எழுத்துப்பூர்வமாக தகவல் தெரிவிக்கவும்.",
        "படி 4: உங்கள் மாவட்ட தொழிலாளர் நல அலுவலர் (சமூக பாதுகாப்பு திட்டம்) அல்லது இ-சேவை மையம் மூலம் நல வாரிய நிவாரணத்திற்கு விண்ணப்பிக்கவும்.",
        "படி 5: முதலாளி இழப்பீடு வழங்க மறுத்தால், இலவச சட்ட உதவிக்கு மாவட்ட சட்டப்பணிகள் ஆணைக்குழுவை (DLSA) அணுகலாம்."
    ]

    disclaimer_en = (
        "Disclaimer: HakkuAI provides educational welfare guidance and does not issue legal rulings or government decisions. "
        "Actual entitlement depends on formal investigation, official verification of documents, and statutory discretion of competent authorities."
    )

    disclaimer_ta = (
        "பொறுப்புத் துறப்பு: ஹக்கு ஏஐ (HakkuAI) பொதுவான வழிகாட்டலை மட்டுமே வழங்குகிறது; இது அதிகாரப்பூர்வ அரசு தீர்ப்பு அல்ல. "
        "இறுதி நிவாரணத் தொகை மற்றும் தகுதி, அரசு அதிகாரிகளின் ஆவண சரிபார்ப்புக்குப் பிறகே தீர்மானிக்கப்படும்."
    )

    return InjuryGuidanceResult(
        is_emergency=is_emergency,
        emergency_message_en=emergency_msg_en,
        emergency_message_ta=emergency_msg_ta,
        records_to_preserve_en=records_en,
        records_to_preserve_ta=records_ta,
        unregistered_worker_guidance_en=unregistered_guidance_en,
        unregistered_worker_guidance_ta=unregistered_guidance_ta,
        next_steps_en=next_steps_en,
        next_steps_ta=next_steps_ta,
        disclaimer_en=disclaimer_en,
        disclaimer_ta=disclaimer_ta
    )
