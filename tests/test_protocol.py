"""
Tests for Agent Communication Protocol (ACP) and End-to-End Hackathon Scenarios.
Covers ACP message structures, acknowledgements, structured RPC handlers,
and the three mandatory Fetch-A-Thon 3.0 demonstration scenarios.
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from uagents_core.contrib.protocols.chat import (
    ChatMessage,
    ChatAcknowledgement,
    TextContent
)
from hakkuai.acp_handlers import (
    handle_chat_message,
    handle_welfare_rpc,
    WelfareAssessmentRequest,
    WelfareAssessmentResponse,
    conversation_engine
)
from hakkuai.schemas import EligibilityStatus

class MockContext:
    """Mock uAgents Context for protocol testing."""
    def __init__(self):
        self.sent_messages: list[tuple[str, any]] = []
        self.logger = MockLogger()

class MockLogger:
    def info(self, msg): pass
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass

async def mock_send(ctx: MockContext, destination: str, message: any):
    ctx.sent_messages.append((destination, message))

@pytest.mark.asyncio
async def test_acp_chat_message_flow():
    """Verify ACP ChatMessage generates ChatAcknowledgement and reply ChatMessage."""
    ctx = MockContext()
    ctx.send = lambda dest, msg: mock_send(ctx, dest, msg)

    incoming_msg_id = uuid4()
    incoming_chat = ChatMessage(
        timestamp=datetime.now(timezone.utc),
        msg_id=incoming_msg_id,
        content=[TextContent(type="text", text="I am a construction worker in Tamil Nadu with an injury")]
    )

    sender = "agent_client_test_address_123"
    await handle_chat_message(ctx, sender, incoming_chat)

    assert len(ctx.sent_messages) == 2, "Expected 2 protocol messages: 1 ChatAcknowledgement + 1 reply ChatMessage"

    # Message 1: ChatAcknowledgement
    dest_ack, msg_ack = ctx.sent_messages[0]
    assert dest_ack == sender
    assert isinstance(msg_ack, ChatAcknowledgement)
    assert msg_ack.acknowledged_msg_id == incoming_msg_id

    # Message 2: Reply ChatMessage
    dest_reply, msg_reply = ctx.sent_messages[1]
    assert dest_reply == sender
    assert isinstance(msg_reply, ChatMessage)
    assert len(msg_reply.content) >= 1
    assert isinstance(msg_reply.content[0], TextContent)
    assert "Tamil Nadu" in msg_reply.content[0].text

@pytest.mark.asyncio
async def test_structured_welfare_rpc_flow():
    """Verify structured Inter-Agent RPC protocol execution."""
    ctx = MockContext()
    ctx.send = lambda dest, msg: mock_send(ctx, dest, msg)

    req = WelfareAssessmentRequest(
        state="Tamil Nadu",
        occupation="Construction Worker",
        is_construction_worker=True,
        is_bocw_registered=True,
        accident_occurred_at_work=True,
        injury_severity="severe",
        language="en"
    )

    sender = "peer_agent_address_456"
    await handle_welfare_rpc(ctx, sender, req)

    assert len(ctx.sent_messages) == 1
    dest, response = ctx.sent_messages[0]
    assert dest == sender
    assert isinstance(response, WelfareAssessmentResponse)
    assert len(response.schemes) >= 2
    scheme_ids = [s.scheme_id for s in response.schemes]
    assert "tn_bocw_accident_relief" in scheme_ids


# ===========================================================================
# FETCH-A-THON 3.0 MANDATORY END-TO-END DEMONSTRATION SCENARIOS
# ===========================================================================

def test_e2e_scenario_1_registered_worker_with_injury():
    """
    Scenario 1: A registered construction worker with a workplace injury.
    State: Tamil Nadu.
    Registration: Registered with TNBOCW Welfare Board.
    Injury: Serious leg fracture at construction site.
    Expected:
      - Preliminary Potentially Eligible for TN BOCW Accident Relief.
      - Potentially Eligible for Employees' Compensation Act 1923.
      - Personalized document checklist includes BOCW membership card, hospital discharge summary.
      - Step-by-step next steps directing to District Labour Officer.
    """
    sender = "worker_scenario_1"
    conversation_engine.session_manager.clear_session(sender)

    # Conversational turn:
    user_prompt = "I am a registered construction worker in Tamil Nadu. I broke my leg at the construction site."
    resp = conversation_engine.process_message(sender, user_prompt)

    session = conversation_engine.session_manager.get_or_create_session(sender)
    assert session.profile.state == "Tamil Nadu"
    assert session.profile.is_construction_worker is True
    assert session.profile.is_bocw_registered is True
    assert session.profile.accident_occurred_at_work is True

    schemes_dict = {s.scheme_id: s for s in resp.schemes_evaluated}
    assert schemes_dict["tn_bocw_accident_relief"].status == EligibilityStatus.POTENTIALLY_ELIGIBLE
    assert schemes_dict["central_employees_compensation_1923"].status == EligibilityStatus.POTENTIALLY_ELIGIBLE

    # Check that response mentions Tamil Nadu BOCW and Employees' Compensation Act
    assert "Tamil Nadu BOCW" in resp.response_text
    assert "Employees' Compensation Act" in resp.response_text
    assert "District Labour Officer" in resp.response_text

def test_e2e_scenario_2_unregistered_worker_injury_assistance():
    """
    Scenario 2: An injured worker whose registration status is unknown / unregistered.
    State: Tamil Nadu.
    Occupation: Construction daily wager.
    Registration: Unregistered (employer did not register them).
    Expected:
      - Honestly explains that direct BOCW board claim requires membership, but does NOT stop there.
      - Informs worker of statutory employer liability under Employees' Compensation Act 1923.
      - Outlines what to do when employer hasn't registered them or documentation is missing.
      - Explains fallback evidence (co-worker witness affidavits, supervisor messages, muster roll).
    """
    sender = "worker_scenario_2"
    conversation_engine.session_manager.clear_session(sender)

    user_prompt = "I work in construction in Tamil Nadu and got injured at work. My contractor never registered me with any welfare board."
    resp = conversation_engine.process_message(sender, user_prompt)

    session = conversation_engine.session_manager.get_or_create_session(sender)
    assert session.profile.state == "Tamil Nadu"
    assert session.profile.is_bocw_registered is False

    schemes_dict = {s.scheme_id: s for s in resp.schemes_evaluated}
    # Direct board claim is flagged as needing more information / registration handling
    assert schemes_dict["tn_bocw_accident_relief"].status == EligibilityStatus.MORE_INFORMATION_NEEDED
    # But Central statutory compensation is Potentially Eligible!
    assert schemes_dict["central_employees_compensation_1923"].status == EligibilityStatus.POTENTIALLY_ELIGIBLE

    # Response must contain explicit unregistered guidance
    assert "Guidance When Unregistered with the Welfare Board" in resp.response_text
    assert "Statutory Employer Liability" in resp.response_text
    assert "Commissioner for Employees' Compensation" in resp.response_text

def test_e2e_scenario_3_incomplete_state_database_honest_uncertainty():
    """
    Scenario 3: A worker from a state for which the local scheme database is incomplete.
    State: Nagaland.
    Occupation: Construction worker with workplace injury.
    Expected:
      - Correctly communicates uncertainty instead of inventing benefits.
      - Does NOT fabricate state welfare board benefit amounts, fake phone numbers, or fake portals.
      - Explicitly flags UNVERIFIED_DATA for the local state board.
      - Evaluates universal national schemes (Employees' Compensation Act 1923).
      - Directs worker to the official Nagaland Labour Commissioner Office.
    """
    sender = "worker_scenario_3"
    conversation_engine.session_manager.clear_session(sender)

    user_prompt = "I am a construction worker in Nagaland. I was hurt in a site accident."
    resp = conversation_engine.process_message(sender, user_prompt)

    session = conversation_engine.session_manager.get_or_create_session(sender)
    assert session.profile.state == "Nagaland"

    unverified_schemes = [s for s in resp.schemes_evaluated if s.status == EligibilityStatus.UNVERIFIED_DATA]
    assert len(unverified_schemes) >= 1, "Must generate an UNVERIFIED_DATA notice for incomplete state"

    unverified = unverified_schemes[0]
    assert "Nagaland" in unverified.scheme_name
    assert "not currently contain" in unverified.explanation_en.lower() or "incomplete" in unverified.explanation_en.lower()

    # Response text must communicate honest uncertainty
    assert "Notice of Incomplete Local Rules" in resp.response_text
    assert "Nagaland" in resp.response_text
    assert "we do NOT fabricate benefit amounts" in resp.response_text
