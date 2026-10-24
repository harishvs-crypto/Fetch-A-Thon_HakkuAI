# Agent Communication Protocol (ACP) Integration

This document describes HakkuAI's implementation of the **Agent Chat Protocol (ACP)** and the dual-protocol communication stack built for Fetch-A-Thon 3.0.

---

## 1. What is ACP in Fetch-A-Thon 3.0?

In the Fetch.ai and ASI ecosystem, **ACP** stands for the **Agent Chat Protocol** (standardized as `AgentChatProtocol` v0.3.0 in `uagents_core.contrib.protocols.chat`).

It is the official standard that allows agents to:
1. Interoperate natively with **ASI:One** conversational interfaces.
2. Exchange structured natural language blocks without requiring custom ad-hoc JSON endpoints.
3. Handle delivery confirmations via standard handshakes (`ChatAcknowledgement`).
4. Broadcast capabilities automatically into the Almanac decentralized registry.

---

## 2. Protocol Specification & Imports

HakkuAI utilizes the verified, official SDK interfaces directly from `uagents_core`:

```python
from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatMessage,
    ChatAcknowledgement,
    TextContent,
    chat_protocol_spec,
)
```

### The Protocol Spec:
- **Canonical Name**: `AgentChatProtocol`
- **Protocol Version**: `0.3.0`
- **Digest**: `proto:30a801ed3a83f9a0ff0a9f1e6fe958cb91da1fc2218b153df7b6cbf87bd33d62`
- **Interactions**:
  - `ChatMessage` -> acknowledges with `ChatAcknowledgement` and replies with `ChatMessage`
  - `ChatAcknowledgement` -> records receipt

---

## 3. HakkuAI's Message Handling Pipeline

```
  Remote Client / ASI:One                        HakkuAI uAgent
         |                                             |
         | -------- 1. Send ChatMessage -------------> |
         |                                             |
         | <------- 2. Send ChatAcknowledgement ----- | (Instant receipt confirmation)
         |                                             |
         |                                             | [Progressive Intake & Engine]
         |                                             | [112 Emergency Check]
         |                                             | [Eligibility Assessment]
         |                                             | [Checklist Generator]
         |                                             |
         | <------- 3. Send Reply ChatMessage -------- | (Formatted Bilingual Guidance)
         |                                             |
```

### Message Handler Code (`src/hakkuai/acp_handlers.py`):
```python
chat_proto = Protocol(spec=chat_protocol_spec)

@chat_proto.on_message(ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    # 1. Immediate Delivery Receipt
    ack = ChatAcknowledgement(
        timestamp=datetime.now(timezone.utc),
        acknowledged_msg_id=msg.msg_id
    )
    await ctx.send(sender, ack)

    # 2. Extract TextContent
    text = "".join(
        content.text for content in msg.content if isinstance(content, TextContent)
    )

    # 3. Process through Welfare Engine
    conv_resp = conversation_engine.process_message(sender=sender, text=text)

    # 4. Return Structured ChatMessage
    reply = ChatMessage(
        timestamp=datetime.now(timezone.utc),
        msg_id=uuid4(),
        content=[TextContent(type="text", text=conv_resp.response_text)]
    )
    await ctx.send(sender, reply)
```

---

## 4. Structured Inter-Agent Welfare RPC Protocol

In addition to conversational ACP, HakkuAI registers `HakkuWelfareRPC` (v1.0.0) for machine-to-machine querying by other autonomous agents in the Fetch.ai mesh:

```python
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

class WelfareAssessmentResponse(Model):
    session_id: str
    is_emergency: bool
    status_summary: str
    schemes: list[SchemeSummaryModel]
    recommended_next_step: str
    disclaimer: str
```

---

## 5. Local Protocol Testing

To test the protocol handlers locally without needing external network connectivity, run the automated protocol tests:

```bash
python -m pytest tests/test_protocol.py -v
```

This verifies:
1. `test_acp_chat_message_flow`: Confirms `ChatMessage` dispatches both a valid `ChatAcknowledgement` and a structured reply `ChatMessage`.
2. `test_structured_welfare_rpc_flow`: Tests typed inter-agent RPC communication.
3. All 3 Hackathon End-to-End demonstration scenarios.
