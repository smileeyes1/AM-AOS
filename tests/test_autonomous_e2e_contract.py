from pathlib import Path


def test_required_autonomous_e2e_artifacts_are_present():
    root = Path(__file__).parents[1]
    required = [
        root / "src/am_aos/controller.py",
        root / "src/am_aos/task_queue.py",
        root / "src/am_aos/worker.py",
        root / "src/am_aos/gates.py",
        root / "src/am_aos/delivery.py",
        root / "docs/AUTONOMOUS_COMPLETION_CONTROL_SPEC_v1.0.md",
        root / "docs/FINAL_USER_DELIVERY_POLICY_v1.0.md",
    ]
    missing = [str(p.relative_to(root)) for p in required if not p.is_file()]
    assert not missing, f"missing autonomous control artifacts: {missing}"
