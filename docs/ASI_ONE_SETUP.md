# ASI:One Integration & Interaction Guide

HakkuAI is natively integrated with **ASI:One**, the Fetch.ai / Artificial Superintelligence Alliance conversational agent discovery interface.

Because HakkuAI implements the standard **Agent Chat Protocol (ACP v0.3.0)**, users and workers can converse with HakkuAI directly inside the ASI:One chat interface without requiring a custom web frontend.

---

## 1. How ASI:One Discovers HakkuAI

1. **Protocol Manifest Publishing**: HakkuAI publishes its `AgentChatProtocol` manifest to the Fetch.ai decentralized Almanac contract upon startup (`publish_manifest=True`).
2. **Indexing**: ASI:One queries the Almanac and indexes HakkuAI under categories such as *Government Welfare*, *Legal Aid*, *Worker Rights*, and *Disability Support*.
3. **Conversational Routing**: When an ASI:One user asks about workplace injuries, construction worker schemes, or BOCW benefits, ASI:One routes the message to HakkuAI's agent address.

---

## 2. Sample Conversational Prompts for ASI:One

### Scenario 1: English - Registered Construction Worker in Tamil Nadu
**Worker prompt in ASI:One**:
> *"I am a construction worker in Tamil Nadu. I injured my leg at work and cannot earn. I am registered with the welfare board."*

**HakkuAI's response in ASI:One**:
- Empathetic acknowledgment of workplace injury.
- Evaluates **Tamil Nadu BOCW Welfare Board Accident Relief Scheme** (`[Potentially eligible]`).
- Evaluates **Employees' Compensation Act, 1923** (`[Potentially eligible]`).
- Explains statutory benefit limits (up to ₹2,00,000 for disability / hospitalization relief).
- Provides personalized document checklist (TNBOCW card, medical discharge summary, bank passbook).
- Cites official government portal: `https://tnuwwb.tn.gov.in` (Verified Local Record).
- Outlines clear next step: Visit District Labour Officer or apply via TNUWWB portal.

---

### Scenario 2: English - Unregistered Worker with Employer Non-Cooperation
**Worker prompt in ASI:One**:
> *"I broke my arm at a building site in Chennai, but my contractor never registered me with any welfare board. What can I do?"*

**HakkuAI's response in ASI:One**:
- Clarifies that direct BOCW board relief requires registration (`[More information needed]`).
- Immediately highlights **Employees' Compensation Act 1923** (`[Potentially eligible]`): Explains that the contractor/employer has statutory legal liability to compensate injury regardless of board registration.
- Details alternative proof of employment (muster roll, supervisor WhatsApp chats, contractor vouchers, coworker affidavits).
- Details recourse through the Commissioner for Employees' Compensation (Labour Court).

---

### Scenario 3: Tamil (தமிழ்) - Bilingual Native Support
**Worker prompt in ASI:One**:
> *"வணக்கம், நான் தமிழ்நாட்டில் கட்டிட வேலை செய்கிறேன். வேலையில் எனக்கு விபத்து ஏற்பட்டு காலில் காயம் அடைந்துள்ளேன். எனக்கு உதவி கிடைக்குமா?"*

**HakkuAI's response in ASI:One**:
- Native Tamil response with patient, non-bureaucratic language.
- Explains தமிழ்நாடு கட்டுமானத் தொழிலாளர்கள் நல வாரிய நிவாரணத் திட்டம் மற்றும் பணியாளர் இழப்பீட்டுச் சட்டம் 1923.
- Outlines தேவையான முக்கிய ஆவணங்கள் மற்றும் மாற்று வழிகள்.
- Prompts for next necessary detail (e.g. whether the worker has a board registration card or hospital discharge summary).

---

### Scenario 4: Critical Trauma / Emergency Prioritization
**Worker prompt in ASI:One**:
> *"Emergency! My brother fell from the 3rd floor scaffolding, he is bleeding heavily and unconscious!"*

**HakkuAI's response in ASI:One**:
- Immediately triggers the **Emergency Medical Banner**:
  - Directs caller to dial **112** (National Emergency) or **108** (Ambulance).
  - Explicitly states that saving the patient's life comes first and welfare paperwork should wait until medical stabilization.

---

## 3. Platform Configuration & Permissions

When registering HakkuAI on Agentverse for ASI:One indexing:
1. Ensure the agent description clearly states:
   > *"HakkuAI is an autonomous welfare assistance agent for Indian workers, providing verified government scheme discovery, statutory compensation guidance under the Employees' Compensation Act 1923, and personalized document checklists."*
2. Ensure tags include: `welfare`, `india`, `workers`, `bocw`, `labor-rights`, `legal-aid`, `injury-assistance`.
3. Check that `AgentChatProtocol` (v0.3.0) is visible in the agent's published protocol list.
