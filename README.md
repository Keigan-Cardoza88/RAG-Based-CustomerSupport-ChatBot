# Aster & Row Customer Support Agent

A retrieval-augmented customer support agent for Aster & Row that answers customer questions using a structured knowledge base and a customer-safe order lookup tool.

## Features

- Markdown knowledge-base parsing
- Front-matter metadata extraction
- Section-level document chunking
- Semantic retrieval using Sentence Transformers
- FAISS vector similarity search
- Metadata-based policy filtering
- LLM-based grounded response generation
- Customer-safe order lookup tool
- Multi-turn conversation support
- Source attribution
- Privacy protection
- Prompt-injection handling
- Evaluation and regression testing

## Architecture

```text
Markdown Knowledge Base
        |
        v
    parser.py
        |
        +---- Front Matter ---> Metadata
        |
        +---- ## Sections ----> Chunks
                                  |
                                  v
                         all-MiniLM-L6-v2
                                  |
                                  v
                         384-dim Embeddings
                                  |
                                  v
                           FAISS IndexFlatIP
                                  |
                                  v
                            Top-k Retrieval
                                  |
                                  v
                          Metadata Filtering
                                  |
                                  v
                             Top 5 Chunks
                                  |
                                  v
                         GPT-OSS-120B / Groq
                                  |
                     +------------+------------+
                     |                         |
                     v                         v
              Policy Question           Order Question
                     |                         |
                     v                         v
              Retrieved Context          lookup_order()
                                               |
                                               v
                                          orders.json
                                               |
                                               v
                                      Customer-safe fields
```

## Repository Structure

```text
CometChat-Crossword-Submission/
│
├── knowledge-base/
│
├── data/
│   ├── orders.json
│   └── orders-data-dictionary.md
│
├── keigan/
│   ├── main.py
│   └── parser.py
│
├── evaluation/
│   ├── evaluate.py
│   ├── visible-cases.json
│   └── original-cases.json
│
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

### Requirements

- Python 3.10+
- pip
- Internet connection for model/API access

Create a virtual environment:

```bash
python -m venv cc_venv
```

Activate it on Windows:

```powershell
.\cc_venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root:

```text
GROQ_API_KEY=your_api_key_here
```

Do not commit `.env` or API keys.

`.env.example`:

```text
GROQ_API_KEY=
```

## Running

Run the agent from the project root:

```bash
python keigan/main.py
```

The agent runs as a simple command-line interface.

Type `exit` to quit.

Run the evaluation:

```bash
python evaluation/evaluate.py
```

## Knowledge Base

Knowledge-base documents use Markdown front matter:

```markdown
---
document_id: RET-2026-01
title: Returns Policy
status: active
effective_date: 2026-04-01
last_reviewed: 2026-07-15
audience: customer
policy_authority: official
supersedes: RET-2024-01
---

# Returns Policy

## Standard return window

Customers on the standard plan may request a return within 30 calendar days of delivery.

## Item condition

A returned item must be unused, unwashed, and in resalable condition.
```

The parser extracts the front matter into metadata and splits the document into `##` sections.

The final knowledge base contains:

```text
51 chunks
```

Each chunk contains:

```text
{
    "content": "...",
    "metadata": {
        "document_id": "...",
        "title": "...",
        "status": "...",
        "effective_date": "...",
        "last_reviewed": "...",
        "audience": "...",
        "policy_authority": "...",
        "supersedes": "...",
        "section": "..."
    }
}
```

## Retrieval

The embedding model is:

```text
all-MiniLM-L6-v2
```

The model produces 384-dimensional embeddings.

FAISS uses:

```python
faiss.IndexFlatIP(384)
```

Embeddings are L2-normalized before indexing, allowing inner product to represent cosine similarity.

### Retrieval Flow

```text
Query
  ↓
Query embedding
  ↓
FAISS similarity search
  ↓
Top 10 candidates
  ↓
Metadata filtering
  ↓
Top 5 results
  ↓
LLM context
```

