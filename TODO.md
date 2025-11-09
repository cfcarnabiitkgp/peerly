# Peerly - TODO & Future Improvements

## Current Status: ✅ MVP Complete

The core peer review system is functional with:
- ✅ Structured LLM output (LangChain `with_structured_output()`)
- ✅ Separate fields: issue, explanation, suggested_fix
- ✅ Clarity & Rigor agents with RAG support
- ✅ Semantic caching for RAG queries
- ✅ Multi-agent workflow orchestration
- ✅ Frontend display of structured suggestions

---

## High Priority Improvements 🔥

### 1. RAG Query Expansion
**Status:** Not Implemented
**Priority:** HIGH
**Impact:** +15-40% better retrieval quality

**Problem:**
Current RAG query formulation is simple keyword-based and has limitations:
- Only samples first 200 chars from first 2 sections (position bias)
- Simple substring matching for keywords (brittle, false positives/negatives)
- Vocabulary mismatch (query says "theorem", guidelines say "lemma")
- Generic queries for diverse content

**Current Code:**
```python
# app/agents/rag_nodes.py, line 74-102
def _formulate_query(self, sections: List[Section]) -> str:
    query_parts = ["writing clarity guidelines mathematical papers"]
    content_sample = " ".join(s.content[:200] for s in sections[:2])
    # Simple keyword detection...
```

**Recommended Solution: Pseudo-Relevance Feedback (PRF)**

**Why PRF:**
- Free (no additional API costs)
- Fast (~100ms additional latency)
- Domain-aware (learns from your actual guidelines)
- Easy to implement

**Implementation Steps:**

1. **Quick Win (30 min):** Improve current sampling
   ```python
   # Increase sampling
   content_sample = " ".join(s.content[:300] for s in sections[:5])

   # Better keyword detection with word boundaries
   if re.search(r'\b(theorem|lemma|corollary)\b', content_sample, re.I):
       query_parts.append("clear mathematical statements")
   ```

2. **Medium Win (1-2 hours):** Add PRF expansion
   ```python
   def expand_with_prf(self, initial_query: str, top_k: int = 5) -> str:
       # Step 1: Initial retrieval
       initial_results = self.rag_service.retrieve(initial_query, top_k=top_k)

       # Step 2: Extract key terms from top results
       all_text = " ".join([doc.page_content for doc in initial_results])
       expansion_terms = self._extract_key_terms(all_text, top_n=3)

       # Step 3: Combine
       expanded_query = f"{initial_query} {' '.join(expansion_terms)}"
       return expanded_query
   ```

3. **Advanced (3-4 hours):** LLM-based query expansion
   ```python
   async def expand_with_llm(self, base_query: str) -> str:
       llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3)
       prompt = f"""Expand this RAG query with 3-5 related keywords:
       Query: {base_query}
       Output: comma-separated keywords only"""

       response = await llm.ainvoke([{"role": "user", "content": prompt}])
       return f"{base_query} {response.content.strip()}"
   ```

**Files to Modify:**
- `app/agents/rag_nodes.py` - Update `_formulate_query()` and `__call__()`
- Add `app/agents/query_expansion.py` - New module for expansion logic

**Testing:**
- Create test notebook: `tests/test_rag_query_expansion.ipynb`
- Compare retrieval quality before/after expansion
- Measure: recall@k, precision@k, latency

**References:**
- See conversation: "Query Expansion with Embeddings" (2025-11-08)
- Comparison table of approaches (PRF, Embedding, LLM, Hybrid)

---

### 2. Enhanced Pydantic Model Documentation
**Status:** Good, Can Be Better
**Priority:** MEDIUM
**Impact:** +10-15% better structured output quality

**Why It Matters:**
Field descriptions in Pydantic models are sent to the LLM via JSON Schema. Better descriptions → Better output quality.

**Current State:**
```python
class StructuredSuggestion(BaseModel):
    issue: str = Field(
        description="Concise statement of what's wrong (1 sentence)"
    )
```

**Recommended Enhancement:**
```python
class StructuredSuggestion(BaseModel):
    issue: str = Field(
        description="A single, concise sentence identifying the specific problem. "
                   "Focus on WHAT is wrong without explaining why or how to fix. "
                   "Example: 'The term convergence rate is used without definition'"
    )
    explanation: str = Field(
        description="1-2 sentences explaining WHY this issue is problematic. "
                   "Describe the impact on clarity, rigor, or scientific validity. "
                   "Example: 'Readers unfamiliar with optimization theory may not...'"
    )
    suggested_fix: str = Field(
        description="Specific, actionable recommendation for HOW to fix (1-2 sentences). "
                   "Include concrete examples or rewrites when applicable. "
                   "Example: 'Define convergence rate: convergence rate (the speed...)'"
    )
```

**Files to Modify:**
- `app/models/schemas.py` - Enhance all Field descriptions with examples

**References:**
- See conversation: "Documenting Pydantic Models for Function Calling" (2025-11-08)

---

## Medium Priority Improvements 🔧

### 3. Multi-Section RAG Strategy
**Status:** Not Implemented
**Priority:** MEDIUM
**Impact:** More targeted guidelines per section type

**Current Behavior:**
- RAG called once per agent for all sections
- Same guidelines used for Introduction, Methodology, Results

**Proposed Enhancement:**
- Detect section types and retrieve specialized guidelines
- Example: Statistical Analysis section → retrieve statistical rigor guidelines

**Implementation:**
```python
def __call__(self, state: dict) -> dict:
    sections = state.get("sections_for_clarity", [])

    # Group sections by type
    section_groups = self._group_by_type(sections)

    # Retrieve guidelines per group
    all_guidelines = []
    for section_type, secs in section_groups.items():
        query = self._formulate_query_for_type(secs, section_type)
        guidelines = self.rag_service.retrieve(query, top_k=2)
        all_guidelines.extend(guidelines)

    return {"clarity_guidelines": self._merge_guidelines(all_guidelines)}
```

