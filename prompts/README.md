# Optional AI integration

The baseline intentionally makes zero model calls. Keep CSV parsing, sorting, policy enforcement,
and validation deterministic. If an LLM is added, restrict it to extracting candidate facts from
ambiguous unstructured evidence; require source/evidence citations, validate all structured output,
never let model output override policy, and record actual provider/model/token/cost data.
Do not place API keys in prompts or commit secrets.
