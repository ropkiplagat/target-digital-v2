"""Target Digital AI reception canon tests.

The routing tests are the ones that matter. A false negative here means someone
describing a heart attack gets offered a Tuesday appointment.

    py mcp-server/test_canon.py
"""
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from canon import (CanonError, assess_fit, classify_caller_utterance,  # noqa: E402
                   safety_rules, what_we_will_not_claim)

FAILURES = []


def check(name, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + name + (("  " + str(detail)) if not cond else ""))
    if not cond:
        FAILURES.append(name)


print("\nEmergencies stop the call")
for line in ["I've got chest pain and it's getting worse",
             "my husband collapsed and is unconscious",
             "she can't breathe properly",
             "I think I'm having a heart attack"]:
    r = classify_caller_utterance(line)
    check("routes to emergency: %r" % line[:38], r["route"] == "emergency", r["route"])
    check("  ...and forbids booking", "book an appointment" in r["must_not"])

print("\nUrgency beats advice when a sentence is both")
# The trap: this is a medication question wrapped around a cardiac symptom.
# Checking advice first would answer about aspirin and miss the heart attack.
r = classify_caller_utterance("I have chest pain, should I take an aspirin?")
check("chest pain + 'should i take' routes to EMERGENCY, not advice",
      r["route"] == "emergency", r["route"])

print("\nClinical advice is refused, not answered")
for line in ["should I take more of my antibiotics",
             "is this normal after a filling",
             "what dose do I give a child"]:
    r = classify_caller_utterance(line)
    check("refuses advice: %r" % line[:38], r["route"] == "clinical_advice_refused", r["route"])
    check("  ...and forbids answering", "answer the clinical question" in r["must_not"])

print("\nOrdinary reception traffic still works")
for line in ["can I move my Tuesday appointment to Thursday",
             "what time do you close on Saturday",
             "is there parking out the front"]:
    r = classify_caller_utterance(line)
    check("handled as reception: %r" % line[:38], r["route"] == "reception", r["route"])

print("\nEmpty input is refused rather than silently routed")
try:
    classify_caller_utterance("   ")
    check("empty utterance raises", False, "no error")
except CanonError:
    check("empty utterance raises", True)

print("\nFit assessment does not assume unknowns are favourable")
r = assess_fit()
check("no inputs -> more_information_needed", r["verdict"] == "more_information_needed", r["verdict"])
check("all four signals listed as unknown", len(r["unknown"]) == 4, r["unknown"])

r = assess_fit(appointment_led=True, misses_calls_after_hours=True,
               front_desk_overloaded=True, calls_are_complex_sales=False)
check("three positives -> likely_fit", r["verdict"] == "likely_fit", r["verdict"])

r = assess_fit(appointment_led=True, misses_calls_after_hours=True,
               front_desk_overloaded=True, calls_are_complex_sales=True)
check("a disqualifier outweighs three positives",
      r["verdict"] == "probably_not_a_fit", r["verdict"])

print("\nNo pricing and no guarantees anywhere in any output")
MONEY = re.compile(r"\$\s*\d|\b\d+\s*/\s*mo\b|\bper month\b|\bsetup fee\b", re.I)
GUARANTEE = re.compile(r"\bguarantee|\bbest in\b|\bnumber one\b|\b#1\b", re.I)
blobs = [repr(safety_rules()), repr(assess_fit(True, True, True, False)),
         repr(classify_caller_utterance("can I book for Friday")),
         repr(what_we_will_not_claim())]
for i, b in enumerate(blobs):
    m = MONEY.search(b)
    check("no price token in output %d" % i, not m, m.group(0) if m else "")
    g = GUARANTEE.search(b)
    # the refusals text is allowed to say the word while refusing it
    allowed = "refus" in b.lower() or "No guaranteed" in b
    check("no unsubstantiated guarantee in output %d" % i, (not g) or allowed,
          g.group(0) if g else "")

print("\nPricing is an explicit refusal, not an omission")
r = what_we_will_not_claim("pricing")
check("pricing is refused", r["refused"] is True)
check("...and says where the number is settled", "scoping call" in r["because"])

print("\n" + "-" * 58)
if FAILURES:
    print("FAILED: %d\n  %s" % (len(FAILURES), "\n  ".join(FAILURES)))
    sys.exit(1)
print("All Target Digital canon tests passed.")
