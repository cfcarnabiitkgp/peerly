#!/usr/bin/env python3
"""
Simple test to check parallel vs sequential execution.
Just adds print statements to see timing.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import time
import asyncio

print("=" * 80)
print("Simple Parallel Execution Check")
print("=" * 80)

# Load example
example_path = Path("examples/example1/climate_prediction.tex")
content = example_path.read_text()

# Parse sections
from app.services.latex_parser import latex_parser
sections = latex_parser.parse_sections(content)
print(f"\nParsed {len(sections)} sections")

# Import workflow
from app.agents.review_workflow import review_workflow

# Monkey-patch the node methods to add logging
original_clarity_node = review_workflow._clarity_review_node
original_rigor_node = review_workflow._rigor_review_node

async def logged_clarity_node(state):
    print(f"[{time.time():.3f}] >>> CLARITY NODE START")
    result = await original_clarity_node(state)
    print(f"[{time.time():.3f}] <<< CLARITY NODE END")
    return result

async def logged_rigor_node(state):
    print(f"[{time.time():.3f}] >>> RIGOR NODE START")
    result = await original_rigor_node(state)
    print(f"[{time.time():.3f}] <<< RIGOR NODE END")
    return result

# Apply patches
review_workflow._clarity_review_node = logged_clarity_node
review_workflow._rigor_review_node = logged_rigor_node

print("\n" + "-" * 80)
print("Running workflow (watch the timestamps)...")
print("-" * 80 + "\n")

start_time = time.time()
print(f"[{start_time:.3f}] WORKFLOW START\n")

# Run workflow
result = asyncio.run(review_workflow.review(sections, agents=["clarity", "rigor"]))

end_time = time.time()
print(f"\n[{end_time:.3f}] WORKFLOW END")

# Restore
review_workflow._clarity_review_node = original_clarity_node
review_workflow._rigor_review_node = original_rigor_node

print("\n" + "=" * 80)
print(f"Total time: {end_time - start_time:.2f}s")
print("=" * 80)

print("\n" + "=" * 80)
print("Analysis:")
print("=" * 80)
print("\nIf you see:")
print("  >>> CLARITY NODE START")
print("  >>> RIGOR NODE START     ← Close timestamps = PARALLEL")
print("  <<< CLARITY NODE END")
print("  <<< RIGOR NODE END")
print("\nThen agents run in PARALLEL")
print("\nIf you see:")
print("  >>> CLARITY NODE START")
print("  <<< CLARITY NODE END")
print("  >>> RIGOR NODE START     ← Gap between = SEQUENTIAL")
print("  <<< RIGOR NODE END")
print("\nThen agents run SEQUENTIALLY")
print("=" * 80)
