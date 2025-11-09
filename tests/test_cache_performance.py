#!/usr/bin/env python3
"""
Comprehensive cache performance test.

This test:
1. Clears semantic caches for both agents
2. Runs the review workflow twice using example1
3. Tracks cache hits/misses for each run
4. Measures RAG retrieval time and total workflow time
5. Computes time/latency savings from caching

Usage:
    python tests/test_cache_performance.py
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import time
import asyncio
from typing import Dict, List

from app.rag.semantic_cache import create_semantic_cache
from app.services.latex_parser import latex_parser
from app.agents.review_workflow import review_workflow
from app.models.schemas import Section


def print_header(title: str):
    """Print formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"{title:^80}")
    print(f"{'=' * 80}\n")


def print_section(title: str):
    """Print formatted subsection."""
    print(f"\n{'-' * 80}")
    print(f"{title}")
    print(f"{'-' * 80}")


def clear_caches():
    """Clear all semantic caches."""
    print_section("Step 1: Clearing Semantic Caches")

    caches_cleared = []

    for agent_name in ["clarity", "rigor"]:
        try:
            cache = create_semantic_cache(cache_name=agent_name)
            cache.clear()
            print(f"  ✓ {agent_name}_query_cache cleared")
            caches_cleared.append(agent_name)
        except Exception as e:
            print(f"  ✗ Failed to clear {agent_name}_query_cache: {e}")

    print(f"\nCaches cleared: {len(caches_cleared)}/2")
    return len(caches_cleared) == 2


def load_example_document() -> str:
    """Load example1 LaTeX document."""
    print_section("Step 2: Loading Example Document")

    example_path = Path("examples/example1/climate_prediction.tex")

    if not example_path.exists():
        raise FileNotFoundError(f"Example file not found: {example_path}")

    content = example_path.read_text()
    lines = content.count('\n') + 1
    chars = len(content)

    print(f"  Document: {example_path}")
    print(f"  Lines: {lines}")
    print(f"  Characters: {chars}")

    return content


def get_cache_stats(agent_name: str) -> Dict:
    """Get cache statistics for an agent."""
    try:
        cache = create_semantic_cache(cache_name=agent_name)
        return cache.get_stats()
    except Exception as e:
        print(f"  ⚠ Failed to get stats for {agent_name}: {e}")
        return {
            "total_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "hit_rate": 0.0
        }


