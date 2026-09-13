"""End-to-end test: launch server.py as a subprocess and speak MCP over stdio.

selftest() in server.py calls the tool functions directly, which proves the canon
but skips the transport entirely. This proves a real client can connect, list the
tools and get an answer back - the thing that actually has to work.

    py mcp-server/test_stdio.py
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.join(HERE, "server.py")


def main():
    proc = subprocess.Popen(
        [sys.executable, SERVER],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, bufsize=1, encoding="utf-8",
    )

    def send(obj):
        proc.stdin.write(json.dumps(obj) + "\n")
        proc.stdin.flush()

    def read():
        line = proc.stdout.readline()
        if not line:
            err = proc.stderr.read()
            raise SystemExit("server closed stdout. stderr:\n" + err[:3000])
        return json.loads(line)

    failures = []

    def check(name, cond, detail=""):
        print(("  PASS  " if cond else "  FAIL  ") + name + ("  " + str(detail) if not cond else ""))
        if not cond:
            failures.append(name)

    send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2025-06-18", "capabilities": {},
        "clientInfo": {"name": "td-stdio-test", "version": "1.0"}}})
    init = read()
    print("\nhandshake")
    check("initialize returns a result", "result" in init, init.get("error"))
    check("server identifies itself as target-digital-ai-reception",
          init.get("result", {}).get("serverInfo", {}).get("name") == "target-digital-ai-reception",
          init.get("result", {}).get("serverInfo"))

    send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    send({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    listed = read()
    names = [t["name"] for t in listed.get("result", {}).get("tools", [])]
    print("\ntools/list over the wire")
    for n in names:
        print("    - " + n)
    check("all three tools are exposed",
          {"classify_call", "get_safety_rules", "assess_business_fit"} <= set(names),
          names)

    print("\ntools/call - chest pain wrapped in a medication question")
    send({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
        "name": "classify_call",
        "arguments": {"utterance": "I have chest pain, should I take an aspirin?"}}})
    called = read()
    content = called.get("result", {}).get("content", [])
    text = content[0].get("text", "") if content else ""
    check("call returns content", bool(text), called.get("error"))
    if text:
        payload = json.loads(text)
        check("urgency wins over the medication question, over the wire",
              payload.get("route") == "emergency", payload.get("route"))
        check("booking is explicitly forbidden",
              "book an appointment" in payload.get("must_not", []), payload.get("must_not"))

    proc.stdin.close()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()

    print("\n" + "-" * 58)
    if failures:
        print("FAILED: %d\n  %s" % (len(failures), "\n  ".join(failures)))
        return 1
    print("stdio transport verified end to end.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