**Trade-offs:**
- ✅ More targeted guidelines
- ❌ More RAG calls (slower, more expensive)
- ❌ Need to balance speed vs. quality

---

### 4. LaTeX/Math Content Handling
**Status:** Basic, Needs Improvement
**Priority:** MEDIUM
**Impact:** Better handling of mathematical papers

**Issues:**
- Current query formulation treats LaTeX as plain text
- Math symbols pollute keyword detection
- `\begin{theorem}` vs. "Theorem 1:" not normalized

**Proposed Solution:**
```python
def _preprocess_content(self, content: str) -> str:
    """Normalize LaTeX and extract semantic content."""
    # Strip LaTeX commands
    content = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', ' ', content)

    # Normalize theorem-like environments
    content = re.sub(r'\\begin\{(theorem|lemma|proof)\}', r'\1:', content)

    # Handle math mode
    content = re.sub(r'\$[^$]+\$', ' [MATH] ', content)

    return content
```

**Files to Modify:**
- `app/agents/rag_nodes.py` - Add preprocessing step
- `app/services/latex_parser.py` - Enhance section parsing

---

### 5. Confidence Scores for Suggestions
**Status:** Not Implemented
**Priority:** LOW-MEDIUM
**Impact:** Help users prioritize suggestions

**Proposal:**
Add confidence field to suggestions:
```python
class StructuredSuggestion(BaseModel):
    issue: str
    explanation: str
    suggested_fix: str
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence score 0.0-1.0, where 1.0 is certain this is an issue"
    )
```

**Benefits:**
- Users can filter low-confidence suggestions
- Helps with false positives
- Better user experience

**Challenges:**
- LLMs aren't well-calibrated for confidence
- May need post-processing/calibration

---

## Low Priority / Future Ideas 💡

### 6. Additional Agents
**Ideas:**
- **Style Agent**: Consistency in terminology, tone, formatting
- **Grammar Agent**: Spelling, punctuation, sentence structure
- **Ethics Agent**: Citations, plagiarism checks, authorship

**Note:** Infrastructure already supports new agents (SuggestionType enum has placeholders)

---

### 7. Caching Improvements
**Current:** Semantic cache at query level
**Ideas:**
- Cache at section level (if same section reviewed multiple times)
- TTL-based cache invalidation
- Cache warming on startup

---

### 8. Interactive Suggestions
**Idea:** Allow users to:
- Accept/reject suggestions
- Mark as "helpful" / "not helpful"
- Use feedback to improve future suggestions (RLHF-style)

---

### 9. Batch Processing
**Idea:** Review multiple documents in one API call
- Upload folder of papers
- Batch review, generate report
- Compare papers against each other

---

### 10. Export & Reporting
**Features:**
- Export suggestions to PDF/DOCX
- Generate summary report (e.g., "Found 23 clarity issues")
- Track improvements over time (if user re-submits)

---

## Edge Cases to Handle

### Current Known Edge Cases:
1. **Short sections** (< 200 chars) → Generic queries
2. **Many sections** (10+) → Only first 2 sampled
3. **LaTeX-heavy content** → Keyword detection fails
4. **Code blocks** in papers → Treated as text
5. **Non-English content** → Keyword matching breaks
6. **False positives** → "theoretically" triggers "theorem" detection

**See:** Conversation "RAG Query Edge Cases" (2025-11-08) for detailed analysis

---

## Performance Benchmarks (To Track)

**Current Performance (Typical 3-section paper):**
- Total time: 5-10 seconds
- RAG retrieval: ~500ms per agent (2 total = 1s)
- LLM calls: ~3-5s per agent (6 sections × 2 agents)
- Semantic cache hit rate: TBD (need metrics)

**Target Performance:**
- < 5 seconds for 3-section paper
- < 15 seconds for 10-section paper
- Cache hit rate > 30%

---

## Technical Debt

### Code Quality
- [ ] Add comprehensive docstrings to all agent methods
- [ ] Type hints for all functions
- [ ] Error handling standardization
- [ ] Logging improvements (structured logging)

### Testing
- [ ] Unit tests for agents
- [ ] Integration tests for workflow
- [ ] RAG retrieval quality tests
- [ ] Frontend E2E tests

### Documentation
- [ ] API documentation (OpenAPI/Swagger)
- [ ] Agent architecture diagram
- [ ] RAG pipeline documentation
- [ ] Deployment guide (Railway/Render)

---

## Completed ✅

- [x] Implement structured LLM output with Pydantic
- [x] Separate issue/explanation/suggested_fix fields
- [x] Remove manual JSON parsing code
- [x] Update frontend to display structured suggestions
- [x] Fix duplicate "Suggested fix:" text in UI
- [x] Delete unused `AgentState` model
- [x] Fix `.env` inline comment issue
- [x] Create test notebook for agent outputs

---

## References & Resources

### Key Conversations
- Query Expansion with Embeddings (2025-11-08)
- Structured Output vs. JSON Parsing (2025-11-08)
- Pydantic Field Descriptions for Function Calling (2025-11-08)
- RAG Query Formulation Edge Cases (2025-11-08)

### External Resources
- LangChain Structured Output: https://python.langchain.com/docs/modules/model_io/chat/structured_output
- OpenAI Function Calling: https://platform.openai.com/docs/guides/function-calling
- Pseudo-Relevance Feedback: https://en.wikipedia.org/wiki/Relevance_feedback
- Query Expansion Techniques: [Academic Papers on IR]

---

**Last Updated:** 2025-11-08
**Next Review:** When starting next feature development
