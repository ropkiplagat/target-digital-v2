# clients/ — per-client deliverables + evidence

This directory is the **namespaced boundary** the `check.py` gatekeeper enforces.
Client work lives here, one folder per client, so two gates can do their job:

- **G2 — Client isolation.** Nothing inside `clients/acme/` may name another client
  (their slug, domain, or aliases). Prevents one client's copy leaking into another's.
- **G4 — Evidence-backed claims.** Every number, percentage, dollar figure, or
  testimonial in a client deliverable must trace to an approved entry in that client's
  `evidence.yml`. Un-sourced claims **hard-stop the build.**

## Layout

```
clients/
  registry.yml            # register every client here (slug, domain, aliases)
  acme-roofing/
    evidence.yml          # the ONLY place approved claims may come from
    blog/ email/ ...      # deliverables for this client
```

## evidence.yml — the honesty file

The whole point of G4 is that **a claim you can't source can't ship.** So every entry
**must** carry a non-blank `source`. An entry with a blank or missing `source` is
treated as a fabrication and **fails the gate** — same as a number with no entry at all.

```yaml
# clients/acme-roofing/evidence.yml
claims:
  - value: "42%"                                  # the literal figure as it appears in copy
    text: "42% more booked calls in 90 days"      # human-readable claim (optional context)
    source: "Client GA4 export, Jan-Mar 2026; screenshot at proof/acme-ga4.png"   # REQUIRED, non-blank

  - value: "quote"                                # use "quote" for a testimonial
    text: "Best decision we made this year. — Jane, Ops Lead"
    source: "Signed testimonial email 2026-05-02, on file"
```

Rules:
- `value` is what the gate matches against copy (e.g. `42%`, `$12,000`, `3x`, or `quote`).
- `source` is **mandatory and must describe real, checkable evidence** — a dashboard,
  a signed email, an invoice. "TBD", "n/a", or blank = fail.
- Keep it truthful. The gate enforces that a source *exists*; only you can keep it *honest*.
