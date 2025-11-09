#!/usr/bin/env python3
"""Debug script to see if equations are being filtered out."""

from pathlib import Path
from unstructured.partition.pdf import partition_pdf
from langchain_core.documents import Document

# Test on one rigor PDF
rigor_docs_path = Path("app/resources/rigor_docs")
pdf_file = list(rigor_docs_path.glob("*.pdf"))[0]

print(f"Analyzing: {pdf_file.name}")
print("="*80)

# Extract elements (same as embed_documents.py)
elements = partition_pdf(
    filename=str(pdf_file),
    strategy="fast",
    infer_table_structure=False,
)

# Filter headers/footers
filtered_elements = [
    el for el in elements
    if el.category not in ["Header", "Footer", "PageNumber"]
]

print(f"Total elements: {len(elements)}")
print(f"After filtering headers/footers: {len(filtered_elements)}")

# Convert to Documents
documents = []
for element in filtered_elements:
    if element.text.strip():
        doc = Document(
            page_content=element.text,
            metadata={
                "source": str(pdf_file),
                "element_type": element.category,
            }
        )
        documents.append(doc)

print(f"After removing empty elements: {len(documents)}")

# Check for equation-containing elements before quality filter
equation_indicators = ['=', '∫', '∑', '∂', '∆', 'lim', 'sup', 'inf', '±', '≤', '≥', '∀', '∃']

docs_with_equations = [
    doc for doc in documents
    if any(indicator in doc.page_content for indicator in equation_indicators)
]

print(f"Documents with equations (before quality filter): {len(docs_with_equations)}")

# Apply quality filters (same as embed_documents.py)
min_chunk_length = 200
quality_chunks = []
filtered_out_equations = []

for doc in documents:
    content = doc.page_content.strip()

    # Check if it has equations
    has_equations = any(indicator in content for indicator in equation_indicators)

    # Skip very short chunks
    if len(content) < min_chunk_length:
        if has_equations:
            filtered_out_equations.append((len(content), content[:200]))
        continue
    # Skip chunks that are just URLs or references
    if content.startswith("http://") or content.startswith("https://"):
        if has_equations:
            filtered_out_equations.append((len(content), content[:200]))
        continue
    # Skip chunks that are just "See" or similar navigation text
    if content.lower().startswith("see ") and len(content) < 100:
        if has_equations:
            filtered_out_equations.append((len(content), content[:200]))
        continue

    quality_chunks.append(doc)

docs_with_equations_after = [
    doc for doc in quality_chunks
    if any(indicator in doc.page_content for indicator in equation_indicators)
]

print(f"Documents with equations (after quality filter): {len(docs_with_equations_after)}")
print(f"\nEquation-containing chunks FILTERED OUT: {len(filtered_out_equations)}")

if filtered_out_equations:
    print("\nSample filtered equation chunks (first 5):")
    for i, (length, text) in enumerate(filtered_out_equations[:5], 1):
        print(f"\n[{i}] Length: {length} chars (< 200 minimum)")
        print(f"Text: {text}")
        print("-" * 40)

# Show sample of what WAS kept
if docs_with_equations_after:
    print(f"\n{'='*80}")
    print(f"Sample KEPT equation chunks (first 3):")
    print(f"{'='*80}")
    for i, doc in enumerate(docs_with_equations_after[:3], 1):
        print(f"\n[{i}] Length: {len(doc.page_content)} chars")
        print(f"Text: {doc.page_content[:400]}")
        if len(doc.page_content) > 400:
            print("...")
