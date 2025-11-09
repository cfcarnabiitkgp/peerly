# RAG Testing Guide

This directory contains tools for testing the RAG system for both Clarity and Rigor agents.

## Available Testing Tools

### 1. Interactive Jupyter Notebook (Recommended)

**File**: `test_rag.ipynb`

Comprehensive interactive testing with visualizations and detailed output.

**Features:**
- ✅ Qdrant connection testing
- ✅ Embedding cache performance testing
- ✅ Clarity agent RAG retrieval
- ✅ Rigor agent RAG retrieval
- ✅ RAG nodes workflow integration
- ✅ Retrieval strategy comparison
- ✅ Custom query testing
- ✅ Diagnostic information

**Usage:**
```bash
# Start Jupyter
jupyter notebook tests/test_rag.ipynb

# Or use VS Code / JupyterLab
code tests/test_rag.ipynb
```

**Sections:**
1. Setup and imports
2. Check Qdrant connection
3. Test embedding cache (verify caching works)
4. Test Clarity agent RAG
5. Test Rigor agent RAG
6. Test RAG nodes (workflow)
7. Compare retrieval strategies
8. Interactive query testing
9. Diagnostic information

---

### 2. Command-Line Test Script

**File**: `test_rag_simple.py`

Quick command-line testing for CI/CD or quick checks.

**Usage:**

```bash
# Test both agents with default queries
python tests/test_rag_simple.py

# Test specific agent
python tests/test_rag_simple.py --agent clarity
python tests/test_rag_simple.py --agent rigor

# Test with custom query
python tests/test_rag_simple.py --agent clarity --query "clear mathematical writing"

# Test RAG nodes (workflow integration)
python tests/test_rag_simple.py --nodes

# Combine options
python tests/test_rag_simple.py --agent clarity --query "proof validation" --nodes
```

**Options:**
- `--agent {clarity,rigor,both}`: Which agent to test (default: both)
- `--query TEXT`: Custom query to test
- `--nodes`: Test RAG nodes in workflow context

---

## Prerequisites

Before running tests, ensure:

1. **Qdrant is running:**
   ```bash
   docker run -p 6333:6333 qdrant/qdrant
   ```

2. **Documents are embedded:**
   ```bash
   python scripts/embed_documents.py --all
   ```

3. **Environment variables set:**
   ```bash
   # .env file should contain:
   OPENAI_API_KEY=your_key_here
   ```

4. **Dependencies installed:**
   ```bash
   uv pip install -e .
   # or
   pip install -e .
   ```

---

## What Gets Tested

### Connection Tests
- Qdrant server connectivity
- Collection existence and status
- Point counts per collection

### Caching Tests
- Cache directory existence
- Cache hit/miss performance
- Speedup verification (should be >100x)

### Retrieval Tests
- Query latency (target: <200ms naive, <500ms rerank)
- Result relevance
- Metadata filtering (agent-specific)

### Integration Tests
- RAG nodes with sample sections
- Query formulation logic
- Guidelines formatting

---

## Expected Results

### ✅ Successful Test Indicators

**Qdrant Connection:**
```
✓ Qdrant connected successfully
   Collections: 2
   - clarity_guidelines: 45 points
   - rigor_guidelines: 38 points
```

**Cache Performance:**
```
First run: 2.150s
Cached run: 0.008s
Speedup: 268x faster
✓ Cache working correctly!
```

**Retrieval:**
```
⏱️  Latency: 120ms
📄 Retrieved 3 documents
```

### ⚠️ Common Issues

**No collections found:**
```
⚠️  No collections found!
   Run: python scripts/embed_documents.py --all
```
**Solution:** Embed documents first

**Connection refused:**
```
❌ Error connecting to Qdrant: Connection refused
```
**Solution:** Start Qdrant: `docker run -p 6333:6333 qdrant/qdrant`

**No guidelines retrieved:**
```
⚠️  No guidelines retrieved
```
**Solution:** Check if PDFs exist in `app/resources/{agent}_docs/` and re-embed

---

## Testing Workflow

### Initial Setup Testing

```bash
# 1. Test connection
python tests/test_rag_simple.py

# 2. If successful, test interactively
jupyter notebook tests/test_rag.ipynb
```

### Adding New Documents

```bash
# 1. Add PDFs to appropriate folder
cp new_guide.pdf app/resources/clarity_docs/

# 2. Re-embed
python scripts/embed_documents.py --agent clarity

# 3. Test retrieval
python tests/test_rag_simple.py --agent clarity --query "test query"
```

### Performance Testing

```bash
# Run notebook section 2 (cache testing)
# Expected: First run slow, second run >100x faster

# Run notebook section 6 (strategy comparison)
# Expected: Naive <200ms, Rerank <500ms
```