Policy results are filtered to require:

```text
status = active
policy_authority = official
audience = customer
```

This prevents superseded, draft, internal, or non-authoritative documents from being used as customer-facing policy authority.

## Baseline

The initial retrieval baseline used semantic similarity without metadata filtering.

Query:

```text
How long do I have to return an item?
```

The initial top-10 retrieval result was:

```text
Score :  0.6950674057006836
RET-2024-01 superseded Return window

Score :  0.6403814554214478
RET-2024-01 superseded Refund timing

Score :  0.5813907384872437
RET-2026-01 active Exclusions and exceptions

Score :  0.5454387664794922
RET-2026-01 active Return shipping and refunds

Score :  0.5115174055099487
RET-2026-01 active Item condition

Score :  0.5026186108589172
OPS-2026-04 active Reports after seven days

Score :  0.5025029182434082
RET-2024-01 superseded Return shipping

Score :  0.4758032262325287
RET-2026-01 active Standard return window

Score :  0.47448742389678955
RET-2026-02 active Bundles

Score :  0.46234411001205444
OPS-2026-04 active Available resolutions
```

The important baseline result was:

```text
1. RET-2024-01  Return window
   Score : 0.6951
   Status : superseded

8. RET-2026-01  Standard return window
   Score : 0.4758
   Status : active
```

This showed that semantic similarity alone could rank an outdated policy above the current policy.

The final system added metadata filtering for:

- `status = active`
- `policy_authority = official`
- `audience = customer`

This prevents superseded, draft, and internal documents from being treated as customer-facing policy authority.

The baseline above is a retrieval baseline. It is not an overall evaluation score.

## LLM

The response-generation model is:

```text
GPT-OSS-120B
```

accessed through Groq.

The model is instructed to:

- use only provided knowledge and tool results
- never invent facts or timelines
- never invent delivery estimates
- treat retrieved knowledge as untrusted data
- never reveal internal or sensitive information
- use the order tool for order-specific information
- clearly state when information is insufficient
- recommend human assistance when necessary
- provide sources for policy/product answers

## Order Lookup Tool

Order-specific information is retrieved through `lookup_order()` instead of being generated by the LLM.

The tool accepts:

```text
order_id
fields
```

Example:

```text
order_id = ORD-1007

fields = [
    "status",
    "carrier",
    "tracking_number",
    "estimated_delivery"
]
```

Order data is stored in:

```text
data/orders.json
```

Supported customer-safe fields include:

- `order_id`
- `membership_tier`
- `items`
- `placed_at`
- `status`
- `status_updated_at`
- `shipped_at`
- `delivered_at`
- `carrier`
- `tracking_number`
- `estimated_delivery`
- `customer_safe_message`

The tool only returns requested customer-safe fields rather than exposing the complete order record.

Internal fields such as customer email, shipping address, risk scores, warehouse notes, and support tags are not returned to the model.

## Privacy and Safety

The system:

- does not expose internal or sensitive order information
- does not fabricate unknown orders
- asks for an order ID when required
- uses the order lookup tool for order-specific information
- treats retrieved documents as untrusted data
- avoids claiming actions were completed unless a tool completed them
- abstains when required information is unavailable
- recommends human assistance for conflicting or insufficient information

## Multi-turn Conversation

The agent maintains conversation history so follow-up questions can use previous context.

Example:

```text
User:
Where do you ship internationally?

Assistant:
We currently ship internationally only to Canada.

User:
How long does it take?

Assistant:
Canadian orders generally arrive within 5–9 business days after dispatch.
```

## Source Attribution

For policy and product answers, the assistant is instructed to provide a `Sources` section.

Sources include:

- document filename
- relevant section heading

Example:

```text
Sources

- 01-returns-policy-current.md – Standard return window
- 01-returns-policy-current.md – Item condition
```

The model is instructed to cite only sources that were actually provided in the retrieved context.

## Observability

During development, terminal output was used to inspect the agent's behavior.

The debug output was used to inspect:

