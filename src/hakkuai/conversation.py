"""
Conversational Engine and Session Manager for HakkuAI.
Maintains isolated worker sessions, implements progressive intake,
detects language (English & Tamil), extracts profile attributes,
manages persistent document state, routes conversational intents,
and provides context-aware, non-repetitive follow-up answers.
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
    DocumentChecklist,
    SchemeEligibilityResult
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
        
        # Persistent state flags for conversational continuity & non-repetition
        self.has_assessed: bool = False
        self.document_statuses: dict[str, DocumentStatus] = {}
        self.last_schemes_evaluated: list[SchemeEligibilityResult] = []
        self.last_intent: str = ""

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
    """Core conversational engine with intent routing and non-repetitive follow-ups."""

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
    def extract_profile_updates(text: str, session: UserSession) -> bool:
        """
        Progressively extracts worker attributes and explicit document states.
        Returns True if a material change occurred in core eligibility attributes
        (e.g., state, occupation, or registration status changes).
        """
        profile = session.profile
        t = text.lower()
        material_change = False

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
                if profile.state != standard:
                    material_change = True
                profile.state = standard
                break

        # 2. Occupation detection
        if any(w in t for w in ["construction", "building", "mason", "carpenter", "painter", "welder", "site worker", "கூலி", "கட்டுமானம்", "மேஸ்திரி", "கொத்தனார்", "கட்டுமானத் தொழிலாளி"]):
            if profile.is_construction_worker is not True:
                material_change = True
            profile.is_construction_worker = True
            profile.occupation = "Construction Worker"

        # 3. Registration detection - check negative conditions first
        negative_reg_terms = [
            "never registered", "unregistered", "not registered", "didn't register",
            "did not register", "no card", "have not registered", "not yet registered",
            "un-registered", "non-registered", "பதிவு செய்யவில்லை", "அட்டை இல்லை"
        ]
        if any(w in t for w in negative_reg_terms):
            if profile.is_bocw_registered is not False:
                material_change = True
            profile.is_bocw_registered = False
            session.document_statuses["doc_bocw_card"] = DocumentStatus.MISSING
            if "bocw_card" in profile.available_documents:
                profile.available_documents.remove("bocw_card")
        elif re.search(r"\b(registered|have bocw|have card|welfare board member|member)\b", t) or any(w in t for w in ["பதிவு செய்துள்ளேன்", "அட்டை உள்ளது", "உறுப்பினர்"]):
            if profile.is_bocw_registered is not True:
                material_change = True
            profile.is_bocw_registered = True
            session.document_statuses["doc_bocw_card"] = DocumentStatus.AVAILABLE
            if "bocw_card" not in profile.available_documents:
                profile.available_documents.append("bocw_card")

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

        # 8. Persistent Document State Management with Strict Positive/Negative Disambiguation
        # A) Hospital Discharge Summary:
        discharge_neg_patterns = [
            r"\b(no|don't have|do not have|haven't got|didn't get|without|missing|lacks?)\b.*\b(discharge summary|discharge paper|hospital paper|medical report|discharge)\b",
            r"\b(discharge summary|discharge paper|hospital paper)\b.*\b(not available|missing|illai|illaiye|இல்லை|இல்ல)\b",
            r"\b(no|not have)\b.*\bdischarge\b",
            r"\bடிஸ்சார்ஜ் இல்லை\b",
            r"\bமருத்துவ அறிக்கை இல்லை\b"
        ]
        discharge_pos_patterns = [
            r"\b(have|got|obtained|available)\b.*\b(discharge summary|discharge paper|hospital paper)\b",
            r"\b(discharge summary|discharge)\b.*\b(உள்ளது|இருக்கு|வைத்திருக்கிறேன்)\b"
        ]
        if any(re.search(pat, t) for pat in discharge_neg_patterns) or (("discharge" in t or "summary" in t) and any(neg in t for neg in ["no", "don't", "do not", "without", "missing", "இல்லை", "இல்ல"])):
            session.document_statuses["doc_hospital_discharge"] = DocumentStatus.MISSING
            if "hospital_discharge" in profile.available_documents:
                profile.available_documents.remove("hospital_discharge")
        elif any(re.search(pat, t) for pat in discharge_pos_patterns):
            session.document_statuses["doc_hospital_discharge"] = DocumentStatus.AVAILABLE
            if "hospital_discharge" not in profile.available_documents:
                profile.available_documents.append("hospital_discharge")

        # B) Aadhaar card:
        if any(w in t for w in ["no aadhaar", "don't have aadhaar", "aadhaar missing", "without aadhaar", "ஆதார் இல்லை"]):
            session.document_statuses["doc_identity_aadhaar"] = DocumentStatus.MISSING
            if "aadhaar" in profile.available_documents:
                profile.available_documents.remove("aadhaar")
        elif any(w in t for w in ["have aadhaar", "have my aadhaar", "aadhaar card", "with aadhaar", "got aadhaar", "ஆதார் உள்ளது", "ஆதார் அட்டை"]):
            if not any(neg in t for neg in ["no aadhaar", "don't have aadhaar", "without aadhaar"]):
                session.document_statuses["doc_identity_aadhaar"] = DocumentStatus.AVAILABLE
                if "aadhaar" not in profile.available_documents:
                    profile.available_documents.append("aadhaar")

        # C) Bank passbook:
        if any(w in t for w in ["no bank", "no passbook", "don't have bank", "don't have passbook", "பாஸ்புக் இல்லை", "வங்கி கணக்கு இல்லை"]):
            session.document_statuses["doc_bank_passbook"] = DocumentStatus.MISSING
            if "bank_passbook" in profile.available_documents:
                profile.available_documents.remove("bank_passbook")
        elif any(w in t for w in ["have passbook", "have my passbook", "bank passbook", "bank account", "வங்கி பாஸ்புக்", "வங்கி"]):
            if not any(neg in t for neg in ["no passbook", "don't have passbook", "no bank"]):
                session.document_statuses["doc_bank_passbook"] = DocumentStatus.AVAILABLE
                if "bank_passbook" not in profile.available_documents:
                    profile.available_documents.append("bank_passbook")

        # D) Disability Certificate:
        if any(w in t for w in ["no disability certificate", "don't have disability certificate", "சான்றிதழ் இல்லை"]):
            session.document_statuses["doc_disability_certificate"] = DocumentStatus.MISSING
        elif any(w in t for w in ["have disability certificate", "got disability certificate", "மாற்றுத்திறனாளி சான்றிதழ் உள்ளது"]):
            session.document_statuses["doc_disability_certificate"] = DocumentStatus.AVAILABLE

        # E) Employment Proof:
        if any(w in t for w in ["no employment proof", "contractor refused", "no wage slip", "no proof", "ஆதாரம் இல்லை"]):
            session.document_statuses["doc_employment_proof"] = DocumentStatus.MISSING
        elif any(w in t for w in ["have wage slip", "have salary slip", "have work proof", "muster roll available"]):
            session.document_statuses["doc_employment_proof"] = DocumentStatus.AVAILABLE

        return material_change

    @staticmethod
    def classify_intent(text: str, session: UserSession, material_change: bool = False) -> str:
        """
        Classifies user intent to determine whether to execute a full initial assessment
        or provide a focused, context-aware direct follow-up answer.
        """
        t = text.lower()

        # 1. Reassessment requested or material change in core profile
        if material_change:
            return "INTENT_REASSESSMENT"

        reassess_patterns = [
            r"\b(check again|reassess|re-assess|repeat assessment|refresh assessment|show assessment again|show schemes again|recalculate|full report|run assessment again)\b",
            r"\b(மீண்டும் சரிபார்க்க|மீண்டும் காட்டு|அனைத்து திட்டங்கள்)\b"
        ]
        if any(re.search(pat, t) for pat in reassess_patterns):
            return "INTENT_REASSESSMENT"

        # 2. Missing documents intent (specifically matches missing discharge summary, missing cards, etc.)
        missing_doc_patterns = [
            r"\b(no|don't have|do not have|haven't got|didn't get|missing|without|where to get|how to get|what if i don't have|lacks?)\b.*\b(discharge summary|discharge|medical records?|papers?|bills?|card|passbook|certificate|evidence|proof)\b",
            r"\b(discharge summary|discharge|medical papers?|hospital records?|bocw card|passbook)\b.*\b(missing|not available|what should i do|what to do)\b",
            r"\b(what should i do|what to do|what next|alternative)\b.*\b(discharge|summary|bills?|card|documents?)\b",
            r"\b(இல்லை|இல்ல|சான்றிதழ் இல்லை|டிஸ்சார்ஜ் இல்லை)\b"
        ]
        if any(re.search(pat, t) for pat in missing_doc_patterns):
            return "INTENT_MISSING_DOCUMENT"

        # 3. Application procedure / office inquiry
        app_step_patterns = [
            r"\b(how to apply|where to apply|where do i go|where should i go|which office|application process|portal|whom to contact|how do i claim)\b",
            r"\b(எப்படி விண்ணப்பிப்பது|எங்கு செல்ல வேண்டும்|எந்த அலுவலகம்)\b"
        ]
        if any(re.search(pat, t) for pat in app_step_patterns):
            return "INTENT_APPLICATION_STEPS"

        # 4. Eligibility or compensation clarification
        eligibility_patterns = [
            r"\b(how much|benefit amount|am i eligible|why not eligible|will employer pay|statutory compensation|compensation amount|how much money)\b",
            r"\b(எவ்வளவு தொகை|இழப்பீடு கிடைக்குமா|முதலாளி தருவாரா)\b"
        ]
        if any(re.search(pat, t) for pat in eligibility_patterns):
            return "INTENT_ELIGIBILITY_CLARIFICATION"

        # 5. General follow-up
        return "INTENT_GENERAL_FOLLOWUP"

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

        # Extract profile updates and document status changes
        material_change = self.extract_profile_updates(raw_text, session)

        # Classify conversational intent
        intent = self.classify_intent(raw_text, session, material_change)
        session.last_intent = intent

        # Record history
        session.history.append({"role": "user", "text": raw_text})

        # 1. Evaluate injury guidance (including 112 emergency check)
        injury_guidance = evaluate_injury_workflow(session.profile, raw_user_text=raw_text)

        # 2. Evaluate eligibility across schemes
        evaluated_schemes = assess_worker_eligibility(session.profile, db=scheme_db)
        session.last_schemes_evaluated = evaluated_schemes

        # 3. Generate personalized checklist using persistent per-session statuses
        checklist = generate_document_checklist(
            session.profile,
            language=lang,
            explicit_statuses=session.document_statuses
        )

        # 4. Formulate response:
        # If this is the first turn OR user requested a full reassessment -> compose full initial assessment.
        # Otherwise -> provide a focused, context-aware direct follow-up without repetitive output!
        if not session.has_assessed or intent == "INTENT_REASSESSMENT":
            response_text = self._compose_full_assessment_response(
                session=session,
                raw_text=raw_text,
                injury_guidance=injury_guidance,
                schemes=evaluated_schemes,
                checklist=checklist
            )
            session.has_assessed = True
        else:
            response_text = self._compose_followup_response(
                session=session,
                raw_text=raw_text,
                intent=intent,
                injury_guidance=injury_guidance,
                schemes=evaluated_schemes,
                checklist=checklist
            )

        session.history.append({"role": "assistant", "text": response_text})

        # Find remaining missing fields
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

    def _compose_full_assessment_response(
        self,
        session: UserSession,
        raw_text: str,
        injury_guidance,
        schemes,
        checklist: DocumentChecklist
    ) -> str:
        """Composes complete initial assessment report (used on turn 1 or explicit reassessment)."""
        p = session.profile
        is_ta = (session.language == Language.TA)
        parts: list[str] = []

        # 1. Emergency Banner if applicable
        if injury_guidance.is_emergency:
            parts.append(injury_guidance.emergency_message_ta if is_ta else injury_guidance.emergency_message_en)
            parts.append("\n---\n")

        # 2. Empathetic Greeting
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

        for doc in checklist.items[:4]:
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

        # Targeted single follow-up question
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

        parts.append("\n---\n*ℹ️ " + (injury_guidance.disclaimer_ta if is_ta else injury_guidance.disclaimer_en) + "*")
        return "\n".join(parts)

    def _compose_followup_response(
        self,
        session: UserSession,
        raw_text: str,
        intent: str,
        injury_guidance,
        schemes,
        checklist: DocumentChecklist
    ) -> str:
        """
        Composes focused, context-aware direct follow-up answers.
        Avoids repeating greetings, entire scheme listings, citations, or legal disclaimers.
        """
        is_ta = (session.language == Language.TA)

        # 1. Missing Document Follow-up (e.g., Discharge Summary missing)
        if intent == "INTENT_MISSING_DOCUMENT":
            return self._compose_missing_document_answer(session, raw_text, checklist)

        # 2. Application Steps Follow-up (where to go, how to apply)
        elif intent == "INTENT_APPLICATION_STEPS":
            return self._compose_application_steps_answer(session, raw_text, checklist)

        # 3. Eligibility & Compensation Clarification Follow-up
        elif intent == "INTENT_ELIGIBILITY_CLARIFICATION":
            return self._compose_eligibility_clarification_answer(session, raw_text, checklist)

        # 4. General Follow-up
        else:
            return self._compose_general_followup_answer(session, raw_text, checklist)

    def _compose_missing_document_answer(
        self,
        session: UserSession,
        raw_text: str,
        checklist: DocumentChecklist
    ) -> str:
        """Specific guidance when a worker is missing a discharge summary or medical documents."""
        is_ta = (session.language == Language.TA)

        # Calculate actual counts dynamically
        available_count = sum(1 for i in checklist.items if i.status == DocumentStatus.AVAILABLE)
        missing_count = sum(1 for i in checklist.items if i.status == DocumentStatus.MISSING)

        if is_ta:
            return (
                "மருத்துவமனை வெளியேற்றச் சான்றிதழ் (Discharge Summary) உங்களிடம் இல்லை என்பதைப் புரிந்துகொள்கிறேன். "
                "சான்றிதழ் இல்லை என்பதற்காகவே நீங்கள் இழப்பீடு பெற தகுதியற்றவர் ஆகிவிட மாட்டீர்கள்.\n\n"
                "**நீங்கள் செய்ய வேண்டிய நடைமுறை நடவடிக்கைகள்**:\n"
                "1. **மருத்துவமனை/சிகிச்சையகத்தை அணுகுதல்**: நீங்கள் சிகிச்சை பெற்ற மருத்துவமனையின் பதிவேட்டுப் பிரிவை (Medical Records Department) அல்லது தலைமை மருத்துவரை அணுகி, உங்கள் சிகிச்சை விவரக் குறிப்பு அல்லது விபத்துக் காயம் குறித்த சிகிச்சைச் சான்றிதழைப் (Treatment Certificate) பெறலாம்.\n"
                "2. **வெளிநோயாளி (OPD) சிகிச்சை முறை**: நீங்கள் மருத்துவமனையில் தங்கி சிகிச்சை பெறாமல் (Outpatient) அன்றுமட்டுமே சிகிச்சை பெற்றிருந்தால், பொதுவாக Discharge Summary வழங்கப்படாது. அந்தச் சூழலில், அவசர சிகிச்சைப் பிரிவு சீட்டு (Casualty Card) அல்லது மருத்துவர் வழங்கிய காயம் குறித்த சிகிச்சைச் சீட்டையே போதுமான ஆவணமாகப் பயன்படுத்தலாம்.\n"
                "3. **பிற மருத்துவ ஆதாரங்களைப் பாதுகாத்தல்**: மருந்து வாங்கிய அசல் ரசீதுகள், எக்ஸ்-ரே / ஸ்கேன் அறிக்கைகள் மற்றும் மருத்துவரின் பரிந்துரைச் சீட்டுகளைக் கட்டாயம் பத்திரமாக வைத்துக்கொள்ளுங்கள்.\n"
                "4. **சம்பந்தப்பட்ட அதிகாரியிடம் சரிபார்த்தல்**: நல வாரிய நிவாரணத்திற்கு அரசு மருத்துவரின் சான்றிதழும், பணியாளர் இழப்பீட்டுச் சட்டம் 1923-ன் கீழ் முதலாளி இழப்பீட்டிற்கு நீதிமன்றத்தில் சமர்ப்பிக்கக்கூடிய மருத்துவ அறிக்கைகளும் மாற்று ஆதாரங்களாக ஏற்றுக்கொள்ளப்படும்.\n\n"
                f"📋 **ஆவணங்கள் தயார் நிலை**: {available_count} தயார், {missing_count} தேவைப்படுகிறது.\n"
                "• மருத்துவமனை வெளியேற்றச் சான்றிதழ்: ⚠️ [தேவைப்படுகிறது / Missing]\n\n"
                "❓ நீங்கள் எந்த மருத்துவமனையில் சிகிச்சை பெற்றீர்கள்? அங்கு உள்நோயாளியாக (அட்மிட் ஆகி) இருந்தீர்களா அல்லது வெளிநோயாளியாக (OPD) சிகிச்சை பெற்றீர்களா?"
            )
        else:
            return (
                "Thank you for clarifying. Not having a hospital discharge summary is very common, and it **does NOT automatically disqualify you** from receiving compensation or welfare assistance.\n\n"
                "**Practical Steps on What You Should Do**:\n"
                "1. **Request Records from the Hospital/Clinic**: Visit the hospital or primary health centre (PHC) where you were treated. Approach the Medical Records Department (MRD) or the treating doctor and request a duplicate case sheet summary or an official **Injury / Treatment Certificate**.\n"
                "2. **If You Received Outpatient (OPD) Care**: If you were treated in casualty or as an outpatient without overnight admission, hospitals do not issue formal discharge summaries. In this case, your **Emergency Casualty Card, Outpatient (OPD) Ticket, or Doctor's Prescription with injury notes** serves as valid alternative medical proof.\n"
                "3. **Preserve All Prescriptions & Bills**: Retain all pharmacy purchase receipts, diagnostic X-ray/scan reports, clinical test results, and doctor memos. These substantiate medical expenditure and the severity of injuries.\n"
                "4. **Verification with the Relevant Authority**: Acceptable fallback evidence depends on the specific claim: for the BOCW Welfare Board, the District Labour Officer can accept a Government Doctor's injury certificate; for statutory claims under the Employees' Compensation Act 1923, the Labour Court evaluates any credible clinical treatment proof.\n\n"
                f"📋 **Document Readiness Update**: {available_count} available, {missing_count} missing or requiring alternative evidence.\n"
                "• Hospital Discharge Summary is now marked as ⚠️ **[Missing]**.\n\n"
                "❓ Which hospital or clinic treated you, and was your treatment inpatient (admitted overnight) or outpatient (OPD)?"
            )

    def _compose_application_steps_answer(
        self,
        session: UserSession,
        raw_text: str,
        checklist: DocumentChecklist
    ) -> str:
        """Step-by-step guidance on application offices and procedures."""
        is_ta = (session.language == Language.TA)
        state_str = session.profile.state or "your state"

        if is_ta:
            return (
                f"விண்ணப்பிக்கும் வழிமுறைகள் மற்றும் அணுக வேண்டிய அலுவலகங்கள் ({state_str}):\n\n"
                "1. **மாவட்ட தொழிலாளர் நல அலுவலர்**: உங்கள் மாவட்ட தொழிலாளர் அலுவலர் (சமூக பாதுகாப்பு திட்டம்) அலுவலகம் அல்லது அருகில் உள்ள அரசு இ-சேவை மையத்தை (CSC) அணுகி நல வாரிய நிவாரண விண்ணப்பத்தைப் பெறவும்.\n"
                "2. **முதலாளிக்கு எழுத்துப்பூர்வ அறிவிப்பு**: விபத்து விவரங்களைக் குறிப்பிட்டு இழப்பீடு கோரி ஒப்பந்ததாரர் அல்லது முதலாளிக்கு எழுத்துப்பூர்வ கடிதம் அனுப்பவும்.\n"
                "3. **தொழிலாளர் நீதிமன்றம் / சட்ட உதவி**: முதலாளி இழப்பீடு தர மறுத்தால், மாவட்ட சட்டப்பணிகள் ஆணைக்குழுவை (DLSA) அணுகி இலவச சட்ட உதவி மூலம் தொழிலாளர் ஆணையரிடம் மனு தாக்கல் செய்யலாம்.\n\n"
                "❓ தற்போது உங்களிடம் ஆதார் அட்டை மற்றும் வங்கி பாஸ்புக் உள்ளதா?"
            )
        else:
            return (
                f"Here are the specific application steps and offices to approach in {state_str}:\n\n"
                "1. **District Labour Office / Common Service Centre (CSC)**: Visit the District Labour Officer (Social Security Scheme) or your nearest government e-Sevai / CSC centre to submit the BOCW accident claim form.\n"
                "2. **Written Notice of Accident to Employer**: Deliver a written accident notice to your contractor/employer detailing the accident date, site, and injury requesting statutory compensation.\n"
                "3. **Commissioner for Employees' Compensation**: If the employer denies compensation, approach the District Labour Court (Commissioner for Employees' Compensation). You can receive free legal counsel from the District Legal Services Authority (DLSA).\n\n"
                "❓ Do you currently have your Aadhaar card and Bank Passbook ready with you?"
            )

    def _compose_eligibility_clarification_answer(
        self,
        session: UserSession,
        raw_text: str,
        checklist: DocumentChecklist
    ) -> str:
        """Direct explanation of benefit amounts and eligibility rules without re-dumping everything."""
        is_ta = (session.language == Language.TA)

        if is_ta:
            return (
                "இழப்பீடு மற்றும் நலத்திட்டத் தொகை விவரங்கள்:\n\n"
                "• **கட்டுமான நல வாரிய நிவாரணம்**: விபத்து மரணத்திற்கு ₹5,00,000; நிரந்தர முழு ஊனத்திற்கு ₹1,00,000 முதல் ₹2,00,000 வரை; தீவிர காய சிகிச்சைக்கு ₹10,000 முதல் ₹25,000 வரை.\n"
                "• **பணியாளர் இழப்பீட்டுச் சட்டம் 1923**: தொழிலாளி வாரியத்தில் பதிவு செய்யப்படாவிட்டாலும், முதலாளி சட்டபூர்வமாக இழப்பீடு வழங்க வேண்டும் (ஊனம் மற்றும் வயதின் அடிப்படையில் கணக்கிடப்படும்).\n\n"
                "❓ உங்கள் காயத்தால் எத்தனை நாட்கள் வேலைக்குச் செல்ல முடியாத நிலை ஏற்பட்டுள்ளது?"
            )
        else:
            return (
                "Key Benefit & Compensation Limits Summary:\n\n"
                "• **State BOCW Welfare Relief**: Up to ₹5,00,000 for accidental death; ₹1,00,000 - ₹2,00,000 for permanent total disability; ₹10,000 - ₹25,000 for grievous injury hospitalization.\n"
                "• **Employees' Compensation Act, 1923 (Statutory Employer Liability)**: Applies even if you are not registered with the welfare board. Compensation is calculated based on 60% of monthly wages multiplied by age factor.\n"
                "• **Ayushman Bharat (AB-PMJAY)**: Up to ₹5,00,000/year for cashless inpatient hospitalization.\n\n"
                "❓ How many days or weeks have you been unable to work due to this injury?"
            )

    def _compose_general_followup_answer(
        self,
        session: UserSession,
        raw_text: str,
        checklist: DocumentChecklist
    ) -> str:
        """General non-repetitive conversational response."""
        is_ta = (session.language == Language.TA)
        available_count = sum(1 for i in checklist.items if i.status == DocumentStatus.AVAILABLE)
        missing_count = sum(1 for i in checklist.items if i.status == DocumentStatus.MISSING)

        if is_ta:
            return (
                f"உங்கள் தகவல் பதிவு செய்யப்பட்டுள்ளது. தற்போது ஆவணங்கள் நிலை: {available_count} தயார், {missing_count} தேவைப்படுகிறது.\n\n"
                "அடுத்த கட்ட நடவடிக்கையாக ஆவணங்களை சேகரித்து தொழிலாளர் நல அலுவலரை அணுகலாம்.\n"
                "❓ உங்களுக்கு வேறு ஏதேனும் சந்தேகம் உள்ளதா?"
            )
        else:
            return (
                f"Your details have been updated. Document status: {available_count} available, {missing_count} pending.\n\n"
                "We can proceed with preparing your application for the District Labour Office.\n"
                "❓ Do you have any specific question about your workplace accident or next steps?"
            )
