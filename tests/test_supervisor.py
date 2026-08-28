from am_aos.supervisor import KillSwitch, Supervisor, SupervisorPolicy


def test_supervisor_replans_then_succeeds():
    attempts = []
    replans = []

    def step():
        attempts.append(1)
        return (len(attempts) >= 2, "done" if len(attempts) >= 2 else None)

    result = Supervisor(SupervisorPolicy(max_cycles=3, max_replans=2)).run(step, lambda n: replans.append(n))
    assert result.status == "SUCCESS"
    assert result.value == "done"
    assert result.replans == 1


def test_kill_switch_prevents_further_execution():
    switch = KillSwitch()
    switch.stop()
    calls = []
    result = Supervisor(kill_switch=switch).run(lambda: (calls.append(1), True)[1:])
    assert result.status == "STOPPED"
    assert calls == []