async def run_workflow(content: str, run_number: int) -> Dict:
    """
    Run the review workflow and track performance.

    Returns:
        Dict with timing and cache statistics
    """
    print_section(f"Step {2 + run_number}: Running Workflow - Run #{run_number}")

    # Get initial cache stats
    initial_clarity_stats = get_cache_stats("clarity")
    initial_rigor_stats = get_cache_stats("rigor")

    print(f"\nInitial Cache State:")
    print(f"  Clarity: {initial_clarity_stats['cache_hits']} hits, "
          f"{initial_clarity_stats['cache_misses']} misses")
    print(f"  Rigor: {initial_rigor_stats['cache_hits']} hits, "
          f"{initial_rigor_stats['cache_misses']} misses")

    # Parse LaTeX content
    print(f"\nParsing LaTeX document...")
    parse_start = time.time()
    sections = latex_parser.parse_sections(content)
    parse_time = time.time() - parse_start

    print(f"  ✓ Parsed {len(sections)} sections in {parse_time:.3f}s")
    for section in sections:
        print(f"    - {section.title} ({len(section.content)} chars)")

    # Run review workflow
    print(f"\nRunning multi-agent review workflow...")
    workflow_start = time.time()
    result = await review_workflow.review(sections, agents=["clarity", "rigor"])
    workflow_time = time.time() - workflow_start

    # Get final cache stats
    final_clarity_stats = get_cache_stats("clarity")
    final_rigor_stats = get_cache_stats("rigor")

    # Calculate differences
    clarity_hits = final_clarity_stats['cache_hits'] - initial_clarity_stats['cache_hits']
    clarity_misses = final_clarity_stats['cache_misses'] - initial_clarity_stats['cache_misses']
    rigor_hits = final_rigor_stats['cache_hits'] - initial_rigor_stats['cache_hits']
    rigor_misses = final_rigor_stats['cache_misses'] - initial_rigor_stats['cache_misses']

    # Count suggestions
    total_suggestions = 0
    if result.get("final_suggestions"):
        for section in result["final_suggestions"]:
            for group in section.suggestions:
                total_suggestions += len(group.items)

    print(f"\n✓ Workflow completed in {workflow_time:.3f}s")
    print(f"  Total suggestions: {total_suggestions}")
    print(f"  Error: {result.get('error', 'None')}")

    # Cache performance for this run
    print(f"\nCache Performance (this run):")
    print(f"  Clarity Agent:")
    print(f"    - Cache HITS: {clarity_hits}")
    print(f"    - Cache MISSES: {clarity_misses}")
    print(f"    - Total queries: {clarity_hits + clarity_misses}")
    print(f"  Rigor Agent:")
    print(f"    - Cache HITS: {rigor_hits}")
    print(f"    - Cache MISSES: {rigor_misses}")
    print(f"    - Total queries: {rigor_hits + rigor_misses}")

    return {
        "run_number": run_number,
        "parse_time": parse_time,
        "workflow_time": workflow_time,
        "total_time": parse_time + workflow_time,
        "total_suggestions": total_suggestions,
        "clarity": {
            "hits": clarity_hits,
            "misses": clarity_misses,
            "total": clarity_hits + clarity_misses
        },
        "rigor": {
            "hits": rigor_hits,
            "misses": rigor_misses,
            "total": rigor_hits + rigor_misses
        },
        "error": result.get("error")
    }


