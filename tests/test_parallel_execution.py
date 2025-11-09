#!/usr/bin/env python3
"""
Test to verify if agents execute in parallel or sequential.

This test will:
1. Instrument the workflow with timing logs
2. Run a review
3. Analyze timestamps to determine execution order
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import time
import asyncio
from unittest.mock import patch
from pathlib import Path

# Store timing events
timing_events = []

def log_event(event_name: str):
    """Log an event with timestamp."""
    timing_events.append({
        "event": event_name,
        "timestamp": time.time(),
        "time_since_start": time.time() - start_time if 'start_time' in globals() else 0
    })
    print(f"[{time.time():.3f}] {event_name}")


async def test_parallel_execution():
    """Test if agents run in parallel or sequential."""
    global start_time, timing_events

    print("=" * 80)
    print("Testing Parallel vs Sequential Execution")
    print("=" * 80)

    # Load example document
    example_path = Path("examples/example1/climate_prediction.tex")
    content = example_path.read_text()

    # Parse sections
    from app.services.latex_parser import latex_parser
    sections = latex_parser.parse_sections(content)
    print(f"\nParsed {len(sections)} sections")

    # Instrument the workflow by patching the agent review methods
    from app.agents.review_workflow import review_workflow

    # Patch clarity agent
    original_clarity_review = review_workflow.clarity_agent.review_section
    async def instrumented_clarity_review(*args, **kwargs):
        log_event("CLARITY_START")
        result = await original_clarity_review(*args, **kwargs)
        log_event("CLARITY_END")
        return result

    # Patch rigor agent
    original_rigor_review = review_workflow.rigor_agent.review_section
    async def instrumented_rigor_review(*args, **kwargs):
        log_event("RIGOR_START")
        result = await original_rigor_review(*args, **kwargs)
        log_event("RIGOR_END")
        return result

    # Patch RAG nodes if they exist
    clarity_rag_called = False
    rigor_rag_called = False

    if hasattr(review_workflow, 'clarity_rag_node'):
        original_clarity_rag = review_workflow.clarity_rag_node.__call__
        async def instrumented_clarity_rag(*args, **kwargs):
            nonlocal clarity_rag_called
            clarity_rag_called = True
            log_event("CLARITY_RAG_START")
            result = await original_clarity_rag(*args, **kwargs)
            log_event("CLARITY_RAG_END")
            return result
        review_workflow.clarity_rag_node.__call__ = instrumented_clarity_rag

    if hasattr(review_workflow, 'rigor_rag_node'):
        original_rigor_rag = review_workflow.rigor_rag_node.__call__
        async def instrumented_rigor_rag(*args, **kwargs):
            nonlocal rigor_rag_called
            rigor_rag_called = True
            log_event("RIGOR_RAG_START")
            result = await original_rigor_rag(*args, **kwargs)
            log_event("RIGOR_RAG_END")
            return result
        review_workflow.rigor_rag_node.__call__ = instrumented_rigor_rag

    # Apply patches
    review_workflow.clarity_agent.review_section = instrumented_clarity_review
    review_workflow.rigor_agent.review_section = instrumented_rigor_review

    # Reset timing
    timing_events = []
    start_time = time.time()

    print("\n" + "-" * 80)
    print("Running workflow with instrumentation...")
    print("-" * 80 + "\n")

    log_event("WORKFLOW_START")

    # Run the workflow
    result = await review_workflow.review(sections, agents=["clarity", "rigor"])

    log_event("WORKFLOW_END")

    total_time = time.time() - start_time

    # Restore original methods
    review_workflow.clarity_agent.review_section = original_clarity_review
    review_workflow.rigor_agent.review_section = original_rigor_review
    if hasattr(review_workflow, 'clarity_rag_node'):
        review_workflow.clarity_rag_node.__call__ = original_clarity_rag
    if hasattr(review_workflow, 'rigor_rag_node'):
        review_workflow.rigor_rag_node.__call__ = original_rigor_rag

    # Analyze timing
    print("\n" + "=" * 80)
    print("Timing Analysis")
    print("=" * 80)

    # Print all events
    print("\nAll Events (chronological):")
    for event in timing_events:
        print(f"  {event['time_since_start']:6.2f}s - {event['event']}")

    # Find key events
    clarity_start = next((e for e in timing_events if e['event'] == 'CLARITY_RAG_START' or e['event'] == 'CLARITY_START'), None)
    rigor_start = next((e for e in timing_events if e['event'] == 'RIGOR_RAG_START' or e['event'] == 'RIGOR_START'), None)

    print("\n" + "-" * 80)
    print("Parallel Execution Check:")
    print("-" * 80)

    if clarity_start and rigor_start:
        time_diff = abs(clarity_start['time_since_start'] - rigor_start['time_since_start'])

        print(f"\nClarity started at: {clarity_start['time_since_start']:.2f}s")
        print(f"Rigor started at:   {rigor_start['time_since_start']:.2f}s")
        print(f"Time difference:    {time_diff:.2f}s")

        if time_diff < 1.0:
            print("\n✅ PARALLEL EXECUTION DETECTED!")
            print(f"   Both agents started within {time_diff:.2f}s of each other")
            print("   This suggests agents run in parallel")
        else:
            print("\n❌ SEQUENTIAL EXECUTION DETECTED!")
            print(f"   Agents started {time_diff:.2f}s apart")
            print("   This suggests agents run sequentially")

            # Try to determine which ran first
            if clarity_start['time_since_start'] < rigor_start['time_since_start']:
                print("   Execution order: Clarity → Rigor")
            else:
                print("   Execution order: Rigor → Clarity")
    else:
        print("\n⚠ Could not determine execution order (missing events)")

    print("\n" + "-" * 80)
    print(f"Total workflow time: {total_time:.2f}s")
    print("-" * 80)

    # Count section review calls
    clarity_calls = sum(1 for e in timing_events if e['event'] == 'CLARITY_START')
    rigor_calls = sum(1 for e in timing_events if e['event'] == 'RIGOR_START')

    print(f"\nSection reviews:")
    print(f"  Clarity: {clarity_calls} sections reviewed")
    print(f"  Rigor:   {rigor_calls} sections reviewed")

    # Check if sections are processed in parallel within each agent
    clarity_starts = [e['time_since_start'] for e in timing_events if e['event'] == 'CLARITY_START']
    if len(clarity_starts) > 1:
        section_time_diffs = [clarity_starts[i+1] - clarity_starts[i] for i in range(len(clarity_starts)-1)]
        avg_diff = sum(section_time_diffs) / len(section_time_diffs) if section_time_diffs else 0

        print(f"\nClarity section processing:")
        if all(diff < 0.1 for diff in section_time_diffs):
            print(f"  ✅ PARALLEL - All sections started nearly simultaneously")
        else:
            print(f"  ❌ SEQUENTIAL - Average {avg_diff:.2f}s between sections")

    return timing_events


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("Parallel Execution Diagnostic Test")
    print("=" * 80)
    print("\nThis test will:")
    print("  1. Instrument the workflow with timing logs")
    print("  2. Run a review on example1")
    print("  3. Analyze timestamps to determine execution order")
    print("  4. Report if agents run in parallel or sequential")

    try:
        timing_events = asyncio.run(test_parallel_execution())

        print("\n" + "=" * 80)
        print("Test Complete!")
        print("=" * 80)

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
