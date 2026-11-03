#!/usr/bin/env python3
"""Demo agent for the Tessl security-gate tutorial.

Loads a skill only if it passed `tessl review run security`, then runs it with the
model and prompt from the AgentControl config `report-summarizer-agent`. There is no
hardcoded fallback: if LaunchDarkly isn't serving the config, the agent exits non-zero.
"""
import asyncio
import json
import os
import sys
from pathlib import Path

import ldclient
from ldclient.config import Config
from launchdarkly_ai_server import config, init_client, inspect_config, shutdown
from launchdarkly_ai_openai_messages import create_openai_messages_handler

CONFIG_KEY = os.environ.get("LD_AI_CONFIG_KEY", "report-summarizer-agent")
SKILL_DIR = Path(__file__).resolve().parents[1] / "skills-content" / "demo" / "report-summarizer"
SAMPLE_REPORT = (
    "Q3 infra review: p99 latency fell 22% after the cache rollout; error budget spend "
    "held at 31%; one SEV-2 (config drift) cost 40 minutes. Cloud spend up 8% on "
    "increased egress. Recommend capping egress and promoting the cache change to all regions."
)


def load_cleared_skill(skill_dir: Path) -> str:
    """Return SKILL.md only if the committed Tessl review result says verdict: pass."""
    review_path = skill_dir / "tessl-review-result.json"
    if not review_path.is_file():
        sys.exit(f"No Tessl review result at {review_path}. Refusing to load an unreviewed skill.")
    verdict = json.loads(review_path.read_text()).get("verdict")
    if verdict != "pass":
        sys.exit(f"Skill has not passed its Tessl review (verdict={verdict!r}).")
    return (skill_dir / "SKILL.md").read_text()


async def main():
    ldclient.set_config(Config(os.environ.get("LD_SDK_KEY") or sys.exit("LD_SDK_KEY is not set.")))
    client = ldclient.get()
    if not client.is_initialized():
        sys.exit("LaunchDarkly SDK failed to initialize. Cannot fetch the config.")
    await init_client(client=client)

    context = {"kind": "user", "key": "demo-user"}
    report_text = SAMPLE_REPORT if sys.stdin.isatty() else sys.stdin.read().strip()

    try:
        state = await inspect_config(CONFIG_KEY, context)
        if not state["enabled"]:
            sys.exit(f"Config {CONFIG_KEY!r} is not being served (enabled=False).")

        skill = load_cleared_skill(SKILL_DIR)

        # The config's system message decides where {{skill}} lands in the prompt.
        result = await config(
            key=CONFIG_KEY,
            handler=create_openai_messages_handler(),
        ).invoke(report_text, context, {"report_text": report_text, "skill": skill})

        print(result.response)
    finally:
        await shutdown()


if __name__ == "__main__":
    asyncio.run(main())
