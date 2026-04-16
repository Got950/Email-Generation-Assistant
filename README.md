# Email Generation Assistant

I built this as a take on the classic "generate professional emails" problem, but with a focus on actually *measuring* whether the output is any good — not just eyeballing it.

The system takes three inputs (intent, key facts, tone) and produces a polished email. Under the hood, it uses a multi-layered prompting approach with a self-reflection loop, and ships with a custom evaluation framework I designed to benchmark quality across two different strategies.

Built with FastAPI, LangChain, OpenAI, and a React + Tailwind CSS frontend.

## How it works

```
User Input (intent, facts, tone)
         │
         ▼
   ┌─────────────┐
   │  LangChain   │──► Advanced: Role-Play + Few-Shot + CoT + Critic
   │  Chains      │──► Baseline: Simple zero-shot
   └─────────────┘
         │
         ▼
   Generated Email
         │
         ▼
   ┌─────────────┐
   │  Evaluation  │──► Fact Recall (LLM Judge + Semantic Similarity)
   │  Pipeline    │──► Tone Alignment (LLM Judge + VADER)
   │              │──► Professional Quality (Readability + Structure + Grammar)
   └─────────────┘
         │
         ▼
   JSON/CSV Reports + Auto-populated REPORT.md
```

## Getting started

You'll need Python 3.11+, Node.js 18+, and an OpenAI API key.

```bash
git clone https://github.com/Got950/Email-Generation-Assistant.git
cd Email-Generation-Assistant

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Add your API key to .env
```

Fire up the API:

```bash
uvicorn app.main:app --reload --port 8000
```

Swagger docs live at http://localhost:8000/docs. Quick test:

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "Follow up after a demo call",
    "key_facts": ["Demo was last Tuesday", "Client liked reporting", "Next step is pilot"],
    "tone": "formal",
    "strategy": "advanced"
  }'
```

Launch the React frontend (in a separate terminal):

```bash
cd frontend
npm install
npm run dev
```

The UI opens at http://localhost:5173 with three pages — Generate (email composer), Evaluation (live streaming dashboard), and Scenarios (test data browser).

Or just `docker-compose up --build` if you want both services running.

## The prompting strategy

The **advanced** strategy stacks three techniques — I found that layering them works noticeably better than any single one:

1. **Role-Playing** — The model acts as a B2B sales communications specialist. This grounds the output in domain expertise and keeps the language professional without being told "be professional" over and over.

2. **Few-Shot Examples** — Three hand-written emails (formal, casual, empathetic) give the model a structural template to anchor on. Without these, the output format varies wildly between runs.

3. **Chain-of-Thought** — Before writing, the model silently plans: what's the CTA, which paragraph gets which fact, what vocabulary fits the tone. This step alone cut fact-omission rate significantly in my testing.

4. **Self-Reflection** — A critic pass reviews the draft for missing facts, tone drift, and structural issues. If anything fails, it rewrites. This is the safety net.

The **baseline** is a simple zero-shot prompt ("write an email with these inputs") for comparison.

## Evaluation

I wasn't happy with generic metrics like BLEU or ROUGE for this — they don't capture what actually matters in a business email. So I built three custom ones:

**Fact Recall (0–100)** — Did the email actually include all the key facts? An LLM judge checks each fact individually. If the judge is uncertain, a sentence-transformer similarity check (cosine ≥ 0.75) acts as a second opinion.

**Tone Alignment (0–100)** — Does it *feel* right? An LLM judge rates tone match on a 1–10 rubric (80% weight), and VADER sentiment analysis provides a sanity check (20% weight). The sentiment profiles are tuned per tone — "urgent" has a different expected compound score than "warm-grateful".

**Professional Quality (0–100)** — Four sub-scores, each 0–25:
- Readability via Flesch Reading Ease (targeting the 50–70 sweet spot for business)
- Conciseness by comparing word count against the reference email
- Structure checks (subject line, greeting, body paragraphs, sign-off)
- Grammar/fluency rated by an LLM judge

Run the full pipeline:

```bash
python run_evaluation.py
```

This evaluates all 10 scenarios × 2 strategies × 3 metrics and generates `reports/evaluation_results.json`, a CSV, and auto-fills `REPORT.md` with real data.

You can also run it from the React UI's Evaluation tab — it streams results live via SSE as each scenario completes.

## Project layout

```
app/
├── main.py                    # FastAPI app + health check
├── config.py                  # Pydantic settings, OpenAI configuration
├── api/
│   ├── schemas.py             # Request/response models
│   └── routes/
│       ├── generate.py        # POST /generate
│       └── evaluate.py        # POST /evaluate, /evaluate/stream (SSE), GET /scenarios
├── core/
│   ├── prompts.py             # All prompt templates (advanced, baseline, critic)
│   ├── chains.py              # LangChain generation + critic logic
│   └── models.py              # Model factory + retry with backoff
└── evaluation/
    ├── metrics/
    │   ├── fact_recall.py
    │   ├── tone_alignment.py
    │   └── professional_quality.py
    ├── runner.py              # Orchestrates the full eval pipeline
    └── report.py              # JSON/CSV/Markdown report generation

data/scenarios.json            # 10 test scenarios with reference emails
frontend/                      # React + Tailwind CSS UI (Vite + TypeScript)
ui/streamlit_app.py            # Legacy Streamlit dashboard
tests/test_generate.py         # 42 unit tests (mocked, no API key needed)
REPORT.md                      # Comparative analysis (auto-populated)
```

## Tests

```bash
pytest tests/ -v -k "not integration"
```

42 tests covering API validation, prompt templates, all three metrics' edge cases (empty inputs, parse failures), critic behavior (approved/revised/garbage/exception), scenario data integrity, and config auto-detection. All mocked — no API key required.

```bash
ruff check app/ tests/
```

## Docker

```bash
docker-compose up --build
```

API on `:8000`, UI on `:8501`. Both share the same `.env` for API keys.

## What I'd do next

A few things I'd add given more time:

- **LangGraph agent graph** — replace the simple critic loop with a proper Planner → Writer → Critic workflow
- **RAG layer** — pull company context from a vector store so emails reference real products/people
- **Token-level streaming** — SSE for real-time token streaming in the email generation UI
- **A/B routing** — serve both strategies in production and collect metrics automatically to validate offline eval findings

## License

MIT