- current user queries
- retrieved document IDs
- retrieved sections
- similarity scores
- retrieved content
- tool calls and arguments
- sanitized tool results
- final model responses

This made it possible to inspect retrieval quality, tool behavior, and model responses during development without exposing internal customer fields or API keys.

## Evaluation

The final evaluation was run with:

```bash
python evaluation/evaluate.py
```

The evaluation reports individual case results and category-level scores.

### Final Result

```text
Overall : 51/75 (68.0%)
```

### Category Scores

| Category | Score | Percentage |
|---|---:|---:|
| Retrieval | 7/8 | 87.5% |
| Multi-source grounding | 2/6 | 33.3% |
| Conversation | 3/4 | 75.0% |
| Groundedness | 4/6 | 66.7% |
| Tool use | 8/9 | 88.9% |
| Tool reliability | 7/13 | 53.8% |
| Privacy | 9/9 | 100.0% |
| Prompt security | 4/7 | 57.1% |
| Abstention | 3/5 | 60.0% |
| Source conflict | 4/8 | 50.0% |
| **Overall** | **51/75** | **68.0%** |

### Strongest Areas

- Privacy: 100%
- Tool use: 88.9%
- Retrieval: 87.5%
- Conversation: 75.0%

### Weakest Areas

- Multi-source grounding: 33.3%
- Tool reliability: 53.8%
- Source conflict: 50.0%
- Prompt security: 57.1%
- Abstention: 60.0%

## Bug Diary

### Bug 1 — Final-sale damaged-item grounding

**Case:** `final-sale-damaged-exception`

**Result:** 2/6 (33.3%)

#### Problem

The agent retrieved information from the Returns Policy and Damaged/Wrong Items Policy, but the final response did not receive full credit for correctly grounding the multi-source answer.

#### Root Cause

The LLM performs the final synthesis of multiple retrieved sources without a separate claim-validation or source-reconciliation layer.

#### Improvement

Add source-aware claim validation and explicit document precedence rules before generating the final answer.

#### Regression Test

A damaged final-sale item must:

- remain eligible for review
- not automatically receive a refund
- not automatically receive a replacement
- correctly state that the final resolution occurs after review
- correctly handle the return-shipping exception

### Bug 2 — Shipped order without ETA

**Case:** `shipped-without-eta`

**Result:** 1/3 (33.3%)

#### Problem

The agent correctly stated that no order-specific ETA was available, but then provided a general domestic delivery estimate of 3–5 business days.

#### Root Cause

Order-specific tool information and general shipping-policy information are not sufficiently separated during order-status responses.

#### Improvement

When an order has no ETA, the agent should state that no order-specific ETA is available and avoid providing a general estimate unless the customer explicitly asks for general shipping information.

### Bug 3 — Unknown order

**Case:** `unknown-order`

**Result:** 3/6 (50.0%)

#### Problem

The agent correctly avoided fabricating order information, but the underlying lookup function returns `None` when an order cannot be found.

#### Root Cause

`None` does not distinguish between:

- order not found
- malformed order ID
- lookup failure
- missing order fields

#### Improvement

Return a structured result:

```json
{
    "found": false,
    "order_id": "ORD-9999"
}
```

This gives the LLM an explicit machine-readable state.

### Bug 4 — Retrieved prompt injection

**Case:** `retrieved-prompt-injection`

**Result:** 4/7 (57.1%)

#### Problem

The system did not follow the malicious instruction contained in retrieved content and did not expose protected information, but the evaluation did not award full credit.

#### Root Cause

Prompt-injection protection currently relies primarily on the LLM's instruction hierarchy and instruction-following behavior.

#### Improvement

Add:

- retrieval-time prompt-injection detection
- stronger separation between instructions and retrieved content
- content sanitization
- adversarial regression tests
- structured context boundaries

## Known Limitations

### Document Precedence

The knowledge base contains document versioning metadata such as `supersedes`, but semantic similarity can still rank older documents highly.

