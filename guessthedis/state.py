"""Persistent state: personal-best times for challenges and sessions."""

import contextlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

_YELLOW = "\x1b[33m"
_RESET = "\x1b[m"


def format_time(seconds: float) -> str:
    """Format seconds as a human-readable time string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    remaining = seconds % 60
    return f"{minutes}m {remaining:.1f}s"


CURRENT_VERSION = 1
STATE_DIR = Path.home() / ".guessthedis"
STATE_FILE = STATE_DIR / "state.json"

_READ_ONLY_KEY = "_read_only"


def _empty_state(*, read_only: bool = False) -> dict[str, Any]:
    state: dict[str, Any] = {
        "version": CURRENT_VERSION,
        "challenge_bests": {},
        "session_bests": {},
    }
    if read_only:
        state[_READ_ONLY_KEY] = True
    return state


def load_state() -> dict[str, Any]:
    """Load state from disk, returning empty state on first run or corruption.

    When the existing file cannot be parsed (corruption, newer version),
    the returned state is marked read-only so that ``save_state`` will
    refuse to overwrite the file on disk.
    """
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    if not STATE_FILE.exists():
        return _empty_state()

    try:
        data = json.loads(STATE_FILE.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        print(f"{_YELLOW}Corrupted state file, starting fresh in memory: {exc}{_RESET}")
        return _empty_state(read_only=True)

    if not isinstance(data, dict) or "version" not in data:
        print(
            f"{_YELLOW}Invalid state file structure, starting fresh in memory{_RESET}",
        )
        return _empty_state(read_only=True)

    if data["version"] > CURRENT_VERSION:
        print(
            f"{_YELLOW}State file version {data['version']} is newer than "
            f"supported ({CURRENT_VERSION}), starting fresh in memory{_RESET}",
        )
        return _empty_state(read_only=True)

    # ensure expected keys exist
    data.setdefault("challenge_bests", {})
    data.setdefault("session_bests", {})
    return data


def save_state(state: dict[str, Any]) -> None:
    """Atomically write state to disk via temp file + os.replace().

    Skips writing if the state is marked read-only (i.e. the existing
    file on disk could not be loaded and should not be overwritten).
    """
    if state.get(_READ_ONLY_KEY):
        print(
            f"{_YELLOW}State is read-only, skipping save to preserve existing file{_RESET}",
        )
        return

    STATE_DIR.mkdir(parents=True, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(dir=STATE_DIR, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(state, f, indent=2)
            f.write("\n")
        os.replace(tmp_path, STATE_FILE)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp_path)
        raise


def get_challenge_best(state: dict[str, Any], func_name: str) -> float | None:
    """Return the best time for a challenge, or None if never completed."""
    best = state["challenge_bests"].get(func_name)
    return float(best) if best is not None else None


def record_challenge_time(
    state: dict[str, Any],
    func_name: str,
    elapsed: float,
) -> float | None:
    """Record a challenge time, returning the previous best if beaten.

    Mutates state in-place but does NOT save to disk.
    """
    prev = get_challenge_best(state, func_name)
    if prev is None or elapsed < prev:
        state["challenge_bests"][func_name] = elapsed
        return prev
    return None


def record_session_time(
    state: dict[str, Any],
    session_key: str,
    elapsed: float,
) -> float | None:
    """Record a session time, returning the previous best if beaten.

    Mutates state in-place but does NOT save to disk.
    """
    prev = state["session_bests"].get(session_key)
    prev_f = float(prev) if prev is not None else None
    if prev_f is None or elapsed < prev_f:
        state["session_bests"][session_key] = elapsed
        return prev_f
    return None
