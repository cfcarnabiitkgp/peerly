#!/usr/bin/env python3
"""Debug script to see what Unstructured extracts from rigor PDFs."""

from pathlib import Path
from unstructured.partition.pdf import partition_pdf

# Test on one rigor PDF
rigor_docs_path = Path("app/resources/rigor_docs")
pdf_files = list(rigor_docs_path.glob("*.pdf"))

if pdf_files:
    test_pdf = pdf_files[0]
    print(f"Analyzing: {test_pdf.name}")
    print("="*80)

    # Extract elements
    elements = partition_pdf(
        filename=str(test_pdf),
        strategy="fast",
        infer_table_structure=False,
    )

    print(f"\nTotal elements extracted: {len(elements)}")
    print("\nElement type distribution:")

    # Count element types
    type_counts = {}
    for el in elements:
        type_counts[el.category] = type_counts.get(el.category, 0) + 1

    for el_type, count in sorted(type_counts.items()):
        print(f"  {el_type}: {count}")

    # Show sample elements
    print("\n" + "="*80)
    print("Sample elements (first 10 non-empty):")
    print("="*80)

    count = 0
    for i, el in enumerate(elements):
        if el.text.strip() and count < 10:
            count += 1
            print(f"\n[{i}] Type: {el.category}")
            print(f"Length: {len(el.text)} chars")
            print(f"Text: {el.text[:300]}")
            if len(el.text) > 300:
                print("...")

    # Look for elements that might contain equations
    print("\n" + "="*80)
    print("Searching for potential equation-containing elements:")
    print("="*80)

    equation_indicators = ['=', '∫', '∑', '∂', '∆', 'lim', 'sup', 'inf', '±', '≤', '≥']

    found_count = 0
    for i, el in enumerate(elements):
        text = el.text.strip()
        if any(indicator in text for indicator in equation_indicators):
            found_count += 1
            if found_count <= 5:  # Show first 5
                print(f"\n[{i}] Type: {el.category}")
                print(f"Text: {text[:400]}")
                if len(text) > 400:
                    print("...")

    print(f"\nTotal elements with equation indicators: {found_count}")
