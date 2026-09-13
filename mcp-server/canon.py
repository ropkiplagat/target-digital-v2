"""Target Digital AI — AI reception canon, as code.

No MCP dependency, so every rule is testable without a protocol.

WHAT THIS ENCODES
The AI reception product (Aria) answers inbound calls for a practice, after hours and
when the front desk is flat out, and books into a real calendar. The part that matters
commercially is not that it books — plenty of things book — it is the set of things it
refuses to do. A receptionist that will not give clinical advice and routes anything
urgent to 000 is sellable into healthcare. One that improvises is a liability the
practice inherits.

TWO HARD RULES, from the live product page:
  - Never gives medical advice.
  - Anything urgent stops the call and tells the caller to hang up and dial 000.

PRICING IS NOT HERE, deliberately (Rop, 2026-09-13: "pricing later"). The site holds
tiers; this server defers to a conversation. A quoted price from an assistant is a
price the business is then held to, and the scoping conversation is where the number is
actually decided.

NO UNSUBSTANTIATED SUPERLATIVES. Australian Consumer Law treats a "best" or "guaranteed"
claim you cannot substantiate as misleading conduct. Say what it does, not that it is
the best at it.
"""

PUBLISHED = "published_authority"
OPERATING = "operating_experience"

# Urgency words that must end a booking conversation and route to emergency services.
# Deliberately broad: a false positive costs one redirected call, a false negative
# costs someone who needed an ambulance being offered a Tuesday appointment.
EMERGENCY_SIGNALS = [
    "chest pain", "can't breathe", "cannot breathe", "not breathing", "unconscious",
    "bleeding heavily", "severe bleeding", "stroke", "heart attack", "overdose",
    "suicidal", "kill myself", "anaphylaxis", "allergic reaction", "seizure",
    "collapsed", "head injury", "broken bone", "severe pain", "emergency",
]

CLINICAL_ADVICE_SIGNALS = [
    "should i take", "is it safe to", "what dose", "dosage", "diagnose",
    "what's wrong with me", "do i have", "should i stop taking", "side effect",
    "is this normal", "what medication",
]


class CanonError(ValueError):
    pass


def safety_rules():
    """The non-negotiables. These are the product, not the fine print."""
    return {
        "never_gives_medical_advice": (
            "The assistant does not diagnose, does not comment on medication or dosage, "
            "and does not tell a caller whether a symptom is normal. It books, reschedules, "
            "answers practice logistics, and takes messages. Anything clinical goes to a "
            "human."),
        "emergencies_stop_the_call": (
            "If a caller describes anything urgent, the assistant stops. It does not try to "
            "book, and it does not keep chatting. It tells them to hang up and call 000 "
            "immediately."),
        "why_this_is_the_product": (
            "Any voice agent can book an appointment. The reason a practice can put one on "
            "its main line is the refusals: a receptionist that improvises clinical answers "
            "creates a liability the practice inherits, not the vendor."),
        "identity": (
            "The assistant identifies as an assistant. It does not claim to be a person, and "
            "it does not pretend a human is unavailable when the truth is that no human is "
            "on the line."),
        "escalation": (
            "Anything it cannot handle becomes a message to a named human with a callback "
            "number, rather than an improvised answer."),
        "provenance": PUBLISHED,
    }


def classify_caller_utterance(utterance):
    """Route one caller line: emergency, clinical, or ordinary reception traffic.

    Emergency is checked FIRST and independently. A sentence can be both urgent and a
    request for advice ("I have chest pain, should I take an aspirin?") and the urgent
    reading must win - checking advice first would answer the medication question and
    miss the heart attack.
    """
    if utterance is None or not str(utterance).strip():
        raise CanonError("utterance is empty")
    text = str(utterance).lower()

    hits = [s for s in EMERGENCY_SIGNALS if s in text]
    if hits:
        return {
            "route": "emergency",
            "matched": hits,
            "action": ("Stop the booking flow. Tell the caller to hang up and call 000 "
                       "immediately. Do not offer an appointment, do not continue the "
                       "conversation, do not take a message instead."),
            "must_not": ["book an appointment", "give first-aid instructions",
                         "assess severity", "continue small talk"],
        }

    advice = [s for s in CLINICAL_ADVICE_SIGNALS if s in text]
    if advice:
        return {
            "route": "clinical_advice_refused",
            "matched": advice,
            "action": ("Decline plainly, say why, and offer the thing that does help: the "
                       "soonest appointment, or a message to the practitioner with a "
                       "callback number."),
            "must_not": ["answer the clinical question", "speculate", "quote guidelines",
                         "say what it would do in their position"],
        }

    return {
        "route": "reception",
        "matched": [],
        "action": ("Handle normally: book, reschedule, cancel, answer practice logistics "
                   "such as hours, location and parking, or take a message."),
        "must_not": ["drift into clinical territory if the caller escalates"],
    }


