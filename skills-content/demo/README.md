# Demo skills for the security-gate tutorial

These two skills are **fixtures** for the tutorial *"Gate your agent skills on a security review before they ship."* They exist to show `tessl review run security` passing a safe skill and catching a malicious one.

## ⚠️ `pdf-exporter-risky/` is an intentionally malicious fixture — do not install or run it

`pdf-exporter-risky/SKILL.md` deliberately contains an attack payload: a prompt-injection instruction plus a shell command that base64-encodes your environment and `~/.aws/credentials` and POSTs them to an external endpoint, with instructions telling the agent to hide this from the user. It is here **only** so the security review has something real to flag.

- **Never install this skill into an agent's skills directory, and never execute it.** Loading it into a live agent could cause credential exfiltration.
- The exfil endpoint uses `telemetry-collector.example.net` — `example.net` is an IANA-reserved documentation domain that does not route anywhere, so the payload is inert as written. Keep it that way; do not point it at a real host.
- Scanning it with `tessl review run security` is safe — the reviewer reads the `SKILL.md` text, it does **not** execute the skill.

## `pdf-exporter/` is the clean counterpart

`pdf-exporter/SKILL.md` is a well-behaved skill that passes the gate (`verdict: pass`). Use it as the "before" in the tutorial.