### Debugging Issues

```bash
# 1. Check diagnostics
# Run notebook section 8

# 2. Verify Qdrant
curl http://localhost:6333/collections

# 3. Check cache
ls -lh app/embedding_cache/*/

# 4. Check documents
ls app/resources/clarity_docs/*.pdf
```

---

## Advanced Testing

### Test Custom Retrieval Strategy

In the notebook, modify retrieval config:

```python
# Cell to add:
from app.rag.config import clarity_rag_config

# Change strategy
clarity_rag_config.retrieval_config.retriever_type = "rerank"
clarity_rag_config.retrieval_config.top_k = 5

# Re-test
service = RAGService(config=clarity_rag_config)
results = service.retrieve("your query")
```

### Benchmark Specific Queries

```python
# Add to notebook:
import time

queries = ["query1", "query2", "query3"]
latencies = []

for query in queries:
    start = time.time()
    results = service.retrieve(query)
    latencies.append(time.time() - start)

print(f"Average: {sum(latencies)/len(latencies)*1000:.0f}ms")
print(f"Min: {min(latencies)*1000:.0f}ms")
print(f"Max: {max(latencies)*1000:.0f}ms")
```

### Test Different Chunk Sizes

```bash
# 1. Modify config
# In app/rag/config.py, change chunk_size

# 2. Re-embed
python scripts/embed_documents.py --agent clarity

# 3. Test retrieval
python tests/test_rag_simple.py --agent clarity

# 4. Compare results in notebook
```

---

## Continuous Integration

### CI Pipeline Test Script

```bash
#!/bin/bash
# tests/ci_test_rag.sh

set -e

echo "Starting Qdrant..."
docker run -d -p 6333:6333 --name qdrant-test qdrant/qdrant

echo "Waiting for Qdrant..."
sleep 5

echo "Embedding documents..."
python scripts/embed_documents.py --all

echo "Testing RAG..."
python tests/test_rag_simple.py

echo "Cleanup..."
docker stop qdrant-test
docker rm qdrant-test

echo "✓ All tests passed!"
```

---

## Performance Benchmarks

### Expected Performance

| Metric | Target | Good | Excellent |
|--------|--------|------|-----------|
| Cache speedup | >50x | >100x | >200x |
| Naive latency | <200ms | <150ms | <100ms |
| Rerank latency | <500ms | <400ms | <300ms |
| Results per query | 3-5 | 3 | 3 |

### Measuring Performance

Use the notebook section 6 or add to script:

```python
import time
import statistics

# Warm-up
service.retrieve("test", top_k=1)

# Benchmark
latencies = []
for _ in range(10):
    start = time.time()
    service.retrieve("test query", top_k=3)
    latencies.append(time.time() - start)

print(f"Mean: {statistics.mean(latencies)*1000:.0f}ms")
print(f"Median: {statistics.median(latencies)*1000:.0f}ms")
print(f"Stdev: {statistics.stdev(latencies)*1000:.0f}ms")
```

---

## Troubleshooting

### Issue: Slow First Run

**Normal behavior!** First run generates embeddings.
- First run: ~2-3 seconds
- Cached runs: <0.01 seconds

### Issue: No Results Retrieved

**Checklist:**
1. ✅ Qdrant running?
2. ✅ Documents embedded?
3. ✅ Collections exist?
4. ✅ PDFs in correct folders?

```bash
# Verify
curl http://localhost:6333/collections
ls app/resources/clarity_docs/*.pdf
python scripts/embed_documents.py --all
```

### Issue: Import Errors

```bash
# Reinstall dependencies
uv pip install -e .

# Verify imports
python -c "from app.rag.rag_service import RAGService; print('OK')"
```

### Issue: Inconsistent Results

**Possible causes:**
1. Reranking with temperature > 0
2. Different queries
3. Collection changes

**Solution:** Use naive retrieval for consistent results

---

## Tips

1. **Start with notebook** - More detailed output and visualization
2. **Use script for CI** - Automated testing
3. **Test incrementally** - One agent at a time
4. **Check diagnostics** - Section 8 of notebook
5. **Clear cache to reset** - `rm -rf app/embedding_cache/*/`

---

## Next Steps After Testing

Once tests pass:

1. ✅ RAG is working correctly
2. ✅ Ready for workflow integration
3. ✅ Can run review on actual documents

```bash
# Test full workflow
python -m app.main
# Or run FastAPI server
uvicorn app.main:app --reload
```

---

## Support

- Check main docs: `RAG_QUICKSTART.md`, `RAG_ARCHITECTURE.md`
- LangChain docs: https://python.langchain.com/docs/
- Qdrant docs: https://qdrant.tech/documentation/
- Issues: GitHub repository

---

Happy testing! 🚀
