"""
Main entry point for HakkuAI Welfare Assistant Agent.
Initializes the uAgent with Agent Communication Protocol (ACP),
handles Agentverse/Mailbox setup, and provides optional health endpoints and CLI mode.
"""

import argparse
import sys
from pathlib import Path

# Ensure 'src' is in sys.path when executed directly as a script
src_dir = str(Path(__file__).resolve().parent.parent)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from uagents import Agent, Context
from hakkuai.config import settings
from hakkuai.logging_config import logger
from hakkuai.acp_handlers import chat_proto, welfare_rpc_proto, conversation_engine

def create_agent() -> Agent:
    """
    Factory function creating and configuring the HakkuAI uAgent.
    """
    # Configure mailbox arguments if enabled
    mailbox_param = None
    if settings.MAILBOX_ENABLED:
        if settings.AGENTVERSE_MAILBOX_KEY:
            mailbox_param = f"{settings.AGENTVERSE_MAILBOX_KEY}@https://agentverse.ai"
        else:
            mailbox_param = True # Auto-mailbox via agentverse

    agent = Agent(
        name=settings.AGENT_NAME,
        port=settings.AGENT_PORT,
        seed=settings.AGENT_SEED,
        mailbox=mailbox_param
    )

    # Include Official Agent Chat Protocol (ACP)
    agent.include(chat_proto, publish_manifest=True)

    # Include Structured Inter-Agent Welfare RPC Protocol
    agent.include(welfare_rpc_proto, publish_manifest=True)

    @agent.on_event("startup")
    async def startup_handler(ctx: Context):
        ctx.logger.info("==================================================")
        ctx.logger.info("   HAKKUAI WELFARE ASSISTANCE AGENT (Fetch-A-Thon 3.0)")
        ctx.logger.info("==================================================")
        ctx.logger.info(f"Agent Name    : {ctx.name}")
        ctx.logger.info(f"Agent Address : {ctx.address}")
        ctx.logger.info(f"Listening Port: {settings.AGENT_PORT}")
        ctx.logger.info(f"ACP Protocol  : AgentChatProtocol v0.3.0 (Enabled)")
        ctx.logger.info(f"Mailbox Mode  : {'Active' if settings.MAILBOX_ENABLED else 'Local Standalone'}")
        ctx.logger.info("Ready for ASI:One & Agentverse communication.")
        ctx.logger.info("==================================================")

    return agent

# Singleton agent instance
hakku_agent = create_agent()

def run_interactive_cli():
    """
    Runs an interactive terminal session demonstrating HakkuAI's conversational intake,
    scheme evaluation, emergency handling, and document checklist generator.
    """
    print("\n" + "=" * 65)
    print("   HAKKUAI INTERACTIVE CLI — WELFARE GUIDANCE ENGINE")
    print("   Type 'exit' or 'quit' to end session.")
    print("   Supports English and Tamil (தமிழ்).")
    print("=" * 65 + "\n")

    sender = "local_worker_cli_demo"
    print("HakkuAI: Hello! I am HakkuAI. How can I help you today?\n"
          "         (வணக்கம்! நான் ஹக்கு ஏஐ. உங்களுக்கு எவ்வாறு உதவலாம்?)\n")

    while True:
        try:
            user_input = input("Worker > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q"):
                print("\nThank you for using HakkuAI. Stay safe!")
                break

            response = conversation_engine.process_message(sender=sender, text=user_input)
            print("\n" + "-" * 60)
            print(f"HakkuAI >\n{response.response_text}")
            print("-" * 60 + "\n")
        except (KeyboardInterrupt, EOFError):
            print("\nSession ended.")
            break

def start_health_server():
    """Starts a lightweight FastAPI healthcheck and metadata server."""
    import uvicorn
    from fastapi import FastAPI

    app = FastAPI(
        title="HakkuAI Health API",
        description="Health check and status API for HakkuAI agent",
        version="0.1.0"
    )

    @app.get("/health")
    def health():
        return {
            "status": "healthy",
            "agent_name": settings.AGENT_NAME,
            "agent_address": hakku_agent.address,
            "protocols": ["AgentChatProtocol_0.3.0", "HakkuWelfareRPC_1.0.0"],
            "mailbox_enabled": settings.MAILBOX_ENABLED
        }

    @app.get("/schemes")
    def list_schemes():
        from hakkuai.scheme_database import scheme_db
        return {
            "count": len(scheme_db.get_all_schemes()),
            "schemes": [
                {
                    "scheme_id": s.scheme_id,
                    "name": s.name,
                    "state": s.state_or_national,
                    "verified": s.verified_status
                }
                for s in scheme_db.get_all_schemes()
            ]
        }

    port = settings.AGENT_PORT + 1
    logger.info(f"Starting HakkuAI Health server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)

def main():
    parser = argparse.ArgumentParser(description="HakkuAI Welfare Assistant Agent")
    parser.add_argument("--cli", action="store_true", help="Launch interactive CLI demo mode")
    parser.add_argument("--health-server", action="store_true", help="Launch FastAPI health server")
    args = parser.parse_args()

    if args.cli:
        run_interactive_cli()
    elif args.health_server:
        start_health_server()
    else:
        logger.info(f"Starting HakkuAI agent with address: {hakku_agent.address}")
        hakku_agent.run()

if __name__ == "__main__":
    main()
