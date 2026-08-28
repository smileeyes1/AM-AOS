from am_aos.project_controller import GateStatus, ProjectState, ProjectStateStore


def test_state_round_trip(tmp_path):
    path = tmp_path / "state.json"
    state = ProjectState.initial("G3", "integrate capability guard")
    state = ProjectState("G3", GateStatus.NO_GO, "abc123", "pytest", state.next_action, ("api",), "NOT-RELEASED", state.updated_at)
    store = ProjectStateStore(path)
    store.save(state)
    assert store.load() == state


def test_save_is_atomic_and_creates_parent(tmp_path):
    path = tmp_path / "nested" / "state.json"
    store = ProjectStateStore(path)
    store.save(ProjectState.initial("G3", "next"))
    assert path.exists()
    assert not path.with_suffix(".json.tmp").exists()
