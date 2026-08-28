import argparse

from .api import serve
from .runtime import AMAOSEngine


def self_check() -> None:
    e = AMAOSEngine()
    m = e.create_mission(
        "self-check",
        ["execution succeeds"],
        ["constitutional-boundary"],
        ["execute"],
        "local",
    )
    e.register_agent("self", {"execute"}, lambda task: True)
    t = e.add_task(m, "self check", "execute", "local-verifier")
    assert e.execute(t, "self").value == "PASS"
    e.capture_regression_baseline()
    assert e.regression_check()
    assert e.audit.verify_chain()
    print("SELF-CHECK PASS")


def main() -> None:
    p = argparse.ArgumentParser(prog="am-aos")
    p.add_argument("--self-check", action="store_true")
    p.add_argument("--serve", action="store_true")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8080)
    args = p.parse_args()
    if args.self_check:
        self_check()
        return
    if args.serve:
        serve(AMAOSEngine(), args.host, args.port)
        return
    p.error("choose --self-check or --serve")


if __name__ == "__main__":
    main()
