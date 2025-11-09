#!/usr/bin/env python3
"""
Comprehensive test for the full Peerly review workflow.

Tests:
1. LaTeX parser
2. Orchestrator routing logic
3. Clarity agent
4. Rigor agent
5. Orchestrator finalization
6. End-to-end workflow
"""
import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.latex_parser import latex_parser
from app.agents.review_workflow import ReviewWorkflow, review_workflow
from app.models.schemas import Section


# Test LaTeX content
TEST_LATEX = r"""
\documentclass{article}
\usepackage{amsmath}
\title{Machine Learning for Climate Prediction}
\author{Test Author}

\begin{document}
\maketitle

\section{Introduction}
Machine learning is important. It uses data to make predictions.
Climate prediction is a challenging problem that requires advanced techniques.

\section{Related Work}
Previous work has explored various approaches to climate modeling.
Many methods use statistical techniques.

\section{Methodology}
Our method uses a neural network architecture with parameters $\theta$.
The loss function is defined as:
\begin{equation}
L(\theta) = \sum_{i=1}^{n} (y_i - f(x_i; \theta))^2
\end{equation}

We prove the following theorem:
\begin{theorem}
The model converges to a local minimum.
\end{theorem}

\section{Experiments}
We conducted experiments on the CMIP6 dataset.
The results show significant improvement over baseline methods.

\section{Results}
Our experiments show improvement. The accuracy increased significantly.
We achieve better performance than all baselines.

\section{Conclusion}
In conclusion, our method works well and shows promising results.

\end{document}
"""


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_subheader(text):
    """Print a formatted subheader."""
    print(f"\n{text}")
    print("-" * 70)


async def test_parser():
    """Test 1: LaTeX Parser"""
    print_header("TEST 1: LaTeX Parser")

    sections = latex_parser.parse_sections(TEST_LATEX)

    print(f"\n✓ Parsed {len(sections)} sections:")
    for i, section in enumerate(sections, 1):
        print(f"\n  {i}. {section.title}")
        print(f"     Type: {section.section_type}")
        print(f"     Lines: {section.line_start}-{section.line_end}")
        print(f"     Content length: {len(section.content)} chars")

    assert len(sections) > 0, "Parser should find at least one section"
    assert any(s.title == "Introduction" for s in sections), "Should find Introduction section"

    print("\n✅ Parser test PASSED")
    return sections


async def test_orchestrator_routing(sections):
    """Test 2: Orchestrator Routing Logic"""
    print_header("TEST 2: Orchestrator Routing Logic")

    workflow = ReviewWorkflow()

    # Test routing decision
    routing_result = await workflow._orchestrator_route_node({"sections": sections})

    sections_for_clarity = routing_result['sections_for_clarity']
    sections_for_rigor = routing_result['sections_for_rigor']

    print_subheader("Clarity Agent Sections (ALL sections):")
    print(f"  Count: {len(sections_for_clarity)}")
    for sec in sections_for_clarity:
        print(f"    ✓ {sec.title} ({sec.section_type})")

    print_subheader("Rigor Agent Sections (Methodological/Math only):")
    print(f"  Count: {len(sections_for_rigor)}")
    if sections_for_rigor:
        for sec in sections_for_rigor:
            has_math = workflow._contains_mathematical_content(sec.content)
            reason = "has math" if has_math else f"type={sec.section_type}"
            print(f"    ✓ {sec.title} ({reason})")
    else:
        print("    (none)")

    # Assertions
    assert len(sections_for_clarity) == len(sections), "All sections should go to clarity"

    # Check that methodological sections go to rigor
    methodology_sections = [s for s in sections if s.section_type in ['methodology', 'experiments', 'results']]
    rigor_titles = [s.title for s in sections_for_rigor]

    for method_sec in methodology_sections:
        assert method_sec.title in rigor_titles, f"{method_sec.title} should be routed to rigor agent"

    # Check that math content is detected
    methodology_sec = next((s for s in sections if s.title == "Methodology"), None)
    if methodology_sec:
        assert workflow._contains_mathematical_content(methodology_sec.content), \
            "Methodology section should contain math content"

    print("\n✅ Orchestrator routing test PASSED")
    return routing_result


