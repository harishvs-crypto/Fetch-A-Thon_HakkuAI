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

## 3. Option A: Connecting via Agentverse Mailbox (Recommended for Local Hosting)

The **Agentverse Mailbox** allows your local HakkuAI agent to receive messages from ASI:One and other agents 24/7 without opening firewall ports or acquiring a static public IP.

### Step 1: Create a Mailbox on Agentverse
1. Log in to [Agentverse](https://agentverse.ai).
2. Go to **My Agents** -> **Local Agents**.
3. Click **Connect Local Agent**.
4. Enter your Agent Name: `hakkuai_welfare_assistant`.
5. Enter your Agent Address (obtained from the command above).
6. Copy the generated **Mailbox Key**.

### Step 2: Configure Environment Variables
Copy `.env.example` to `.env` and fill in your Mailbox configuration:

```bash
cp .env.example .env
```

Edit `.env`:
```ini
HAKKUAI_AGENT_NAME=hakkuai_welfare_assistant
HAKKUAI_AGENT_PORT=8000
HAKKUAI_AGENT_SEED=your_secure_unique_seed_phrase_here

# Enable Mailbox
HAKKUAI_MAILBOX_ENABLED=true
AGENTVERSE_MAILBOX_KEY=your_copied_mailbox_key_here
```

### Step 3: Start HakkuAI
```bash
python src/hakkuai/agent.py
```
HakkuAI will connect to `https://agentverse.ai`, establish its websocket mailbox tunnel, and register its protocol manifests automatically!

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
