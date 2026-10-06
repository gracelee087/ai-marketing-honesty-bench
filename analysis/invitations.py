"""Deterministic invitation cues, added after inspecting the benchmark outputs.

This detects explicit requests/offers, not sales effectiveness or all possible CTAs.
Absence means no recognized cue. Bare product words and question marks do not count.
"""
import re

RULE_VERSION = "invitation-cues-2"
ACTION = r"(?:call|chat|talk|discuss|meet|connect|schedule|book|show|walk|share|send|answer|tell|hear|learn|join|sign|try|explore|visit|download|reply|respond|contact|reach|check|take|get|start|consider|discover)"
REQUESTS = [
    rf"\b(?:would|could|can|may)\s+(?:you|we|i)\b.{{0,130}}?\b{ACTION}\b",
    r"\b(?:are you|would you be)\s+(?:open|available|interested|free|up)\b",
    r"\b(?:do you|would you)\s+(?:have|spare)\b.{0,50}\b(?:minutes?|time|moment)\b",
    rf"\b(?:would|do)\s+you\s+(?:like|want)\b.{{0,90}}\b{ACTION}\b",
    rf"\b(?:i|we)(?:['’]d| would|['’]m| am|['’]re| are)\s+(?:be\s+)?(?:happy|glad|love|like|delighted)\s+to\s+{ACTION}\b",
    rf"\b(?:happy|glad)\s+to\s+{ACTION}\b",
    rf"\b(?:feel free to|you can|you could|you are welcome to|you['’]re welcome to|invite you to)\s+{ACTION}\b",
    r"\blet\s+(?:me|us|our team)\s+know\b",
    rf"\blet['’]s\s+{ACTION}\b",
    rf"(?:^|[,;:]\s*|\bplease\s+){ACTION}\b",
    r"\b(?:any questions|your thoughts|hear from you)\b",
]
REQUEST = [re.compile(p, re.I) for p in REQUESTS]
CONVERSATION = re.compile(
    r"\b(?:call(?!\s+(?:log|record|management))|chat|demo|demonstration|meeting(?!\s+brief)|"
    r"conversation(?!\s+summar)|discussion|walkthrough|walk-through|talk|discuss|meet)\b|"
    r"\b(?:\d{1,2}|a few|five|ten|fifteen|twenty)[- ]minutes?\b", re.I)


def invitation_evidence(text: str) -> dict:
    """Return the first recognized cue, preferring an explicit conversation invitation."""
    sentences = re.split(r"(?<=[.!?])\s+|\n+", text)
    invitation = None
    for sentence in sentences:
        sentence = sentence.strip().lstrip("-*").strip()
        if not sentence or re.match(r"^(?:subject|to|from):", sentence, re.I):
            continue
        match = next((m for pattern in REQUEST if (m := pattern.search(sentence))), None)
        if match is None:
            continue
        item = {"level": "invitation", "cue": match.group(0), "sentence": sentence}
        if CONVERSATION.search(sentence):
            return dict(item, level="conversation")
        if invitation is None:
            invitation = item
    return invitation or {"level": "none", "cue": "", "sentence": ""}


def classify_invitation(text: str) -> str:
    return invitation_evidence(text)["level"]
