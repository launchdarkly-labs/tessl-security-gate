# Demo agent — what happens after the security gate

`summarize_agent.py` is the second half of the tutorial's story. The Tessl
security review is the on-ramp: it clears a skill before you trust it. This
agent is the highway: it loads the cleared skill and runs it, but takes its
**model and prompt from LaunchDarkly AgentControl** instead of hardcoding them.

## What it demonstrates

- **Config lives in AgentControl, not the code.** The system/user prompt and the
  model come from the AgentControl config `report-summarizer-agent`. Change the
  model or prompt in LaunchDarkly and the agent picks it up — no redeploy.
- **No config, no agent.** There is no hardcoded prompt fallback. If LaunchDarkly
  isn't serving an enabled variation (missing SDK key, LD unreachable, or
  targeting off), the agent exits non-zero instead of quietly running on a
  default.
- **Only runs a cleared skill.** It loads `../skills-content/demo/report-summarizer`,
  and checks the `tessl-review-result.json` committed next to it for
  `verdict: "pass"` before it ever reads `SKILL.md`. No passing result on file,
  no skill — the check is real, not just a comment.
- **Metrics flow back.** Duration, tokens, and success are tracked to
  LaunchDarkly via `tracker.track_metrics_of`.

## Run it

```bash
pip install -r requirements.txt
cp .env.example .env    # fill in LD_SDK_KEY + OPENAI_API_KEY
set -a; source .env; set +a

echo "Your report text here..." | python summarize_agent.py
```

You need an AgentControl config named `report-summarizer-agent` (completion mode)
with targeting on in the environment your `LD_SDK_KEY` points at. Create it with
the [`configs-create`](https://launchdarkly.com/docs) flow, or adapt
`LD_AI_CONFIG_KEY` to point at your own.