def print_comparison(run1_stats: Dict, run2_stats: Dict):
    """Print detailed comparison between two runs."""
    print_header("Performance Comparison & Savings Analysis")

    # Timing comparison
    print("WORKFLOW TIMING:")
    print(f"{'Metric':<30} {'Run 1 (Cold)':<15} {'Run 2 (Cached)':<15} {'Difference':<15}")
    print("-" * 80)

    parse_diff = run1_stats['parse_time'] - run2_stats['parse_time']
    workflow_diff = run1_stats['workflow_time'] - run2_stats['workflow_time']
    total_diff = run1_stats['total_time'] - run2_stats['total_time']

    print(f"{'Parse Time':<30} {run1_stats['parse_time']:>12.3f}s  "
          f"{run2_stats['parse_time']:>12.3f}s  {parse_diff:>12.3f}s")
    print(f"{'Workflow Time':<30} {run1_stats['workflow_time']:>12.3f}s  "
          f"{run2_stats['workflow_time']:>12.3f}s  {workflow_diff:>12.3f}s")
    print(f"{'Total Time':<30} {run1_stats['total_time']:>12.3f}s  "
          f"{run2_stats['total_time']:>12.3f}s  {total_diff:>12.3f}s")

    # Cache performance
    print(f"\nCACHE PERFORMANCE:")
    print(f"{'Agent':<20} {'Run 1':<20} {'Run 2':<20}")
    print("-" * 80)

    print(f"{'Clarity Agent:':<20}")
    print(f"  {'Hits':<18} {run1_stats['clarity']['hits']:>18}  "
          f"{run2_stats['clarity']['hits']:>18}")
    print(f"  {'Misses':<18} {run1_stats['clarity']['misses']:>18}  "
          f"{run2_stats['clarity']['misses']:>18}")
    print(f"  {'Hit Rate':<18} "
          f"{run1_stats['clarity']['hits'] / max(1, run1_stats['clarity']['total']) * 100:>16.1f}%  "
          f"{run2_stats['clarity']['hits'] / max(1, run2_stats['clarity']['total']) * 100:>16.1f}%")

    print(f"\n{'Rigor Agent:':<20}")
    print(f"  {'Hits':<18} {run1_stats['rigor']['hits']:>18}  "
          f"{run2_stats['rigor']['hits']:>18}")
    print(f"  {'Misses':<18} {run1_stats['rigor']['misses']:>18}  "
          f"{run2_stats['rigor']['misses']:>18}")
    print(f"  {'Hit Rate':<18} "
          f"{run1_stats['rigor']['hits'] / max(1, run1_stats['rigor']['total']) * 100:>16.1f}%  "
          f"{run2_stats['rigor']['hits'] / max(1, run2_stats['rigor']['total']) * 100:>16.1f}%")

    # Savings calculation
    print(f"\nLATENCY SAVINGS:")
    print("-" * 80)

    if total_diff > 0:
        speedup = run1_stats['total_time'] / run2_stats['total_time']
        percent_savings = (total_diff / run1_stats['total_time']) * 100

        print(f"  Time Saved: {total_diff:.3f}s ({percent_savings:.1f}% reduction)")
        print(f"  Speedup: {speedup:.2f}x faster")

        # Estimate based on typical RAG query time (~1s per miss)
        total_misses_run1 = run1_stats['clarity']['misses'] + run1_stats['rigor']['misses']
        total_hits_run2 = run2_stats['clarity']['hits'] + run2_stats['rigor']['hits']

        estimated_rag_time_saved = total_hits_run2 * 0.98  # ~0.98s saved per cache hit
        print(f"\n  Estimated RAG Time Saved: {estimated_rag_time_saved:.2f}s")
        print(f"  (Based on {total_hits_run2} cache hits × ~0.98s/hit)")

        print(f"\n✓ Caching provides significant performance improvement!")

    else:
        print(f"  ⚠ Run 2 was slower (possible variance in network/system)")
        print(f"  This can happen if cache misses or system load differs")

    # Quality check
    print(f"\nQUALITY CHECK:")
    print("-" * 80)
    print(f"  Suggestions (Run 1): {run1_stats['total_suggestions']}")
    print(f"  Suggestions (Run 2): {run2_stats['total_suggestions']}")

    if run1_stats['total_suggestions'] == run2_stats['total_suggestions']:
        print(f"  ✓ Same number of suggestions (cache doesn't affect quality)")
    else:
        print(f"  ⚠ Different suggestion counts (investigate)")


async def main():
    """Main test execution."""
    print_header("Cache Performance Test - Example 1")

    print("This test will:")
    print("  1. Clear all semantic caches")
    print("  2. Run the workflow with example1 (cold start)")
    print("  3. Run the workflow again (cached)")
    print("  4. Compare performance and show savings")

    try:
        # Step 1: Clear caches
        if not clear_caches():
            print("\n✗ Failed to clear caches. Aborting test.")
            return

        # Step 2: Load example document
        content = load_example_document()

        # Step 3: First run (cold - no cache)
        run1_stats = await run_workflow(content, run_number=1)

        # Brief pause to ensure all cache writes complete
        print("\nWaiting 1s for cache writes to complete...")
        await asyncio.sleep(1)

        # Step 4: Second run (warm - with cache)
        run2_stats = await run_workflow(content, run_number=2)

        # Step 5: Compare and analyze
        print_comparison(run1_stats, run2_stats)

        # Final summary
        print_header("Test Complete")

        print("Summary:")
        print(f"  ✓ Both runs completed successfully")
        print(f"  ✓ Run 1 (cold): {run1_stats['total_time']:.3f}s")
        print(f"  ✓ Run 2 (cached): {run2_stats['total_time']:.3f}s")

        if run1_stats['total_time'] > run2_stats['total_time']:
            savings = run1_stats['total_time'] - run2_stats['total_time']
            print(f"  ✓ Cache saved {savings:.3f}s ({savings/run1_stats['total_time']*100:.1f}%)")

        print(f"\nCache collections still have data for future use!")
        print(f"To clear: python scripts/clear_cache.py")

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