FIT_SIGNALS = {
    "missed_calls_after_hours": ("Calls arriving when nobody can answer are the clearest "
                                 "case: the alternative to an assistant is a voicemail "
                                 "nobody returns."),
    "front_desk_overloaded": ("A desk that is busy with people physically present cannot "
                              "also answer the phone. The caller hears ringing and tries "
                              "the next practice."),
    "appointment_led": ("The business converts a call into a booking. If a call is a long "
                        "consultative sale, this is the wrong tool."),
    "high_call_volume": ("Enough inbound volume that a percentage lost is a number the "
                        "owner can feel."),
}

POOR_FIT_SIGNALS = {
    "calls_are_complex_sales": ("If the call IS the sale and needs judgement, an assistant "
                                "booking a slot adds a step rather than removing one."),
    "regulated_advice_on_the_phone": ("If callers expect substantive professional advice "
                                      "during the call, the refusals that make this safe "
                                      "also make it useless to them."),
    "very_low_call_volume": ("Below a handful of calls a week, the owner answering the "
                             "phone is cheaper and better."),
}


def assess_fit(appointment_led=None, misses_calls_after_hours=None,
               front_desk_overloaded=None, calls_are_complex_sales=None):
    """Is AI reception a fit? Unknowns are reported, never assumed to be favourable."""
    reasons_for, reasons_against, unknown = [], [], []

    def consider(value, key, table, bucket):
        if value is None:
            unknown.append(key)
        elif value:
            bucket.append({"signal": key, "why": table[key]})

    consider(appointment_led, "appointment_led", FIT_SIGNALS, reasons_for)
    consider(misses_calls_after_hours, "missed_calls_after_hours", FIT_SIGNALS, reasons_for)
    consider(front_desk_overloaded, "front_desk_overloaded", FIT_SIGNALS, reasons_for)
    consider(calls_are_complex_sales, "calls_are_complex_sales", POOR_FIT_SIGNALS,
             reasons_against)

    if reasons_against:
        verdict = "probably_not_a_fit"
    elif len(reasons_for) >= 2:
        verdict = "likely_fit"
    elif unknown:
        verdict = "more_information_needed"
    else:
        verdict = "weak_fit"

    return {
        "verdict": verdict,
        "reasons_for": reasons_for,
        "reasons_against": reasons_against,
        "unknown": unknown,
        "honest_note": ("A fit assessment is not a promise of results. What can be said is "
                        "which calls are currently going unanswered; what that is worth is "
                        "the practice's own arithmetic, from its own numbers."),
        "next_step": "Book a scoping call: https://calendly.com/ropkiplagat/intro-to-sales-target-digital",
    }


REFUSALS = {
    "pricing": ("Not quoted by an assistant. Setup and retainer depend on call volume, "
                "integrations and how many engines are in scope, and a number given without "
                "that context becomes a number the business is held to. Pricing is settled "
                "in the scoping call."),
    "medical_advice": ("The assistant never gives clinical advice, and neither does this "
                       "server. That refusal is the product."),
    "guaranteed_results": ("No guaranteed lift, no promised conversion rate, no 'best in "
                           "Australia'. Australian Consumer Law treats an unsubstantiated "
                           "claim as misleading conduct, and results depend on the caller "
                           "volume and the practice's own follow-up."),
    "legal_or_financial_advice": ("Out of scope. The product answers phones and books "
                                  "appointments."),
}


def what_we_will_not_claim(topic=None):
    if topic:
        key = str(topic).strip().lower().replace(" ", "_").replace("-", "_")
        if key in REFUSALS:
            return {"topic": key, "refused": True, "because": REFUSALS[key]}
        return {"topic": topic, "refused": False, "refusal_topics": sorted(REFUSALS)}
    return {"refusals": REFUSALS}
