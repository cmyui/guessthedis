import json

from guessthedis import state


class TestFormatTime:
    def test_seconds_only(self) -> None:
        assert state.format_time(4.21) == "4.2s"

    def test_rounds_correctly(self) -> None:
        assert state.format_time(4.25) == "4.2s"

    def test_minutes_and_seconds(self) -> None:
        assert state.format_time(95.3) == "1m 35.3s"

    def test_exactly_60(self) -> None:
        assert state.format_time(60.0) == "1m 0.0s"

    def test_zero(self) -> None:
        assert state.format_time(0.0) == "0.0s"


class TestEmptyState:
    def test_has_expected_keys(self) -> None:
        s = state._empty_state()
        assert s["version"] == state.CURRENT_VERSION
        assert s["challenge_bests"] == {}
        assert s["session_bests"] == {}


class TestLoadState:
    def test_first_run(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(state, "STATE_DIR", tmp_path)
        monkeypatch.setattr(state, "STATE_FILE", tmp_path / "state.json")
        s = state.load_state()
        assert s["version"] == state.CURRENT_VERSION
        assert s["challenge_bests"] == {}

    def test_valid_file(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(state, "STATE_DIR", tmp_path)
        state_file = tmp_path / "state.json"
        monkeypatch.setattr(state, "STATE_FILE", state_file)
        data = {
            "version": 1,
            "challenge_bests": {"no_op_pass": 4.21},
            "session_bests": {},
        }
        state_file.write_text(json.dumps(data))
        s = state.load_state()
        assert s["challenge_bests"]["no_op_pass"] == 4.21

    def test_corrupted_json_returns_read_only(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(state, "STATE_DIR", tmp_path)
        state_file = tmp_path / "state.json"
        monkeypatch.setattr(state, "STATE_FILE", state_file)
        state_file.write_text("not valid json{{{")
        s = state.load_state()
        assert s["challenge_bests"] == {}
        assert s.get(state._READ_ONLY_KEY) is True

    def test_newer_version_returns_read_only(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(state, "STATE_DIR", tmp_path)
        state_file = tmp_path / "state.json"
        monkeypatch.setattr(state, "STATE_FILE", state_file)
        data = {"version": 999, "challenge_bests": {}, "session_bests": {}}
        state_file.write_text(json.dumps(data))
        s = state.load_state()
        assert s["version"] == state.CURRENT_VERSION
        assert s.get(state._READ_ONLY_KEY) is True

    def test_invalid_structure_returns_read_only(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(state, "STATE_DIR", tmp_path)
        state_file = tmp_path / "state.json"
        monkeypatch.setattr(state, "STATE_FILE", state_file)
        state_file.write_text(json.dumps([1, 2, 3]))
        s = state.load_state()
        assert s.get(state._READ_ONLY_KEY) is True

    def test_missing_keys_filled(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(state, "STATE_DIR", tmp_path)
        state_file = tmp_path / "state.json"
        monkeypatch.setattr(state, "STATE_FILE", state_file)
        state_file.write_text(json.dumps({"version": 1}))
        s = state.load_state()
        assert "challenge_bests" in s
        assert "session_bests" in s


class TestSaveState:
    def test_round_trip(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(state, "STATE_DIR", tmp_path)
        state_file = tmp_path / "state.json"
        monkeypatch.setattr(state, "STATE_FILE", state_file)
        data = state._empty_state()
        data["challenge_bests"]["foo"] = 1.23
        state.save_state(data)
        loaded = state.load_state()
        assert loaded["challenge_bests"]["foo"] == 1.23

    def test_read_only_skips_write(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(state, "STATE_DIR", tmp_path)
        state_file = tmp_path / "state.json"
        monkeypatch.setattr(state, "STATE_FILE", state_file)
        original_content = "not valid json{{{"
        state_file.write_text(original_content)
        s = state.load_state()
        s["challenge_bests"]["foo"] = 1.23
        state.save_state(s)
        assert state_file.read_text() == original_content

    def test_newer_version_preserves_file(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(state, "STATE_DIR", tmp_path)
        state_file = tmp_path / "state.json"
        monkeypatch.setattr(state, "STATE_FILE", state_file)
        original = {"version": 999, "challenge_bests": {"x": 1.0}, "session_bests": {}}
        state_file.write_text(json.dumps(original))
        s = state.load_state()
        s["challenge_bests"]["foo"] = 1.23
        state.save_state(s)
        assert json.loads(state_file.read_text()) == original


class TestGetChallengeBest:
    def test_existing(self) -> None:
        s = {"challenge_bests": {"foo": 4.21}, "session_bests": {}}
        assert state.get_challenge_best(s, "foo") == 4.21

    def test_missing(self) -> None:
        s = {"challenge_bests": {}, "session_bests": {}}
        assert state.get_challenge_best(s, "foo") is None


class TestRecordChallengeTime:
    def test_first_time(self) -> None:
        s = {"challenge_bests": {}, "session_bests": {}, "version": 1}
        prev = state.record_challenge_time(s, "foo", 5.0)
        assert prev is None
        assert s["challenge_bests"]["foo"] == 5.0

    def test_new_best(self) -> None:
        s = {"challenge_bests": {"foo": 5.0}, "session_bests": {}, "version": 1}
        prev = state.record_challenge_time(s, "foo", 3.0)
        assert prev == 5.0
        assert s["challenge_bests"]["foo"] == 3.0

    def test_not_beaten(self) -> None:
        s = {"challenge_bests": {"foo": 3.0}, "session_bests": {}, "version": 1}
        prev = state.record_challenge_time(s, "foo", 5.0)
        assert prev is None
        assert s["challenge_bests"]["foo"] == 3.0


class TestRecordSessionTime:
    def test_first_time(self) -> None:
        s = {"challenge_bests": {}, "session_bests": {}, "version": 1}
        prev = state.record_session_time(s, "all", 100.0)
        assert prev is None
        assert s["session_bests"]["all"] == 100.0

    def test_new_best(self) -> None:
        s = {"challenge_bests": {}, "session_bests": {"all": 100.0}, "version": 1}
        prev = state.record_session_time(s, "all", 80.0)
        assert prev == 100.0
        assert s["session_bests"]["all"] == 80.0

    def test_not_beaten(self) -> None:
        s = {"challenge_bests": {}, "session_bests": {"all": 80.0}, "version": 1}
        prev = state.record_session_time(s, "all", 100.0)
        assert prev is None
        assert s["session_bests"]["all"] == 80.0
