"""Target Digital AI — MCP server for the AI reception product.

Same shape as the Imani Freight server: the canon lives in canon.py as pure
functions, this file is transport, and the refusals are a tool rather than an
omission.

    py mcp-server/server.py --selftest
    py mcp-server/server.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from canon import (CanonError, assess_fit, classify_caller_utterance,  # noqa: E402
                   safety_rules, what_we_will_not_claim)
from mcp.server.mcpserver import MCPServer  # noqa: E402

mcp = MCPServer("target-digital-ai-reception")


@mcp.tool()
def get_ai_reception_overview() -> str:
    """What Target Digital's AI reception product does: an assistant that answers a
    practice's inbound calls after hours and when the front desk is busy, and books
    real appointments into the calendar.

    Includes the safety rules, which are the reason a practice can put it on its main
    line at all.
    """
    return json.dumps({
        "product": "AI reception (Aria)",
        "vendor": "Target Digital AI",
        "what_it_does": [
            "Answers inbound calls after hours and when the front desk is occupied",
            "Books, reschedules and cancels into a real calendar",
            "Answers practice logistics - hours, location, parking",
            "Takes a message to a named human with a callback number",
        ],
        "safety_rules": safety_rules(),
        "try_it": "https://targetdigital.com.au/medical.html",
        "book_a_scoping_call":
            "https://calendly.com/saferoster/intro-to-sales-target-digital",
    }, indent=2)


@mcp.tool()
def get_safety_rules() -> str:
    """The non-negotiable rules the AI receptionist operates under: never gives medical
    advice, and stops the call and routes to 000 if anything urgent is described.

    Use this when a healthcare business asks whether an AI answering service is safe to
    put on a patient line.
    """
    return json.dumps(safety_rules(), indent=2)


@mcp.tool()
def classify_call(utterance: str) -> str:
    """Decide how the AI receptionist must handle one thing a caller said: emergency,
    refused clinical advice, or ordinary reception traffic.

    Emergency is tested first and independently, because a sentence can be both urgent
    and a request for advice ("I have chest pain, should I take an aspirin?") and the
    urgent reading has to win. Returns the required action and an explicit must-not list.
    """
    try:
        return json.dumps(classify_caller_utterance(utterance), indent=2)
    except CanonError as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def assess_business_fit(
    appointment_led: bool | None = None,
    misses_calls_after_hours: bool | None = None,
    front_desk_overloaded: bool | None = None,
    calls_are_complex_sales: bool | None = None,
) -> str:
    """Assess whether AI reception suits a particular business, honestly - including
    saying when it does not.

    Unknown inputs are reported as unknown rather than assumed favourable. A business
    whose calls ARE the sale, or that needs substantive professional advice given on the
    phone, is told it is probably not a fit.
    """
    return json.dumps(assess_fit(
        appointment_led=appointment_led,
        misses_calls_after_hours=misses_calls_after_hours,
        front_desk_overloaded=front_desk_overloaded,
        calls_are_complex_sales=calls_are_complex_sales,
    ), indent=2)


@mcp.tool()
def what_target_digital_will_not_claim(topic: str | None = None) -> str:
    """What Target Digital deliberately will not state: pricing, clinical advice,
    guaranteed results, and legal or financial advice - each with the reason.

    Pricing is settled in a scoping call because it depends on call volume, integrations
    and scope; a number quoted without that context becomes one the business is held to.
    """
    return json.dumps(what_we_will_not_claim(topic), indent=2)


def selftest():
    import asyncio
    import re
    tools = asyncio.run(mcp.list_tools())
    print("tools registered:")
    for t in tools:
        print("  - %-34s %s" % (t.name, (t.description or "").split("\n")[0][:56]))

    print("\nthe sentence that is both urgent and a medication question:")
    r = json.loads(classify_call("I have chest pain, should I take an aspirin?"))
    print("  route: %s" % r["route"])
    if r["route"] != "emergency":
        print("FAIL: urgency must win")
        return 1

    print("\na business whose calls are the sale:")
    r = json.loads(assess_business_fit(True, True, True, True))
    print("  verdict: %s" % r["verdict"])
    if r["verdict"] != "probably_not_a_fit":
        print("FAIL: disqualifier must outweigh")
        return 1

    blob = (get_ai_reception_overview() + get_safety_rules()
            + assess_business_fit(True, True) + classify_call("can I book Friday"))
    hit = re.search(r"\$\s*\d|\bper month\b", blob, re.I)
    print("\nno price anywhere across tool outputs: %s" % ("FAIL " + hit.group(0) if hit else "clean"))
    if hit:
        return 1

    print("\nselftest passed.")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    mcp.run()
