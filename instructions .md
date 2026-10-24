# HakkuAI Welfare Assistance Agent

HakkuAI is an AI welfare assistance agent designed to help construction and daily-wage workers understand potential welfare benefits, eligibility requirements, required documents, and application steps.

## 1. Prerequisites

Install the following before running HakkuAI:

- Python 3.11
- Git
- A terminal such as PowerShell, Command Prompt, or a Bash shell

## 2. Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/hakkuai-welfare-assistant.git
cd hakkuai-welfare-assistant
```

Replace `YOUR-USERNAME` with the GitHub account that hosts this repository.

## 3. Create a Virtual Environment

**Windows (Command Prompt):**

```cmd
python -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 4. Install Dependencies

Install the project dependencies using the repository's dependency configuration:

```bash
python -m pip install --upgrade pip
pip install -e .
```

If the project does not define editable installation in its `pyproject.toml`, follow the dependency installation instructions specified in that file instead.

## 5. Configure Environment Variables

Create a local `.env` file from the example:

**Windows (Command Prompt):**

```cmd
copy .env.example .env
```

**macOS/Linux:**

```bash
cp .env.example .env
```

Review `.env.example` and configure the required values in `.env`. For example, the project may use:

```dotenv
HAKKUAI_MAILBOX_ENABLED=true
HAKKUAI_NETWORK=testnet
```

Keep all private keys, agent seeds, tokens, and other credentials in the local `.env` file. Never commit `.env` or private key files to GitHub.

## 6. Run Automated Tests

From the repository root, execute:

```bash
python -m pytest tests/ -v
```

The current development test report recorded **36 passing tests**. Run the command again after cloning to verify the exact result in your environment.

The tests cover conversation handling, eligibility guidance, document checklists, injury workflows, scheme filtering, and protocol message flows.

## 7. Run HakkuAI in CLI Mode

Start the local command-line interface:

```bash
python src/hakkuai/agent.py --cli
```

Use the CLI to exercise the welfare assistance conversation and check the agent's responses.

## 8. Run the Agent

Start the agent in normal mode:

```bash
python src/hakkuai/agent.py
```

The agent startup logs should report its address, network, protocol configuration, and mailbox status.

To stop the running agent, press `Ctrl+C`.

### Agentverse and ASI:One

For Agentverse integration:

1. Configure the environment variables using `.env.example`.
2. Start the agent.
3. Open the Agent Inspector URL printed in the terminal.
4. Sign in to Agentverse and follow its current instructions to connect the local agent mailbox.
5. Verify mailbox connectivity and agent registration in the logs and Agentverse.

**Note:** Successful local startup and passing tests do not guarantee live ASI:One message delivery. During the current development session, ASI:One returned a retry error, and a server-side issue was reported. Verify live integration independently before claiming end-to-end availability.

## 9. Health Server (Optional)

To run the health server mode:

```bash
python src/hakkuai/agent.py --health-server
```

Use this mode only for the health-check workflow supported by the current implementation.

## 10. Project Structure

```text
Hakku AI/
├── data/
│   └── schemes.json
├── docs/
│   └── AGENTVERSE_SETUP.md
├── src/
│   └── hakkuai/
│       ├── agent.py
│       └── config.py
├── tests/
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

## Troubleshooting

- **Missing dependencies:** Activate the virtual environment and reinstall dependencies.
- **Missing configuration:** Check `.env.example` and your local `.env`.
- **Mailbox connection errors:** Check internet connectivity, DNS resolution, and Agentverse service status.
- **Almanac registration warnings:** Check the configured network and registration status. Do not send real cryptocurrency just to silence a warning.
- **ASI:One retry errors:** Check mailbox connectivity and the live service status; local tests alone cannot diagnose a remote delivery failure.

## Security

- Never commit `.env`, agent seeds, private keys, or credentials.
- Use testnet for development where supported.
- Do not publish secrets in issue reports, logs, or screenshots.

## Disclaimer

HakkuAI provides informational assistance about potential welfare benefits and application processes. Eligibility and benefit amounts depend on the applicable scheme, location, and official rules. Users should verify requirements with the relevant government department or welfare board.
