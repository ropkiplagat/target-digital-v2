# Target Digital AI — MCP server (AI reception)

Five tools covering the AI reception product. Same shape as the Imani Freight server:
canon as pure functions in `canon.py`, `server.py` is transport, refusals are a tool.

```
py mcp-server/test_canon.py     # the rules
py mcp-server/server.py --selftest
py mcp-server/test_stdio.py     # real client over stdio JSON-RPC
```

| Tool | Answers |
|---|---|
| `get_ai_reception_overview` | What the product does, plus the safety rules |
| `get_safety_rules` | Never gives medical advice; urgent calls stop and go to 000 |
| `classify_call` | Routes one caller utterance: emergency / refused advice / reception |
| `assess_business_fit` | Honest fit, including saying when it is not a fit |
| `what_target_digital_will_not_claim` | Pricing, clinical advice, guarantees — with reasons |

## The one rule that matters most

**Emergency is tested first and independently of clinical advice.** A caller can say
something that is both urgent and a medication question:

> "I have chest pain, should I take an aspirin?"

Checking for advice first would answer about the aspirin and miss the heart attack.
`test_canon.py` pins that exact sentence, and `test_stdio.py` re-checks it over the wire.
If anyone reorders those checks, both tests fail.

The emergency word list is deliberately broad. A false positive costs one redirected
call; a false negative offers a Tuesday appointment to someone who needed an ambulance.

## Why the refusals are a tool

A voice agent that books appointments is not hard to build. A practice can only put one
on its main patient line because of what it refuses to do — improvised clinical answers
become a liability the practice inherits, not the vendor's. Selling that means being able
to state it precisely, which is what `get_safety_rules` is for.

## No pricing, deliberately

Rop, 2026-09-13: *"pricing later."* The site carries tiers; this server defers to a
scoping call, because setup and retainer depend on call volume, integrations and scope,
and a number an assistant quotes is a number the business gets held to.

`test_canon.py` asserts no price token appears in any output, and that pricing is an
explicit refusal rather than a silent omission.

## No unsubstantiated superlatives

Australian Consumer Law treats a "best" or "guaranteed" claim you cannot substantiate as
misleading conduct. A regex in the tests sweeps every output for guarantee language.

## Not yet done

- **Lead capture.** Deliberately absent, as with Imani: a tool that writes leads needs
  rate limiting and validation first.
- **Hosting.** stdio only. A directory listing needs a remote transport.
- **The other two engines.** This server covers AI reception. The Lead Gen Engine and
  Outbound Call Engine have their own logic and are not modelled here yet.
