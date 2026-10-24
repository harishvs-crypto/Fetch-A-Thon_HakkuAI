# Agentverse Registration & Deployment Guide

This guide details how to register and deploy **HakkuAI** on Fetch.ai's **Agentverse** to achieve 24/7 global discoverability and integration with the Fetch.ai / ASI ecosystem.

---

## 1. Prerequisites

1. An account on [Agentverse](https://agentverse.ai).
2. Python 3.11 with dependencies installed (`pip install -r requirements.txt`).
3. Your agent's unique seed phrase generated locally or securely generated on Agentverse.

---

## 2. Agent Identity & Address

When you start HakkuAI, the agent derives an immutable address on the Fetch network based on its seed phrase:

```bash
python -c "import sys; sys.path.insert(0, 'src'); from hakkuai.agent import hakku_agent; print(hakku_agent.address)"
```
*Example Output:*
```
agent1qf3a2vppnvrg4txephs5ut9vn0x5tfyd87aer4fszxtlh35vj6ay7z4f2mr
```

> [!IMPORTANT]
> Keep your seed phrase secure! Never commit `.env` or paste seeds into public repositories.

---

## 3. Connecting via Agentverse Mailbox (Recommended for Local Hosting)

The **Agentverse Mailbox** allows your local HakkuAI agent to receive messages from ASI:One and other agents 24/7 without opening router ports or having a public static IP.

In `uAgents >= 0.26.0`, connection is handled seamlessly via the built-in **Agent Inspector**:

### Step 1: Configure Environment Variables
Copy `.env.example` to `.env` if you have not already:

```bash
cp .env.example .env
```

Ensure `.env` contains:
```ini
HAKKUAI_AGENT_NAME=hakkuai_welfare_assistant
HAKKUAI_AGENT_PORT=8000
HAKKUAI_AGENT_SEED=your_secure_unique_seed_phrase_here

# Enable Mailbox mode for Agentverse
HAKKUAI_MAILBOX_ENABLED=true
```

### Step 2: Start HakkuAI as a Local Agent
Run HakkuAI in agent daemon mode:
```bash
python src/hakkuai/agent.py
```
Upon startup, `uagents` starts the local ASGI server on `http://0.0.0.0:8000` and displays your **Agent Inspector** URL in the terminal logs:
```text
INFO: [hakkuai_welfare_assistant]: Agent inspector available at https://agentverse.ai/inspect/?uri=http%3A//127.0.0.1%3A8000&address=agent1qf3a2vppnvrg4txephs5ut9vn0x5tfyd87aer4fszxtlh35vj6ay7z4f2mr
```

### Step 3: Connect in Agentverse
1. Log in to [Agentverse](https://agentverse.ai).
2. Open the **Agent Inspector** URL displayed in your startup terminal in your web browser.
3. In the Inspector interface, click the **Connect** button.
4. Select the **Mailbox** option.
5. Confirm the connection. Agentverse will verify your agent's cryptographic identity and provision the mailbox endpoint.

Once connected, your local terminal will confirm:
```text
INFO: [mailbox]: Successfully registered as mailbox agent in Agentverse.
INFO: [hakkuai_welfare_assistant]: Starting mailbox client for https://agentverse.ai
```
Your agent is now visible in the Agentverse **My Agents** dashboard under **Local Agents** with the **Mailbox** badge.

---

## 4. Option B: Direct Hosting on Agentverse Cloud

If deploying entirely as a hosted agent in Agentverse Cloud:
1. In Agentverse, navigate to **My Agents** -> **New Agent** -> **Blank Agent**.
2. Set the Agent Name to `HakkuAI - Welfare Assistance Agent`.
3. Paste the contents of `src/hakkuai/agent.py` and supporting modules into the Agentverse editor.
4. Add the protocol `AgentChatProtocol` (v0.3.0) and compile.
5. Click **Start** to run the agent in the cloud.

---

## 5. Almanac Registration & Discoverability Verification

To verify that HakkuAI is registered in the decentralized Almanac smart contract registry:

1. **Check Local Startup Log**:
   ```
   [INFO] [hakkuai] Ready for ASI:One & Agentverse communication.
   [INFO] [hakkuai] ACP Protocol : AgentChatProtocol v0.3.0 (Enabled)
   ```
2. **Inspect Almanac Contract Lookup**:
   Use Fetch.ai's network explorer or query the resolver:
   ```bash
   python -c "from uagents.resolver import RulesBasedResolver; r = RulesBasedResolver(); print(r)"
   ```
3. **Agentverse Discovery Tab**:
   In Agentverse, search for your agent's address or name (`hakkuai_welfare_assistant`) under the **Search Agents** tab. Ensure that:
   - Status shows as **Active / Running**.
   - Protocol shows **AgentChatProtocol v0.3.0**.
