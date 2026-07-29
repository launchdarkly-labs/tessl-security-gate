#!/usr/bin/env python3
"""Demo agent for the Tessl security-gate tutorial.

The security gate (`tessl review run security`) is the on-ramp: it clears a skill
before you trust it. This agent is what happens *after* the gate. It loads the
cleared skill and runs it, but takes its model and prompt from LaunchDarkly
AgentControl rather than hardcoding them.

Design choices for the demo:
  * No hardcoded prompt fallback. The system/user messages come only from the
    AgentControl config `report-summarizer-agent`.
  * Hard-fail if LaunchDarkly isn't serving the config. If the SDK returns
    enabled=False (no valid SDK key, LD unreachable, or targeting off), the
    agent refuses to run and exits non-zero. No config, no agent.
  * Only loads a skill that passed the Tessl security review.

Env (see .env.example):
  LD_SDK_KEY       server-side SDK key for the environment whose targeting is on
  OPENAI_API_KEY   OpenAI key for the completion call
  LD_AI_CONFIG_KEY optional; defaults to "report-summarizer-agent"
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import ldclient
from ldclient import Context
from ldclient.config import Config
from ldai.client import AICompletionConfigDefault, LDAIClient
from ldai_openai import convert_messages_to_openai, get_ai_metrics_from_response
from openai import OpenAI

CONFIG_KEY = os.environ.get("LD_AI_CONFIG_KEY", "report-summarizer-agent")
# The clean, Tessl-cleared skill. We deliberately point at the skill that passed
# `tessl review run security`; the risky one never reaches this agent.
SKILL_DIR = Path(__file__).resolve().parents[1] / "skills-content" / "demo" / "report-summarizer"


def die(msg: str) -> "NoReturn":  # noqa: F821
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def load_cleared_skill(skill_dir: Path) -> str:
    """Load a skill only if its directory carries a passing Tessl review result.

    `tessl-review-result.json` is the real `tessl review run security --json`
    output, committed alongside the skill when it last passed review. This is
    the actual gate: an unreviewed or failing skill has no such file (or one
    with verdict != "pass"), and this function refuses to load it either way.
    """
    skill_md = skill_dir / "SKILL.md"
    review_path = skill_dir / "tessl-review-result.json"

    if not review_path.is_file():
        die(f"no Tessl review result at {review_path}. Refusing to load an unreviewed skill.")
    try:
        review = json.loads(review_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        die(f"{review_path} is not valid JSON ({exc}). Refusing to load the skill.")
    if review.get("verdict") != "pass":
        die(
            f"{skill_dir.name} has not passed its Tessl security review "
            f"(verdict={review.get('verdict')!r}). Refusing to load it."
        )

    if not skill_md.is_file():
        die(f"cleared skill not found at {skill_md}")
    return skill_md.read_text(encoding="utf-8")


def main() -> None:
    sdk_key = os.environ.get("LD_SDK_KEY")
    if not sdk_key:
        die("LD_SDK_KEY is not set. The agent's config lives in AgentControl.")
    if not os.environ.get("OPENAI_API_KEY"):
        die("OPENAI_API_KEY is not set.")

    # The report we want summarized (stdin, or a short built-in sample).
    report_text = sys.stdin.read().strip() if not sys.stdin.isatty() else (
        "Q3 infra review: p99 latency fell 22% after the cache rollout; error "
        "budget spend held at 31%; one SEV-2 (config drift) cost 40 minutes. "
        "Cloud spend up 8% on increased egress. Recommend capping egress and "
        "promoting the cache change to all regions."
    )

    # 1. Initialize the LD client ONCE. Fail fast if it can't connect.
    ldclient.set_config(Config(sdk_key))
    client = ldclient.get()
    if not client.is_initialized():
        die("LaunchDarkly SDK failed to initialize. Cannot fetch the config.")
    ai_client = LDAIClient(client)

    # 2. Fetch the config from AgentControl. The default is DISABLED on purpose:
    #    it exists only to satisfy the SDK signature. If LD isn't serving an
    #    enabled variation, we treat that as fatal rather than falling back.
    context = Context.builder("tutorial-demo-user").kind("user").build()
    disabled_default = AICompletionConfigDefault(enabled=False)
    config = ai_client.completion_config(
        CONFIG_KEY,
        context,
        disabled_default,
        variables={"report_text": report_text},
    )

    if not config.enabled:
        die(
            f"AgentControl config '{CONFIG_KEY}' is not being served (enabled=False). "
            "Check that targeting is on for this environment and the fallthrough "
            "points at an enabled variation. This agent has no hardcoded fallback."
        )

    # 3. Load the security-cleared skill and prepend it to the served messages.
    skill = load_cleared_skill(SKILL_DIR)
    messages = convert_messages_to_openai(config.messages)
    messages = [
        {"role": "system", "content": f"You have access to this reviewed skill:\n\n{skill}"},
        *messages,
    ]

    # 4. Run the completion, tracking duration/tokens/success back to LaunchDarkly.
    tracker = config.create_tracker()
    openai_client = OpenAI()
    model_params = config.model.to_dict().get("parameters") or {}
    completion = tracker.track_metrics_of(
        get_ai_metrics_from_response,
        lambda: openai_client.chat.completions.create(
            model=config.model.name,
            messages=messages,
            **model_params,
        ),
    )
    client.flush()

    print(completion.choices[0].message.content.strip())
    print(
        "\n---\n"
        f"Served by AgentControl config '{CONFIG_KEY}' "
        f"(model={config.model.name}). Metrics sent to LaunchDarkly."
    )


if __name__ == "__main__":
    main()
