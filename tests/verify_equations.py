#!/usr/bin/env python3
"""Verify that equation chunks are now in the collection."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from qdrant_client import QdrantClient
from app.rag.config import rigor_rag_config
from app.rag.rag_service import RAGService

# Mathematical symbols
math_symbols = ['=', '∫', '∑', '∂', '∆', 'lim', 'sup', 'inf', '±', '≤', '≥',
                '∀', '∃', '⊥', '∧', '∨', '→', '¬', '∈', '⊂', '⊆', '∪', '∩']

print("="*80)
print("RIGOR Collection - Equation Verification")
print("="*80)

# Create RAG service
qdrant_client = QdrantClient(url="http://localhost:6333")
service = RAGService(config=rigor_rag_config, qdrant_client=qdrant_client)

# Get collection info
collection_info = qdrant_client.get_collection(rigor_rag_config.collection_name)
print(f"\nTotal chunks: {collection_info.points_count}")

# Test query for mathematical content
query = "formal logic rules and inference symbols"
print(f"\nTest Query: '{query}'")

results = service.retrieve_with_scores(query, top_k=5)

print(f"\nRetrieved {len(results)} chunks:\n")

equation_count = 0
for i, (doc, score) in enumerate(results, 1):
    has_math = any(symbol in doc.page_content for symbol in math_symbols)
    if has_math:
        equation_count += 1

    print(f"--- Chunk {i} (Similarity: {score:.4f}) ---")
    print(f"Has math symbols: {'YES' if has_math else 'NO'}")
    print(f"Length: {len(doc.page_content)} chars")
    print(f"Content: {doc.page_content[:300]}")
    if len(doc.page_content) > 300:
        print("...")
    print()

print(f"Chunks with equations: {equation_count}/{len(results)}")

# Show some short equation chunks
print("\n" + "="*80)
print("Sample SHORT equation chunks (50-150 chars):")
print("="*80)

# Do a broader search to find short chunks
all_results = service.retrieve_with_scores("mathematical notation logic", top_k=20)

short_equation_chunks = []
for doc, score in all_results:
    content = doc.page_content.strip()
    has_math = any(symbol in content for symbol in math_symbols)
    if has_math and 50 <= len(content) <= 150:
        short_equation_chunks.append((content, len(content), score))

# Show unique ones
seen = set()
count = 0
for content, length, score in short_equation_chunks:
    if content not in seen and count < 5:
        seen.add(content)
        count += 1
        print(f"\n[{count}] Length: {length} chars, Score: {score:.4f}")
        print(f"Content: {content}")

if count == 0:
    print("\nNo short equation chunks found in top 20 results.")
    print("This is normal - short chunks may rank lower in semantic search.")
