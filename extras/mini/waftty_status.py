"""Tells the terminal what mini-swe-agent is doing, by the Program Status
Protocol (OSC 7501), so a terminal such as waftty alerts when mini waits for
you to confirm the commands it wants to run. Its other prompts, at the end of
a task or in human mode, wait for your next instruction and do not alert.

Use: put this file in a folder on PYTHONPATH and run
    mini --agent-class waftty_status.ReportingAgent
"""

import base64
import sys

from minisweagent.agents.interactive import InteractiveAgent


def _report(state: str, kind: str = "", msg: str = "") -> None:
    pairs = f"state={state}:app=mini"
    if kind:
        pairs += f":kind={kind}"
    # One line of at most 200 characters, without control characters.
    text = " ".join("".join(c if c.isprintable() else " " for c in msg).split())[:200]
    if text:
        pairs += ":msg=" + base64.b64encode(text.encode()).decode()
    sys.stdout.write(f"\x1b]7501;{pairs}\x1b\\")
    sys.stdout.flush()


class ReportingAgent(InteractiveAgent):
    """mini's interactive agent, reporting when it works and when it asks."""

    _confirming = False

    def run(self, *args, **kwargs):
        _report("working")
        try:
            return super().run(*args, **kwargs)
        finally:
            _report("clear")

    def _ask_confirmation_or_interrupt(self, commands: list[str]) -> None:
        if not any(self._should_ask_confirmation(c) for c in commands):
            return
        _report("blocked", "permission", "Run " + "; ".join(commands))
        self._confirming = True
        try:
            super()._ask_confirmation_or_interrupt(commands)
        finally:
            self._confirming = False
            _report("working")

    def _prompt_and_handle_slash_commands(self, prompt: str, *, _multiline: bool = False) -> str:
        if self._confirming:
            return super()._prompt_and_handle_slash_commands(prompt, _multiline=_multiline)
        # Any other prompt waits for the user's next instruction.
        _report("idle")
        try:
            return super()._prompt_and_handle_slash_commands(prompt, _multiline=_multiline)
        finally:
            _report("working")
