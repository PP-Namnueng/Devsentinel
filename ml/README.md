# DevSentinel ML Plan

Fine-tuning is intentionally deferred until the deterministic demo path is stable.

Allowed strategy:

- LoRA or QLoRA only.
- Train for review reasoning, security detection, architecture violation detection, and structured output consistency.
- Use 50-100 curated examples rather than a noisy scraping pipeline.

Comparison target:

- Base model vs fine-tuned model.
- Metrics: critical issue detection, reasoning quality, structured output consistency, and architecture violation detection.

The model layer remains model-agnostic through `backend/app/model_gateway`.
