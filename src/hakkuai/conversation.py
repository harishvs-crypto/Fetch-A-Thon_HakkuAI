"""
Conversational Engine and Session Manager for HakkuAI.
Maintains isolated worker sessions, implements progressive intake,
detects language (English & Tamil), extracts profile attributes,
and composes empathetic, human-readable welfare guidance.
"""

import re
import time
from typing import Dict, Any, List
from hakkuai.schemas import (
    WorkerProfile,
    Language,
    InjurySeverity,
    EligibilityStatus,
    DocumentStatus,
    ConversationalResponse,
    DocumentChecklist
)
from hakkuai.scheme_database import SchemeDatabase, scheme_db
from hakkuai.eligibility import assess_worker_eligibility
from hakkuai.document_checklist import generate_document_checklist
from hakkuai.injury_workflow import evaluate_injury_workflow
from hakkuai.sources import SourceManager
from hakkuai.logging_config import logger

class UserSession:
    """Represents an isolated worker interaction session."""
    def __init__(self, session_id: str, sender_address: str):
        self.session_id: str = session_id
        self.sender_address: str = sender_address
        self.profile: WorkerProfile = WorkerProfile()
        self.language: Language = Language.EN
        self.history: list[dict[str, str]] = []
        self.step: str = "INTAKE"
        self.last_active: float = time.time()

class SessionManager:
    """Manages active user sessions with strict per-sender isolation."""
    def __init__(self):
        self._sessions: dict[str, UserSession] = {}

    def get_or_create_session(self, sender: str) -> UserSession:
        """Retrieves or initializes a session for a given sender."""
        if sender not in self._sessions:
            session = UserSession(session_id=f"sess_{sender[:12]}", sender_address=sender)
            self._sessions[sender] = session
            logger.info(f"Initialized new isolated session for sender: {sender}")
        else:
            self._sessions[sender].last_active = time.time()
        return self._sessions[sender]

    def clear_session(self, sender: str) -> None:
        """Resets a session."""
        if sender in self._sessions:
            del self._sessions[sender]

