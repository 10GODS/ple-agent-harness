# A Budget-Aware Engineering Agent Harness for PLE-Bench

**Declared model:** google-cloud/gpt-oss-120b · **Repository:** https://github.com/10GODS/ple-agent-harness

PLE-Bench tasks are not chat problems. Each one hands an agent a working directory of drawings, models, spreadsheets and mail, and grades the files it leaves behind. Our harness is a small OpenAI-compatible agent server; this writeup reports what actually failed when we ran it, measured on the public dev set.

## 1. Insight & failure analysis (25 pts)

We ran the harness on `data-hall-mep-routing` — rebuild a data-hall model from a seven-sheet drawing set and route three overhead services clash-free. Three failures dominated, and each changed the harness.

**Premature completion.** The first run ended in **3 steps / 16 s**. The model wrote a 2 KB `solution.py`, claimed it generated an IFC4 model, and stopped — without listing a single input file. Score: **0/12 checks**. The harness had a gate that checked the deliverable *existed*, and it did. Existence is not verification. We added a progress gate: a run may not finish until it has (a) opened at least one input (`ls/find/cat/read_file`) and (b) run a shell command after its last write (`dirty` flag cleared). The same model then took **7 steps / 95 s**, inspected the work directory, executed its script, and emitted a real IFC file. Still 0/12 — the geometry was wrong — but the failure became visible and diagnosable instead of a hallucinated success.

**Context growth versus free-tier token budgets.** Our longest run (46 steps) averaged **37,582 prompt tokens per call** (1.73 M total, 1.57 M cached). Free inference tiers meter input tokens per minute: 8,000 for `gpt-oss-120b` on Groq, 16,000 for Gemma 4 26B on AI Studio. A 37 k-token call can never fit, so every call after the first few returned 429 and the sweep died with "harness exited before model produced any output." Fix: make the caps tunable and tight — `TOOL_RESULT_CHARS` 30,000 → 10,000, `KEEP_RECENT_RESULTS` 12 → 3, `COMPACT_AT_TOKENS` 60,000 → 6,000. The proof run now averages **2,479 prompt tokens per call** (17,354 / 7) with zero 429s.

**Model routes that look free but are not.** `gemini-4-argon` and `gemini-3.1-pro-preview` report a free-tier limit of **0** — not an exhausted quota that resets, but a model unavailable without billing. `gemini-3.8-flash` returned **503** on every probe for 24 hours. Vertex AI returns 403 "requires billing" on our project. Gemma 4 26B works, but a 26B-A4B model with a 16 k/min input cap still cannot hold a 37 k-token call. The one workable free route was the same open-weights `gpt-oss-120b` served by Groq behind a local LiteLLM proxy.

**Compatibility bugs found by running.** Groq rejects provider-extra assistant fields (`channel`, `reasoning_content`) when conversation history is echoed back; `STRICT_ASSISTANT_FIELDS=1` keeps the standard shape. Gemini rejects `reasoning_effort` entirely, and an empty value caused LiteLLM 500s, so the key is omitted when unset. The retry schedule was extended to 10 minutes to ride out minute-scale quota windows.

| Ablation | Before | After |
|---|---|---|
| progress gate | 3 steps, no input opened, 16 s | 7 steps, input read, script executed, 95 s |
| `COMPACT_AT_TOKENS` 60k → 6k | 37.6k prompt tokens/call → 429 | 2.5k prompt tokens/call → 200 |
| `TOOL_RESULT_CHARS` 30k → 10k | one read = ~7.5k tokens | one read ≤ 2.5k tokens |
| strict assistant fields | 400 on history echo | clean 200s |

## 2. Engineering reasoning (25 pts)

The data-hall trace shows the gap between the harness and a licensed engineer. A mechanical engineer starts by loading the seven sheets, extracting the room envelope (~27 × 21 m) and the 128-cabinet layout, then routing telecom tray, power busway and chilled-water pipe by shortest clash-free path, checking code clearances, and only then producing the IFC model and schedule. The harness does follow the same *sequence*: it inventories the work directory, reads the task spec as a requirements document, writes a generator script rather than hand-authoring geometry, runs it, and re-opens the deliverable. What it cannot do at this budget is *see*: with a 2.5k-token working window and no vision, it never extracted the drawing dimensions, so its IFC contains placeholder racks and simplified assemblies. The checker correctly awarded zero.