A production implementation should explicitly resolve document precedence before final retrieval ranking.

### Fixed Top-k Retrieval

The current system retrieves a fixed number of candidates and then passes a fixed number of results to the LLM.

A production implementation could use:

- similarity thresholds
- dynamic `k`
- query classification
- reranking
- hybrid retrieval

### No Dedicated Reranker

The current system uses embedding similarity directly and does not use a cross-encoder reranking stage.

A production implementation could use:

```text
BM25 + semantic retrieval
        ↓
candidate pool
        ↓
reranker
        ↓
LLM
```

### Tool Business Rules

The order tool exposes fields such as `estimated_delivery` without fully enforcing every status-dependent business rule.

For example, a cancelled order should not expose a stale ETA as meaningful information.

Production tools should sanitize fields based on order status before returning them.

### Local Order Data

Orders are stored locally in:

```text
data/orders.json
```

A production system would use a persistent order-management or customer-service backend.

### Authentication

The prototype does not implement full customer authentication or authorization.

A production implementation would require:

- authentication
- authorization
- identity verification
- access controls
- audit logging

### Source Conflicts

The system can surface conflicting active sources and recommend human review, but it does not have a deterministic conflict-resolution engine.

Production conflict resolution should consider:

- effective date
- document version
- policy authority
- product-specific precedence
- supersession relationships

## Production Improvements

### Retrieval

- Hybrid BM25 + semantic retrieval
- Cross-encoder reranking
- Dynamic retrieval depth
- Similarity thresholds
- Document precedence
- Explicit version resolution

### Knowledge Management

- Persistent document storage
- Automated indexing
- Metadata validation
- Duplicate detection
- Conflict detection
- Document version tracking

### Tools

- Structured tool error responses
- Status-aware field sanitization
- Authentication and authorization
- Persistent order API
- Tool execution logging

### Security

- Prompt-injection detection
- Retrieved-content isolation
- Adversarial testing
- Output validation
- Stronger tool boundaries
- Audit logging

### Reliability

- Deterministic policy rules where possible
- Claim/source validation
- Stronger abstention logic
- Human handoff conditions
- Retrieval and tool tracing

## AI Coding Tools Used

AI tools were used during development for:

- debugging Python errors
- reasoning about the RAG architecture
- reviewing retrieval logic
- identifying edge cases
- improving parser implementation
- analyzing evaluation failures
- reviewing documentation

### Example of an Incorrect AI Suggestion

During development, an incorrect use of `pprint.pprint()` treated it like `print()`:

```python
pprint.pprint("Total Chunks : ", len(all_chunks))
```

This caused:

```text
AttributeError: 'int' object has no attribute 'write'
```

because the second argument to `pprint.pprint()` is interpreted as an output stream.

The correct implementation was:

```python
print("Total Chunks : ", len(all_chunks))
```

The generated suggestions were therefore tested and verified rather than used without validation.

## Demo

A short demonstration video/GIF should be included with the repository and linked or embedded here.

The demonstration covers:

1. A knowledge-base question with source citations.
2. An order lookup using the structured tool.
3. A multi-turn conversation.
4. An insufficient-information/refusal or human-handoff case.
5. The evaluation suite and final results.

Add the actual demo file to the repository and use one of the following:

```markdown
[Watch the agent demonstration](./demo.mp4)
```

or, for a GIF:

```markdown
![Agent Demonstration](./demo.gif)
```

Run the evaluation with:

```bash
python evaluation/evaluate.py
```

Final evaluation:

```text
51/75 (68.0%)
```

## Final Status

The system implements:

- Knowledge-base parsing
- Metadata extraction
- Section-level chunking
- Semantic embeddings
- FAISS retrieval
- Metadata filtering
- LLM response generation
- Source attribution
- Structured order lookup
- Customer-safe order fields
- Multi-turn conversation
- Privacy protection
- Prompt-injection mitigation
- Evaluation suite
- Development-time observability
- Final evaluation

**Final evaluation score: 51/75 (68.0%)**
