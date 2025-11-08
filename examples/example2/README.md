# Example 2: Quantum Computing Paper

A LaTeX document with more mathematical content to showcase Peerly's review of formal proofs and theoretical claims.

## About This Example

**Topic**: Quantum Algorithms for Graph Problems

**Complexity**: Medium (includes theorems, lemmas, proofs)

**Dependencies**: Standard packages (amsmath, amssymb, amsthm)

**Purpose**: Demonstrates Peerly's ability to review:
- Mathematical rigor and proofs
- Theoretical claims
- Complexity analysis
- Formal definitions

## Expected AI Suggestions

### Clarity Agent will flag:
- "The algorithms are fast and efficient" - vague quantification
- "The approach leverages quantum mechanics" - needs explanation
- "problems that are hard classically" - undefined complexity class
- Missing explanation of quantum walk operator
- Undefined notation usage

### Rigor Agent will flag:
- **Theorem 1**: No proof provided!
- **Lemma 1**: Proof is missing
- "The proof relies on amplitude amplification" - but no actual proof given
- Missing experimental setup details
- "average time 31.4 units" - units not defined
- Claimed speedup not rigorously proven
- Missing statistical analysis of experimental results
- Assumptions not explicitly stated

## How to Use

1. **Start Peerly**: `./start.sh`
2. **Open frontend**: http://localhost:5173
3. **Copy content** from `quantum_computing.tex`
4. **Paste into editor** and click "Get AI Suggestions"

## What Makes This Example Different

This example focuses more on **mathematical rigor**:
- Formal theorems and lemmas
- Complexity analysis
- Mathematical notation
- Theoretical claims

Perfect for testing Peerly's ability to identify:
- Missing proofs
- Unsupported mathematical claims
- Incomplete complexity arguments
- Undefined mathematical notation

## Common Issues Highlighted

1. **Missing proofs**: Theorem and Lemma stated without proofs
2. **Vague complexity**: "Fast and efficient" without Big-O notation
3. **Undefined terms**: "Hard classically" (NP-hard? PSPACE-hard?)
4. **Experimental gaps**: Units not defined, no error bars, no statistical tests
5. **Assumptions**: Ideal quantum gates assumed but not stated upfront

## Try Improving

**Before**: "Our quantum algorithm finds the shortest path in time $O(\sqrt{n} \log n)$."
**After**: Add a complete proof sketch with detailed steps

**Before**: "average time 31.4 units"
**After**: "average time 31.4 ± 2.1 milliseconds (95% confidence interval, n=100 trials)"