That is the honest finding: the binding constraint here is model capability under a free-token budget, not the plumbing. The harness's job is to make that constraint visible. The progress gate now refuses a "done" that opened no input; the compaction layer records when context was cut; the deadline logic reserves three minutes for a final summary so a run never ends with an empty deliverable. On a task the model *can* do — text-heavy memos, spreadsheet checks, deterministic calculations — the same loop reads the inputs, computes in Python, writes the file, executes a self-check, and only then answers.

## 3. Cross-model generalizability (15 pts)

| Model (route) | Task | Steps | Prompt tokens | Wall time | Score |
|---|---|---|---|---|---|
| `gpt-oss-120b` (Groq free) | data-hall-mep-routing | 7 | 17,354 | 95 s | 0.000 (0/12) |
| `gemini-3.5-flash-lite` (AI Studio free) | wind-diaphragm-shear | 46 | 1,728,773 | 628 s | 0.0476 (1/21) |
| `gemma-4-26b` (AI Studio free) | data-hall-mep-routing | — | — | aborted | 429 at 16k TPM |
| `gemini-4-argon`, `gemini-3.1-pro` | — | — | — | — | free-tier limit = 0 |
| `gemini-3.8-flash` | — | — | — | — | 503 for 24 h |

The long-context Gemini run earned partial credit (1 of 21 checks) but spent 100× the tokens of the gpt-oss run. The gpt-oss run had a cleaner process (it executed what it wrote) but a weaker model. Gemma could not complete a single call at our context size. The harness itself is provider-agnostic: it reads `MODEL_BASE_URL` / `MODEL_API_KEY` and speaks OpenAI Chat Completions, so the same commit runs unchanged against the graders' proxy for the declared `google-cloud/gpt-oss-120b`.

*Transparency: local development and the committed `artifacts/` were produced on free inference tiers — the same open-weights model served through our local LiteLLM proxy. No billing was enabled and no keys are committed.*

## 4. Efficiency & scaling (20 pts)

The budget arithmetic drives every setting. At 8,000 input tokens/minute, a call can use at most ~7,000 prompt tokens plus ~1,000 output tokens, which allows roughly one call per minute and ~60 calls/hour. We therefore compact at 6,000 tokens, cap output at 2,048, and ask for low reasoning effort. The measured proof run used **8 model calls, 17,354 prompt + 1,293 completion tokens, 95 s, $0 cash** — about **$0.0036** at gpt-oss list price ($0.15/M input, $0.75/M output). The 46-step Gemini run used 1.73 M prompt + 22.9 k completion tokens in 628 s, about **$0.17** at flash-lite list price.

Levers that mattered: compaction before every call (not only on context errors), hard tool-result caps, a 10-minute retry ladder for 429/503, single-trial iteration, and per-task runs that download only that task's folder instead of the 33,345-file dataset. Caching helped the long run (1.57 M of 1.73 M prompt tokens were cached) but does not raise a per-minute quota.

Scaling is linear in steps, not parallel: one free key is one quota. A 100-step task is ~1.7 hours at 60 calls/hour; all 29 dev tasks would take about two days on a single key. Under a billed endpoint the same harness runs with a 60 k compaction threshold and a 4 k output ceiling, so the budget knobs are configuration, not architecture.

## 5. Clarity & visuals (15 pts)

1. **Architecture** (`assets/architecture.png`) — the harness serves the task over WebSocket, executes tools inside the Docker task container, and reaches the model only through the local LiteLLM proxy; the task container has no internet egress.
2. **Score vs. cost** (`assets/score_vs_cost.png`) — the two measured runs plotted as score against prompt tokens, with free-tier per-minute ceilings marked; the Gemini point buys 0.048 for 1.7 M tokens, the gpt-oss point costs 17 k tokens for a cleaner but unscored attempt.
3. **Failure breakdown** (`assets/failure_breakdown.png`) — the observed failure modes: premature completion, context-window/quota death, model unavailable (limit 0), and capability shortfall on drawing interpretation.

The repository contains the harness (`serve.py`, `submission.yaml`), the exported `artifacts/` with `manifest.json`, and the three figures. The kit's `artifacts` review accepts the entry (1 of 29 dev tasks usable; the rest score 0 and are reported as missing), and `kit check` validates submission, build, smoke, model and listen stages.

---
*Reproduce: `uv run python eval/run.py ../my-harness --tasks data-hall-mep-routing --trials 1 --env-file judge.env` with `MODEL_PROXY_URL` pointing at the local proxy. Keys are supplied at runtime; nothing is committed.*