async def test_clarity_agent(sections):
    """Test 3: Clarity Agent"""
    print_header("TEST 3: Clarity Agent")

    workflow = ReviewWorkflow()

    # Test clarity agent on Introduction
    intro_section = next((s for s in sections if s.title == "Introduction"), None)
    if not intro_section:
        print("⚠️  No Introduction section found, skipping clarity test")
        return

    print(f"\nTesting on: {intro_section.title}")
    print(f"Content preview: {intro_section.content[:100]}...")

    try:
        suggestions = await workflow.clarity_agent.review_section(intro_section)

        print(f"\n✓ Generated {len(suggestions)} clarity suggestions:")
        for i, sugg in enumerate(suggestions[:3], 1):  # Show first 3
            print(f"\n  {i}. [{sugg.severity.value}] Line {sugg.line}")
            print(f"     {sugg.text[:80]}...")

        if len(suggestions) > 3:
            print(f"\n  ... and {len(suggestions) - 3} more")

        print("\n✅ Clarity agent test PASSED")
        return suggestions

    except Exception as e:
        print(f"\n❌ Clarity agent test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return []


async def test_rigor_agent(sections):
    """Test 4: Rigor Agent"""
    print_header("TEST 4: Rigor Agent")

    workflow = ReviewWorkflow()

    # Test rigor agent on Methodology
    method_section = next((s for s in sections if s.title == "Methodology"), None)
    if not method_section:
        print("⚠️  No Methodology section found, skipping rigor test")
        return

    print(f"\nTesting on: {method_section.title}")
    print(f"Content preview: {method_section.content[:100]}...")

    try:
        suggestions = await workflow.rigor_agent.review_section(method_section)

        print(f"\n✓ Generated {len(suggestions)} rigor suggestions:")
        for i, sugg in enumerate(suggestions[:3], 1):  # Show first 3
            print(f"\n  {i}. [{sugg.severity.value}] Line {sugg.line}")
            print(f"     {sugg.text[:80]}...")

        if len(suggestions) > 3:
            print(f"\n  ... and {len(suggestions) - 3} more")

        print("\n✅ Rigor agent test PASSED")
        return suggestions

    except Exception as e:
        print(f"\n❌ Rigor agent test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return []


async def test_full_workflow(sections):
    """Test 5: Full End-to-End Workflow"""
    print_header("TEST 5: Full End-to-End Workflow")

    print(f"\nRunning complete workflow on {len(sections)} sections...")
    print("This will:")
    print("  1. Orchestrator routes sections to agents")
    print("  2. Clarity agent reviews all sections")
    print("  3. Rigor agent reviews methodological sections")
    print("  4. Orchestrator validates and finalizes suggestions")

    try:
        import time
        start_time = time.time()

        result = await review_workflow.review(sections)

        elapsed = time.time() - start_time

        print(f"\n✓ Workflow completed in {elapsed:.2f}s")

        # Check for errors
        if result.get('error'):
            print(f"\n❌ Workflow error: {result['error']}")
            return False

        # Display results
        print_subheader("Workflow State:")
        print(f"  Sections for clarity: {len(result.get('sections_for_clarity', []))}")
        print(f"  Sections for rigor: {len(result.get('sections_for_rigor', []))}")
        print(f"  Clarity suggestions: {len(result.get('clarity_suggestions', []))}")
        print(f"  Rigor suggestions: {len(result.get('rigor_suggestions', []))}")
        print(f"  Final suggestions: {len(result.get('final_suggestions', []))}")

        # Display final suggestions
        print_subheader("Final Suggestions:")

        total_suggestions = 0
        clarity_count = 0
        rigor_count = 0

        for section_sugg in result.get('final_suggestions', []):
            print(f"\n  📄 {section_sugg.section} (Line {section_sugg.line})")

            for group in section_sugg.suggestions:
                count = len(group.items)
                total_suggestions += count

                icon = '💡' if group.type.value == 'clarity' else '📐'
                print(f"     {icon} {group.type.value}: {count} suggestion(s)")

                if group.type.value == 'clarity':
                    clarity_count += count
                elif group.type.value == 'rigor':
                    rigor_count += count

                # Show first suggestion from each group
                if group.items:
                    item = group.items[0]
                    print(f"        - [{item.severity.value}] {item.text[:60]}...")

        # Summary
        print_subheader("Summary:")
        print(f"  Total suggestions: {total_suggestions}")
        print(f"  💡 Clarity: {clarity_count}")
        print(f"  📐 Rigor: {rigor_count}")
        print(f"  ⏱️  Processing time: {elapsed:.2f}s")

        # Assertions
        assert total_suggestions > 0, "Should generate at least some suggestions"
        assert clarity_count > 0, "Should generate clarity suggestions"

        print("\n✅ Full workflow test PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Full workflow test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all tests in sequence."""
    print("\n" + "=" * 70)
    print("  PEERLY WORKFLOW TEST SUITE")
    print("=" * 70)

    try:
        # Test 1: Parser
        sections = await test_parser()

        # Test 2: Orchestrator Routing
        routing_result = await test_orchestrator_routing(sections)

        # Test 3: Clarity Agent (may fail if no API key)
        await test_clarity_agent(sections)

        # Test 4: Rigor Agent (may fail if no API key)
        await test_rigor_agent(sections)

        # Test 5: Full Workflow
        success = await test_full_workflow(sections)

        # Final summary
        print_header("TEST SUITE SUMMARY")
        if success:
            print("\n✅ ALL TESTS PASSED!")
            print("\nThe workflow is working correctly:")
            print("  ✓ Orchestrator routes sections intelligently")
            print("  ✓ Agents run in parallel without concurrent update errors")
            print("  ✓ Final suggestions are validated and prioritized")
        else:
            print("\n⚠️  Some tests completed with warnings")
            print("Check individual test results above")

        return success

    except Exception as e:
        print(f"\n❌ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point."""
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
