# Example 1: Climate Prediction Paper

A simple LaTeX document demonstrating Peerly's AI review capabilities.

## About This Example

**Topic**: Machine Learning for Climate Prediction

**Complexity**: Simple

**Dependencies**: Only standard packages (amsmath, amssymb)

**Purpose**: Demonstrates common issues that Peerly's agents can detect:
- **Clarity issues**: Vague statements, undefined terms, missing context
- **Rigor issues**: Unproven claims, missing experimental details, incomplete methodology

## Expected AI Suggestions

When you review this paper with Peerly, you should get suggestions like:

### Clarity Agent will flag:
- "Climate change is an important problem" - too vague
- "good results" - needs quantification
- "Our approach is different" - needs explanation of how it's different
- "special architecture" - undefined term
- Missing definitions for technical terms

### Rigor Agent will flag:
- "achieves good results" - needs specific metrics
- Missing proof for mathematical claims
- "The improvement is significant" - needs statistical test
- Unverified claim about outperforming baselines
- Missing experimental setup details
- No discussion of statistical significance
- Missing reproducibility information

## How to Use

1. **Start Peerly**:
   ```bash
   cd /Users/arnabbhattacharya/Desktop/Peerly-Demo
   ./start.sh
   ```

2. **Open the frontend**: http://localhost:5173

3. **Load the example**:
   - Copy the content from `climate_prediction.tex`
   - Paste it into the LaTeX editor (left panel)

4. **Get AI suggestions**:
   - Click "🔄 Get AI Suggestions" in the right panel
   - Wait 5-10 seconds for analysis
   - Review suggestions by section

5. **Compile PDF** (optional):
   - Click "Compile to PDF" to see the rendered document
   - View in the middle preview panel

## What to Expect

**Processing time**: ~5-10 seconds

**Number of suggestions**: ~15-25 suggestions across both agents

**Severity distribution**:
- Errors: Issues that must be fixed (missing definitions, unproven claims)
- Warnings: Issues that should be addressed (vague statements, unclear explanations)
- Info: Suggestions for improvement (additional context, better phrasing)

## Learning Points

This example demonstrates:
1. ✅ Section-wise analysis (Introduction, Methodology, Results, etc.)
2. ✅ Multiple agent types (Clarity + Rigor)
3. ✅ Severity levels (Error, Warning, Info)
4. ✅ Mathematical notation review
5. ✅ Experimental validation critique
6. ✅ Related work analysis

## Common Issues Highlighted

1. **Vague claims**: "good results", "works well", "significant improvement"
2. **Undefined terms**: "special architecture", "novel approach"
3. **Missing rigor**: No statistical tests, incomplete methodology
4. **Incomplete experiments**: Missing baselines, datasets not described
5. **Mathematical gaps**: Equations without explanation or derivation

## Try Making Improvements

After getting suggestions, try fixing some issues:

**Before**: "Our method achieves good results"
**After**: "Our method achieves MSE of 2.3, a 51% improvement over the baseline (MSE = 4.7)"

**Before**: "The results show that our method works well"
**After**: "Statistical analysis using paired t-test shows our method significantly outperforms baselines (p < 0.01)"

Then request AI suggestions again to see if the issues are resolved!
