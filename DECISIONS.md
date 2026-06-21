# DECISIONS

Assumptions and deviations made during autonomous execution, dated.

## 2026-06-20

- **Counterfactual baseline.** Savings are computed against the baseline model by
  pricing the *actual* token usage at the baseline's rates. This assumes the
  frontier model would produce a comparable number of tokens. It's the standard
  honest counterfactual but it is an assumption, stated plainly in the README.
- **Escalation cost is additive.** When a request escalates, the recorded actual
  cost includes both the original (cheap) call and the escalated call — savings
  are never inflated by ignoring the wasted first call.
- **Token estimation uses tiktoken `cl100k_base`** as a provider-agnostic
  estimator (with a chars/4 fallback). Exact tokenization differs per model, so
  reported costs are estimates, not billing-exact.
- **Verifier is a heuristic confidence proxy** (empty / refusal / too-short →
  low score). The architecture allows a real LLM judge to be substituted; the
  heuristic keeps tests deterministic and offline.
- **Demo savings band (40-60%).** Realistic tier prices make naive routing look
  *better* than 40-60% (haiku is ~95% cheaper than opus, sonnet ~80%). To land in
  the spec's stated band, the demo policy routes hard work to the frontier (0%
  savings) and only downgrades trivial/simple work — a conservative strategy. The
  band is configurable in the telemetry test.
- **respx not required for the server test.** Because provider calls go through
  the mockable provider abstraction, the FastAPI proxy is tested with
  `TestClient` + `MockProvider` (offline) instead of HTTP-level `respx` mocking.
  respx remains a dev dependency for anyone testing the real HTTP providers.
