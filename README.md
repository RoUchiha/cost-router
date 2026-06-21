# costrouter — LLM Cost Router

**💸 [Live demo on Hugging Face Spaces](https://huggingface.co/spaces/rosingh/ai-ml-portfolio-demos)** — route a prompt and see the savings vs frontier-only.

## 🧠 In plain English

**The problem:** there are cheap, fast AI models and expensive, smart ones (often 20× the price). Most apps lazily send *everything* to the expensive one — even trivial questions. That's taking a taxi to your mailbox.

**The fix (analogy):** a help-desk dispatcher. Easy questions go to a junior agent (cheap); hard ones to a senior (expensive). If the junior gives a weak answer, the dispatcher escalates it.

**How it works:** a quick classifier rates each request's difficulty → it routes to the **cheapest model that can handle it** → optionally checks the answer and **escalates once** if it's weak → reports what was spent vs what always-expensive would have cost.

**Why it's honest:** when it escalates, it counts the cost of *both* calls (the failed cheap one and the retry), so the savings number is never flattering. Typically cuts **40–60%** of spend with no quality loss on the easy stuff. Ships as a drop-in proxy — change one URL.

Routes each request to the **cheapest model that can satisfy it**, cutting LLM
spend 40–60% vs always calling a frontier model. Complexity classification →
tiered routing → optional verify-and-escalate → honest savings telemetry. Ships
an **OpenAI-compatible FastAPI proxy** so it's a drop-in.

## How it works

1. **Classify** the request complexity (`trivial` / `simple` / `hard`) — a cheap,
   explainable heuristic by default; an optional LLM classifier is available.
2. **Route** to the cheapest tier the policy maps that level to.
3. **Call** the chosen model through the provider abstraction.
4. **Verify** (optional): a confidence proxy scores the answer; if it's below the
   bar, **escalate one tier and retry** (at most `max_escalations`).
5. **Record** tokens, actual cost, and the **counterfactual baseline cost**
   (what a frontier-only call would have cost) → savings %.

## Honest savings methodology

Savings are measured against a baseline model (default `claude-opus-4-8`). The
baseline cost prices the *actual* token usage at the baseline's rates — i.e. it
assumes the frontier model would emit a similar number of tokens. When an
escalation happens, the actual cost includes **both** calls (the failed cheap one
and the escalated one), so the number is never flattering by omission. See
[DECISIONS.md](DECISIONS.md).

## Quickstart

```bash
python -m venv .venv && .venv/Scripts/activate    # Windows
pip install -e ".[dev]"

# One-off routing decision + cost (offline mock provider)
costrouter route --prompt "what is the capital of France?"
costrouter route --prompt "Design a scalable ride-sharing backend and explain the trade-offs."

# Batch a workload and print a savings report
costrouter bench --file workload.jsonl

# Run the OpenAI-compatible proxy (real provider; needs ANTHROPIC_API_KEY)
costrouter serve --port 8000 --provider anthropic
```

`workload.jsonl` is one JSON object per line: `{"prompt": "..."}`.

### Using the proxy

```bash
curl localhost:8000/v1/chat/completions \
  -H 'content-type: application/json' \
  -d '{"messages":[{"role":"user","content":"hi"}]}' -i
# Response carries: X-Router-Tier, X-Router-Level, X-Router-Savings, X-Router-Escalated
```

## Config (YAML)

```yaml
tiers:
  - {name: cheap,    model: claude-haiku-4-5-20251001, price_input: 0.80, price_output: 4.00,  capability: simple}
  - {name: mid,      model: claude-sonnet-4-6,         price_input: 3.00, price_output: 15.00, capability: hard}
  - {name: frontier, model: claude-opus-4-8,           price_input: 15.0, price_output: 75.0,  capability: hard}
policy:
  trivial: cheap
  simple: cheap
  hard: mid
  escalate_to: frontier
  max_escalations: 1
  verify: true
baseline_model: claude-opus-4-8
```

## Tests

```bash
pytest                 # all gates, offline
pytest --cov=costrouter
```

The classifier accuracy gate, the routing/escalation gates, and a ~100-request
telemetry gate (savings within the 40–60% band) all run without an API key.

## Live demo

`app.py` is a Gradio demo: type a prompt, see the classified level, chosen tier,
and savings vs frontier — plus a batch view over a sample workload. Deployable to
Hugging Face Spaces (`requirements.txt` included).

## Layout

```
src/costrouter/
  config.py        # tiers, policy, pricing (YAML -> Pydantic)
  models.py        # ModelTier, Usage, RoutingDecision, CostRecord
  classifier/      # heuristic (default) + optional LLM classifier
  pricing.py       # token estimation + $ cost
  router.py        # classify -> route -> verify -> escalate -> record
  providers/       # base, anthropic, openai (import-safe), mock
  telemetry.py     # savings aggregation
  server.py        # OpenAI-compatible FastAPI proxy
  cli.py           # route / bench / serve
```