class ConversationEngine:
    """Core conversational engine for HakkuAI."""

    def __init__(self, session_manager: SessionManager | None = None):
        self.session_manager = session_manager or SessionManager()

    @staticmethod
    def detect_language(text: str) -> Language:
        """Detects whether user prefers Tamil or English."""
        # 1. Check for Tamil Unicode characters (\u0B80-\u0BFF)
        if re.search(r"[\u0B80-\u0BFF]", text):
            return Language.TA
        lowered = text.lower()
        # 2. Strip occurrences of 'tamil nadu' so state mention does not trigger Tamil language
        cleaned = re.sub(r"\btamil\s*nadu\b", "", lowered)
        # 3. Check for explicit request to communicate in Tamil
        if re.search(r"\b(tamil|tamizh|tamilil)\b", cleaned):
            return Language.TA
        return Language.EN

    @staticmethod
    def extract_profile_updates(text: str, profile: WorkerProfile) -> None:
        """
        Progressively extracts worker attributes from conversational text.
        Never demands all information in one single turn.
        """
        t = text.lower()

        # 1. State detection
        for alias, standard in [
            ("tamil nadu", "Tamil Nadu"), ("tamilnadu", "Tamil Nadu"), ("tn", "Tamil Nadu"),
            ("கர்நாடகா", "Karnataka"), ("தமிழ்நாடு", "Tamil Nadu"),
            ("karnataka", "Karnataka"), ("kerala", "Kerala"), ("andhra", "Andhra Pradesh"),
            ("delhi", "Delhi"), ("maharashtra", "Maharashtra"), ("uttar pradesh", "Uttar Pradesh"),
            ("bihar", "Bihar"), ("west bengal", "West Bengal"), ("nagaland", "Nagaland"),
            ("sikkim", "Sikkim")
        ]:
            if alias in t:
                profile.state = standard
                break

        # 2. Occupation detection
        if any(w in t for w in ["construction", "building", "mason", "carpenter", "painter", "welder", "site worker", "கூலி", "கட்டுமானம்", "மேஸ்திரி", "கொத்தனார்", "கட்டுமானத் தொழிலாளி"]):
            profile.is_construction_worker = True
            profile.occupation = "Construction Worker"

        # 3. Registration detection - check negative conditions first
        negative_reg_terms = [
            "never registered", "unregistered", "not registered", "didn't register",
            "did not register", "no card", "have not registered", "not yet registered",
            "un-registered", "non-registered", "பதிவு செய்யவில்லை", "அட்டை இல்லை"
        ]
        if any(w in t for w in negative_reg_terms):
            profile.is_bocw_registered = False
        elif re.search(r"\b(registered|have bocw|have card|welfare board member|member)\b", t) or any(w in t for w in ["பதிவு செய்துள்ளேன்", "அட்டை உள்ளது", "உறுப்பினர்"]):
            profile.is_bocw_registered = True

        # 4. Accident / Injury occurrence
        if any(w in t for w in ["injury", "injured", "accident", "hurt", "fell", "fracture", "leg", "hand", "wound", "விபத்து", "காயம்", "கால் உடைந்தது", "அடிபட்டது"]):
            profile.accident_occurred_at_work = True

        # 5. Severity check
        if any(w in t for w in ["unconscious", "head injury", "severe bleeding", "critical", "emergency", "உயிருக்கு ஆபத்து", "அவசரம்"]):
            profile.injury_severity = InjurySeverity.CRITICAL_LIFE_THREATENING
        elif any(w in t for w in ["fracture", "cannot walk", "loss of limb", "admitted", "surgery", "தீவிர காயம்", "எலும்பு முறிவு", "அறுவை சிகிச்சை"]):
            profile.injury_severity = InjurySeverity.SEVERE
        elif any(w in t for w in ["cut", "sprain", "minor", "சிறிய காயம்"]):
            profile.injury_severity = InjurySeverity.MINOR

        # 6. Lost wages / disability
        if any(w in t for w in ["cannot earn", "lost wages", "cannot work", "bed rest", "disabled", "வருமானம் இல்லை", "வேலை செய்ய முடியவில்லை", "ஊனம்"]):
            profile.lost_wages = True
            profile.has_disability = True

        # 7. Hospital treatment
        if any(w in t for w in ["hospital", "doctor", "clinic", "admitted", "discharge", "மருத்துவமனை", "சிகிச்சை"]):
            profile.hospital_treatment_received = True

        # 8. Available documents
        if "aadhaar" in t or "ஆதார்" in t:
            if "aadhaar" not in profile.available_documents:
                profile.available_documents.append("aadhaar")
        if any(w in t for w in ["passbook", "bank account", "வங்கி பாஸ்புக்", "வங்கி"]):
            if "bank_passbook" not in profile.available_documents:
                profile.available_documents.append("bank_passbook")
        if any(w in t for w in ["discharge summary", "medical bills", "மருத்துவ அறிக்கை"]):
            if "hospital_discharge" not in profile.available_documents:
                profile.available_documents.append("hospital_discharge")
        if any(w in t for w in ["bocw card", "board card", "நல வாரிய அட்டை"]):
            if "bocw_card" not in profile.available_documents:
                profile.available_documents.append("bocw_card")

    def process_message(self, sender: str, text: str) -> ConversationalResponse:
        """
        Main entry point for conversational interaction.
        Returns a rich ConversationalResponse object.
        """
        session = self.session_manager.get_or_create_session(sender)
        raw_text = text.strip()

        # Update language preference if detected
        lang = self.detect_language(raw_text)
        session.language = lang
        session.profile.preferred_language = lang

        # Extract profile updates
        self.extract_profile_updates(raw_text, session.profile)

        # Record history
        session.history.append({"role": "user", "text": raw_text})

        # 1. Evaluate injury guidance (including 112 emergency check)
        injury_guidance = evaluate_injury_workflow(session.profile, raw_user_text=raw_text)

        # 2. Evaluate eligibility across schemes
        evaluated_schemes = assess_worker_eligibility(session.profile, db=scheme_db)

        # 3. Generate personalized checklist
        checklist = generate_document_checklist(session.profile, language=lang)

        # 4. Formulate response text
        response_text = self._compose_response(
            session=session,
            raw_text=raw_text,
            injury_guidance=injury_guidance,
            schemes=evaluated_schemes,
            checklist=checklist
        )

        session.history.append({"role": "assistant", "text": response_text})

        # Find remaining missing fields to guide next questions
        missing_fields = []
        if session.profile.state is None:
            missing_fields.append("state")
        if session.profile.is_construction_worker is None:
            missing_fields.append("occupation")
        if session.profile.is_bocw_registered is None:
            missing_fields.append("bocw_registration")
        if session.profile.accident_occurred_at_work is None:
            missing_fields.append("workplace_accident")

        return ConversationalResponse(
            session_id=session.session_id,
            language=lang,
            response_text=response_text,
            current_step=session.step,
            is_emergency=injury_guidance.is_emergency,
            schemes_evaluated=evaluated_schemes,
            checklist=checklist,
            injury_guidance=injury_guidance,
            missing_fields=missing_fields
        )

    def _compose_response(
        self,
        session: UserSession,
        raw_text: str,
        injury_guidance,
        schemes,
        checklist: DocumentChecklist
    ) -> str:
        """Composes structured, empathetic bilingual response."""
        p = session.profile
        is_ta = (session.language == Language.TA)

        parts: list[str] = []

        # 1. Emergency Banner if applicable
        if injury_guidance.is_emergency:
            parts.append(injury_guidance.emergency_message_ta if is_ta else injury_guidance.emergency_message_en)
            parts.append("\n---\n")

        # 2. Empathetic Greeting & Intake Progress
        if is_ta:
            greeting = "வணக்கம்! நான் ஹக்கு ஏஐ (HakkuAI) - தொழிலாளர் நல வழிகாட்டி.\n"
            if p.accident_occurred_at_work or p.injury_severity:
                greeting += "பணியிடத்தில் உங்களுக்கு காயம் ஏற்பட்டதற்கு வருந்துகிறேன். உங்களுக்கு உதவ தேவையான அரசு நலத்திட்டங்கள் மற்றும் இழப்பீட்டு வழிகளைப் பார்ப்போம்.\n"
        else:
            greeting = "Hello! I am HakkuAI — Government Welfare Assistant for Indian Workers.\n"
            if p.accident_occurred_at_work or p.injury_severity:
                greeting += "I am sorry to hear about your workplace injury. Let us look at the legal compensation pathways and government welfare options available for you.\n"
        parts.append(greeting)

        # 3. Known Profile Summary
        known_items = []
        if p.state:
            known_items.append(f"• State: {p.state}" if not is_ta else f"• மாநிலம்: {p.state}")
        if p.is_construction_worker is not None:
            known_items.append(f"• Construction Worker: {'Yes' if p.is_construction_worker else 'No'}" if not is_ta else f"• கட்டுமானத் தொழிலாளி: {'ஆம்' if p.is_construction_worker else 'இல்லை'}")
        if p.is_bocw_registered is not None:
            reg_str = "Registered" if p.is_bocw_registered else "Unregistered / Membership Pending"
            reg_ta = "பதிவு செய்யப்பட்டுள்ளது" if p.is_bocw_registered else "பதிவு செய்யப்படவில்லை / விவரம் நிலுவை"
            known_items.append(f"• BOCW Board Registration: {reg_str}" if not is_ta else f"• நல வாரியப் பதிவு: {reg_ta}")

        if known_items:
            summary_title = "📋 **Your Recorded Profile Details**:" if not is_ta else "📋 **பதிவு செய்யப்பட்ட விவரங்கள்**:"
            parts.append(summary_title + "\n" + "\n".join(known_items))

        # 4. Potentially Relevant Welfare Schemes
        parts.append("\n🏛️ **" + ("பொருந்தக்கூடிய அரசு நலத்திட்டங்கள் மற்றும் சட்டப்படியான இழப்பீடு" if is_ta else "Identified Welfare Schemes & Statutory Compensation") + "**:")

        for s in schemes:
            badge = f"[{s.status.value}]"
            name = s.tamil_name if is_ta else s.scheme_name
            expl = s.explanation_ta if is_ta else s.explanation_en
            source_info = SourceManager.format_citation(
                title=s.scheme_name,
                url=s.official_source_url,
                authority="Government Authority",
                verified_date="2024-10-15"
            )

            scheme_block = (
                f"\n### {name} {badge}\n"
                f"• **{'விளக்கம்' if is_ta else 'Assessment'}**: {expl}\n"
                f"• **{'உதவித் தொகை / பலன்' if is_ta else 'Benefit Limits'}**: {s.benefit_limits}\n"
                f"{source_info}\n"
            )

            if s.missing_information:
                missing_str = ", ".join(s.missing_information)
                scheme_block += f"• **{'தேவைப்படும் கூடுதல் தகவல்' if is_ta else 'Pending Information'}**: {missing_str}\n"

            parts.append(scheme_block)

        # 5. Guidance for Unregistered Workers if relevant
        if p.is_bocw_registered is False:
            parts.append("\n" + (injury_guidance.unregistered_worker_guidance_ta if is_ta else injury_guidance.unregistered_worker_guidance_en))

        # 6. Document Checklist & Evidence Preservation
        parts.append("\n📄 **" + ("தேவைப்படும் முக்கிய ஆவணங்கள் மற்றும் மாற்று ஆதாரங்கள்" if is_ta else "Personalized Document Checklist & Fallback Evidence") + "**:")
        parts.append(checklist.summary_ta if is_ta else checklist.summary_en)

        for doc in checklist.items[:4]: # show primary top 4 documents
            d_name = doc.name_ta if is_ta else doc.name_en
            d_purpose = doc.purpose_ta if is_ta else doc.purpose_en
            d_alt = doc.alternative_evidence_ta if is_ta else doc.alternative_evidence_en
            status_symbol = "✅" if doc.status == DocumentStatus.AVAILABLE else ("⚠️" if doc.status == DocumentStatus.MISSING else "ℹ️")

            parts.append(
                f"\n{status_symbol} **{d_name}** [{doc.status.value}]\n"
                f"   - {'நோக்கம்' if is_ta else 'Why Needed'}: {d_purpose}\n"
                f"   - {'ஆவணம் இல்லையெனில் மாற்று வழி' if is_ta else 'Alternative if Missing'}: {d_alt}"
            )

        # 7. Next Steps & Progressive Intake Prompt
        parts.append("\n🚀 **" + ("அடுத்த கட்ட நடவடிக்கைகள்" if is_ta else "Recommended Next Steps") + "**:")
        steps = injury_guidance.next_steps_ta if is_ta else injury_guidance.next_steps_en
        for step in steps[:3]:
            parts.append(f"• {step}")

        # Targeted follow-up question
        next_q = ""
        if p.state is None:
            next_q = "\n❓ எந்த மாநிலத்தில் நீங்கள் வசிக்கிறீர்கள் அல்லது பணிபுரிகிறீர்கள்? (உதாரணம்: தமிழ்நாடு, கர்நாடகா)" if is_ta else "\n❓ Which state do you live or work in? (e.g., Tamil Nadu, Karnataka)"
        elif p.is_bocw_registered is None:
            next_q = "\n❓ நீங்கள் உங்கள் மாநில கட்டுமான தொழிலாளர்கள் நல வாரியத்தில் (BOCW Welfare Board) பதிவு செய்துள்ளீர்களா? (ஆம் / இல்லை / தெரியாது)" if is_ta else "\n❓ Are you registered with your State Construction Workers Welfare Board? (Yes / No / Not sure)"
        elif p.hospital_treatment_received is None:
            next_q = "\n❓ மருத்துவமனையில் சிகிச்சை பெற்றீர்களா? உங்களிடம் சிகிச்சை வெளியேற்ற அறிக்கை (Discharge Summary) அல்லது ரசீதுகள் உள்ளதா?" if is_ta else "\n❓ Did you receive hospital treatment? Do you have a hospital discharge summary or medical bills?"
        elif not p.available_documents:
            next_q = "\n❓ தற்போது உங்களிடம் உள்ள ஆவணங்கள் என்னென்ன? (ஆதார், வங்கி பாஸ்புக், மருத்துவ ரசீதுகள், வாரிய அட்டை)" if is_ta else "\n❓ Which documents do you currently have readily available with you? (e.g. Aadhaar, Bank passbook, medical reports)"

        if next_q:
            parts.append(next_q)

        # 8. Honest Disclaimer
        parts.append("\n---\n*ℹ️ " + (injury_guidance.disclaimer_ta if is_ta else injury_guidance.disclaimer_en) + "*")

        return "\n".join(parts)
