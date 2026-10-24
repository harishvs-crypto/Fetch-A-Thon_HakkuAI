"""
Agent Communication Protocol (ACP) & Agent Chat Protocol Implementation.
Supports AgentChatProtocol, structured Welfare RPC, and Readiness RPC.
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
# 1. Standard Agent Chat Protocol
# ---------------------------------------------------------------------------

chat_proto = Protocol(spec=chat_protocol_spec)

# Store the original chat sender for each outstanding readiness request.
# This is suitable for a simple single-process example.
pending_readiness_requests: dict[str, str] = {}


@chat_proto.on_message(ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    """Handle incoming chat messages and optional readiness requests."""

    ctx.logger.info(f"ACP ChatMessage received from {sender}")

    try:
        await ctx.send(
            sender,
            ChatAcknowledgement(
                timestamp=datetime.now(timezone.utc),
                acknowledged_msg_id=msg.msg_id,
            ),
        )
    except Exception as e:
        ctx.logger.warning(f"Failed to send ChatAcknowledgement: {e}")

    incoming_text = " ".join(
        item.text for item in msg.content if isinstance(item, TextContent)
    ).strip() or "Hello"

    # Route an explicit readiness-review request to the remote agent.
    if "readiness review" in incoming_text.lower():
        request_id = str(uuid4())
        pending_readiness_requests[request_id] = sender

        try:
            await ctx.send(
                READINESS_AGENT_ADDRESS,
                ReadinessRequest(
                    request_id=request_id,
                    situation=incoming_text,
                    candidate_schemes=(
                        "Identify relevant schemes based on the user's "
                        "situation; verify details using official sources."
                    ),
                ),
            )
            ctx.logger.info(
                f"Readiness request {request_id} sent to remote agent."
            )
            return
        except Exception as err:
            pending_readiness_requests.pop(request_id, None)
            ctx.logger.error(f"Could not send readiness request: {err}")

            response_text = (
                "I couldn't contact the Readiness Agent right now. "
                "Please try again later."
            )
            await ctx.send(
                sender,
                ChatMessage(
                    timestamp=datetime.now(timezone.utc),
                    msg_id=uuid4(),
                    content=[TextContent(type="text", text=response_text)],
                ),
            )
            return

    # Preserve the existing HakkuAI conversation behavior for other messages.
    try:
        conv_resp = conversation_engine.process_message(
            sender=sender,
            text=incoming_text,
        )
        response_text = conv_resp.response_text
    except Exception as err:
        ctx.logger.error(f"Error processing message from {sender}: {err}")
        response_text = (
            "I encountered a technical processing error. Please restate "
            "your situation, including your state, occupation, and whether "
            "you experienced a workplace injury."
        )

    await ctx.send(
        sender,
        ChatMessage(
            timestamp=datetime.now(timezone.utc),
            msg_id=uuid4(),
            content=[TextContent(type="text", text=response_text)],
        ),
    )


@chat_proto.on_message(ChatAcknowledgement)
async def handle_chat_ack(
    ctx: Context, sender: str, msg: ChatAcknowledgement
):
    """Handle chat delivery acknowledgements."""
    ctx.logger.debug(
        f"Received acknowledgement from {sender} "
        f"for {msg.acknowledged_msg_id}"
    )


# ---------------------------------------------------------------------------
# 2. Structured Welfare RPC Protocol
# ---------------------------------------------------------------------------

class WelfareAssessmentRequest(Model):
    state: str | None = None
    occupation: str | None = None
    is_construction_worker: bool | None = None
    is_bocw_registered: bool | None = None
    accident_occurred_at_work: bool | None = None
    injury_severity: str | None = None
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
    session_id: str
    is_emergency: bool
    status_summary: str
    schemes: list[SchemeSummaryModel]
    recommended_next_step: str
    disclaimer: str


welfare_rpc_proto = Protocol(name="HakkuWelfareRPC", version="1.0.0")


@welfare_rpc_proto.on_message(
    WelfareAssessmentRequest,
    replies={WelfareAssessmentResponse},
)
async def handle_welfare_rpc(
    ctx: Context, sender: str, msg: WelfareAssessmentRequest
):
    """Handle structured welfare assessment requests."""
    ctx.logger.info(f"Received WelfareAssessmentRequest from {sender}")

    profile = WorkerProfile(
        state=msg.state,
        occupation=msg.occupation,
        is_construction_worker=msg.is_construction_worker,
        is_bocw_registered=msg.is_bocw_registered,
        accident_occurred_at_work=msg.accident_occurred_at_work,
        hospital_treatment_received=msg.hospital_treatment,
        preferred_language=Language.TA if msg.language == "ta" else Language.EN,
    )

    if msg.injury_severity:
        try:
            profile.injury_severity = InjurySeverity(
                msg.injury_severity.lower()
            )
        except ValueError:
            ctx.logger.warning(
                f"Unrecognized injury severity: {msg.injury_severity}"
            )

    if msg.raw_query:
        conversation_engine.extract_profile_updates(msg.raw_query, profile)

    session = conversation_engine.session_manager.get_or_create_session(sender)
    session.profile = profile

    from hakkuai.eligibility import assess_worker_eligibility
    from hakkuai.injury_workflow import evaluate_injury_workflow

    injury_guidance = evaluate_injury_workflow(
        profile,
        raw_user_text=msg.raw_query or "",
    )
    schemes_res = assess_worker_eligibility(profile)

    scheme_models = [
        SchemeSummaryModel(
            scheme_id=s.scheme_id,
            name=(
                s.tamil_name
                if profile.preferred_language == Language.TA
                else s.scheme_name
            ),
            status=s.status.value,
            benefit_limits=s.benefit_limits,
            official_source_url=s.official_source_url,
            explanation=(
                s.explanation_ta
                if profile.preferred_language == Language.TA
                else s.explanation_en
            ),
        )
        for s in schemes_res
    ]

    next_steps = (
        injury_guidance.next_steps_ta
        if profile.preferred_language == Language.TA
        else injury_guidance.next_steps_en
    )
    disclaimer = (
        injury_guidance.disclaimer_ta
        if profile.preferred_language == Language.TA
        else injury_guidance.disclaimer_en
    )

    response = WelfareAssessmentResponse(
        session_id=session.session_id,
        is_emergency=injury_guidance.is_emergency,
        status_summary=f"Evaluated {len(schemes_res)} welfare pathways.",
        schemes=scheme_models,
        recommended_next_step=(
            next_steps[0]
            if next_steps
            else "Consult local labour welfare officer"
        ),
        disclaimer=disclaimer,
    )

    await ctx.send(sender, response)
    ctx.logger.info(f"Dispatched WelfareAssessmentResponse to {sender}")


# ---------------------------------------------------------------------------
# 3. Readiness RPC Protocol
# ---------------------------------------------------------------------------

class ReadinessRequest(Model):
    request_id: str
    situation: str
    candidate_schemes: str


class ReadinessResponse(Model):
    request_id: str
    status: str
    report: str


readiness_proto = Protocol(name="HakkuReadinessRPC", version="1.0.0")

READINESS_AGENT_ADDRESS = (
    "agent1q2a6v2apdw637cf7crfprle8gwthh3wf9w6xtfu9zqha6vrg52rcvszejcv"
)


@readiness_proto.on_message(ReadinessRequest)
async def handle_readiness_request(
    ctx: Context, sender: str, msg: ReadinessRequest
):
    """Respond to readiness requests sent TO HakkuAI."""
    ctx.logger.info(f"Received ReadinessRequest from {sender}")

    report = (
        "HAKKUAI APPLICATION READINESS REPORT\n\n"
        f"Situation: {msg.situation}\n\n"
        f"Candidate schemes: {msg.candidate_schemes}\n\n"
        "CHECKLIST\n"
        "1. Verify scheme details using official government sources.\n"
        "2. Check eligibility conditions and exceptions.\n"
        "3. Identify required supporting documents.\n"
        "4. Identify missing or expired documents.\n"
        "5. Confirm application steps, deadlines, and submission channel.\n"
        "6. Obtain user consent before sharing personal information or "
        "taking consequential action.\n\n"
        "This is a preliminary checklist, not an eligibility decision "
        "or guarantee of approval. Requirements have not been independently "
        "verified by this handler."
    )

    await ctx.send(
        sender,
        ReadinessResponse(
            request_id=msg.request_id,
            status="completed",
            report=report,
        ),
    )


@readiness_proto.on_message(ReadinessResponse)
async def handle_remote_readiness_response(
    ctx: Context, sender: str, msg: ReadinessResponse
):
    """Return the remote report to the original chat sender."""
    original_sender = pending_readiness_requests.pop(msg.request_id, None)

    if original_sender is None:
        ctx.logger.warning(
            f"No matching chat request for readiness response "
            f"{msg.request_id}"
        )
        return

    response_text = (
        f"Remote Readiness Agent status: {msg.status}\n\n{msg.report}"
    )

    await ctx.send(
        original_sender,
        ChatMessage(
            timestamp=datetime.now(timezone.utc),
            msg_id=uuid4(),
            content=[TextContent(type="text", text=response_text)],
        ),
    )

    ctx.logger.info(
        f"Returned readiness report to original user {original_sender}"
    )