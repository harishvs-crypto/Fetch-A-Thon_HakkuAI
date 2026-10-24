"""
Agent Communication Protocol (ACP) & Agent Chat Protocol Implementation.
Integrates with Fetch.ai / ASI ecosystem via official uagents protocols.
Supports both standard AgentChatProtocol (used by ASI:One) and structured
Welfare RPC protocols for direct agent-to-agent communication.
"""

from datetime import datetime, timezone
from uuid import uuid4
from uagents import Context, Protocol, Model
from uagents_core.contrib.protocols.chat import (
    ChatMessage,
    ChatAcknowledgement,
    TextContent,
    chat_protocol_spec,
)
from hakkuai.conversation import ConversationEngine
from hakkuai.logging_config import logger
from hakkuai.schemas import WorkerProfile, InjurySeverity, Language

# Initialize conversation engine
conversation_engine = ConversationEngine()

# ---------------------------------------------------------------------------
# 1. Standard Official Agent Chat Protocol (ACP) for ASI:One & Agentverse
# ---------------------------------------------------------------------------
chat_proto = Protocol(spec=chat_protocol_spec)

@chat_proto.on_message(ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    """
    Handles incoming chat messages from ASI:One, users, or other agents
    using the official Agent Chat Protocol (ACP).
    """
    ctx.logger.info(f"ACP ChatMessage received from {sender} (msg_id: {msg.msg_id})")

    # Step 1: Send protocol acknowledgement receipt
    try:
        ack = ChatAcknowledgement(
            timestamp=datetime.now(timezone.utc),
            acknowledged_msg_id=msg.msg_id
        )
        await ctx.send(sender, ack)
        ctx.logger.debug(f"Dispatched ChatAcknowledgement for {msg.msg_id}")
    except Exception as e:
        ctx.logger.warning(f"Failed to send ChatAcknowledgement: {e}")

    # Step 2: Extract text content from message blocks
    incoming_text = ""
    for content_item in msg.content:
        if isinstance(content_item, TextContent):
            incoming_text += content_item.text + " "

    incoming_text = incoming_text.strip()
    if not incoming_text:
        incoming_text = "Hello"

    # Step 3: Process through HakkuAI conversational engine
    try:
        conv_resp = conversation_engine.process_message(sender=sender, text=incoming_text)
        response_text = conv_resp.response_text
    except Exception as err:
        ctx.logger.error(f"Error processing message from {sender}: {err}")
        response_text = (
            "I encountered a technical processing error. Please restate your situation, "
            "including your state, occupation, and whether you experienced a workplace injury."
        )

    # Step 4: Transmit structured response ChatMessage
    reply_msg = ChatMessage(
        timestamp=datetime.now(timezone.utc),
        msg_id=uuid4(),
        content=[TextContent(type="text", text=response_text)]
    )
    await ctx.send(sender, reply_msg)
    ctx.logger.info(f"Dispatched ACP response to {sender} (length: {len(response_text)} chars)")

@chat_proto.on_message(ChatAcknowledgement)
async def handle_chat_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    """Handles delivery acknowledgements received from peer agents or clients."""
    ctx.logger.debug(f"Received delivery acknowledgement from {sender} for {msg.acknowledged_msg_id}")


# ---------------------------------------------------------------------------
# 2. Structured Agent-to-Agent Welfare RPC Protocol
# ---------------------------------------------------------------------------
class WelfareAssessmentRequest(Model):
    """Structured RPC model for direct inter-agent welfare requests."""
    state: str | None = None
    occupation: str | None = None
    is_construction_worker: bool | None = None
    is_bocw_registered: bool | None = None
    accident_occurred_at_work: bool | None = None
    injury_severity: str | None = None # e.g. "severe", "minor", "critical"
    hospital_treatment: bool | None = None
    language: str = "en"
    raw_query: str | None = None

class SchemeSummaryModel(Model):
    scheme_id: str
    name: str
    status: str
    benefit_limits: str
    official_source_url: str
    explanation: str

class WelfareAssessmentResponse(Model):
    """Structured RPC model returned to peer agents."""
    session_id: str
    is_emergency: bool
    status_summary: str
    schemes: list[SchemeSummaryModel]
    recommended_next_step: str
    disclaimer: str

welfare_rpc_proto = Protocol(name="HakkuWelfareRPC", version="1.0.0")

@welfare_rpc_proto.on_message(WelfareAssessmentRequest, replies={WelfareAssessmentResponse})
async def handle_welfare_rpc(ctx: Context, sender: str, msg: WelfareAssessmentRequest):
    """
    Handles structured programmatic queries from other Fetch.ai agents.
    """
    ctx.logger.info(f"Received WelfareAssessmentRequest from {sender}")
    
    # Map request into WorkerProfile
    profile = WorkerProfile(
        state=msg.state,
        occupation=msg.occupation,
        is_construction_worker=msg.is_construction_worker,
        is_bocw_registered=msg.is_bocw_registered,
        accident_occurred_at_work=msg.accident_occurred_at_work,
        hospital_treatment_received=msg.hospital_treatment,
        preferred_language=Language.TA if msg.language == "ta" else Language.EN
    )
    if msg.injury_severity:
        try:
            profile.injury_severity = InjurySeverity(msg.injury_severity.lower())
        except ValueError:
            pass

    # If raw_query was provided, update profile progressively
    if msg.raw_query:
        conversation_engine.extract_profile_updates(msg.raw_query, profile)

    session = conversation_engine.session_manager.get_or_create_session(sender)
    session.profile = profile

    # Evaluate guidance & schemes
    from hakkuai.eligibility import assess_worker_eligibility
    from hakkuai.injury_workflow import evaluate_injury_workflow

    injury_guidance = evaluate_injury_workflow(profile, raw_user_text=msg.raw_query or "")
    schemes_res = assess_worker_eligibility(profile)

    scheme_models = [
        SchemeSummaryModel(
            scheme_id=s.scheme_id,
            name=s.tamil_name if profile.preferred_language == Language.TA else s.scheme_name,
            status=s.status.value,
            benefit_limits=s.benefit_limits,
            official_source_url=s.official_source_url,
            explanation=s.explanation_ta if profile.preferred_language == Language.TA else s.explanation_en
        )
        for s in schemes_res
    ]

    response = WelfareAssessmentResponse(
        session_id=session.session_id,
        is_emergency=injury_guidance.is_emergency,
        status_summary=f"Evaluated {len(schemes_res)} welfare pathways.",
        schemes=scheme_models,
        recommended_next_step=(
            injury_guidance.next_steps_ta[0] if profile.preferred_language == Language.TA 
            else injury_guidance.next_steps_en[0]
        ) if injury_guidance.next_steps_en else "Consult local labour welfare officer",
        disclaimer=(
            injury_guidance.disclaimer_ta if profile.preferred_language == Language.TA 
            else injury_guidance.disclaimer_en
        )
    )

    await ctx.send(sender, response)
    ctx.logger.info(f"Dispatched WelfareAssessmentResponse to {sender}")
