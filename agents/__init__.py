"""Agent registry: one AgentSpec per supported agent (cc-switch parity).

Sidebar order follows cc-switch: claude, claude-desktop, codex, gemini,
grokbuild, opencode, openclaw, hermes, pi. get_agent() is the single lookup
used by server.py.
"""
from agents.base import AgentSpec
from agents.claude import CLAUDE_SPEC
from agents.claude_desktop import CLAUDE_DESKTOP_SPEC
from agents.codex import CODEX_SPEC
from agents.gemini import GEMINI_SPEC
from agents.grokbuild import GROKBUILD_SPEC
from agents.opencode import OPENCODE_SPEC
from agents.openclaw import OPENCLAW_SPEC
from agents.hermes import HERMES_SPEC
from agents.pi import PI_SPEC

AGENT_REGISTRY: dict = {
    "claude": CLAUDE_SPEC,
    "claude-desktop": CLAUDE_DESKTOP_SPEC,
    "codex": CODEX_SPEC,
    "gemini": GEMINI_SPEC,
    "grokbuild": GROKBUILD_SPEC,
    "opencode": OPENCODE_SPEC,
    "openclaw": OPENCLAW_SPEC,
    "hermes": HERMES_SPEC,
    "pi": PI_SPEC,
}

VALID_APPS = set(AGENT_REGISTRY.keys())


def get_agent(app_type: str) -> AgentSpec:
    return AGENT_REGISTRY[app_type]


def registry_payload() -> list[dict]:
    """Serialize the registry for GET /api/agents."""
    return [
        {
            "id": s.id,
            "name": s.name,
            "icon": s.icon,
            "mode": s.mode,
            "configurable": s.configurable,
        }
        for s in AGENT_REGISTRY.values()
    ]
