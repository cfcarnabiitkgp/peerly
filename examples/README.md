# Peerly Example Papers

This directory contains example LaTeX documents for demonstrating Peerly's AI review capabilities.

## Available Examples

### Example 1: Climate Prediction (Simple)
**File**: `example1/climate_prediction.tex`

**Topic**: Machine Learning for Climate Prediction

**Best for**:
- First-time users
- Understanding basic clarity and rigor issues
- Learning how Peerly works

**Key Features**:
- Simple structure
- Common writing issues
- Vague claims and undefined terms
- Missing experimental details

**Expected suggestions**: 15-25 suggestions

---

### Example 2: Quantum Computing (Medium)
**File**: `example2/quantum_computing.tex`

**Topic**: Quantum Algorithms for Graph Problems

**Best for**:
- Mathematical papers
- Theoretical computer science
- Testing proof validation

**Key Features**:
- Formal theorems and lemmas
- Missing proofs
- Complexity analysis
- Mathematical notation

**Expected suggestions**: 20-30 suggestions

---

## How to Use These Examples

### Method 1: Copy & Paste (Easiest)

1. Start Peerly:
   ```bash
   cd /Users/arnabbhattacharya/Desktop/Peerly-Demo
   ./start.sh
   ```

2. Open http://localhost:5173

3. Copy the content from any `.tex` file

4. Paste into the LaTeX editor (left panel)

5. Click "🔄 Get AI Suggestions" (right panel)

6. Wait 5-10 seconds for analysis

7. Review suggestions by section

### Method 2: Upload File

1. Start Peerly (as above)

2. In the file manager (left panel), click "📁 + Upload Files"

3. Select a `.tex` file from the examples folder

4. Click on the uploaded file to load it into the editor

5. Click "🔄 Get AI Suggestions"

### Method 3: Direct File Access

You can also view and edit the files directly in your favorite editor, then copy the content to Peerly.

## Understanding the Suggestions

### Suggestion Types

- **💡 Clarity**: Readability, unclear statements, missing definitions
- **📐 Rigor**: Mathematical correctness, experimental validity, missing proofs
- **⚖️ Ethics**: (Future) Research ethics, data privacy, fairness

### Severity Levels

- **🔴 Error**: Critical issues that must be fixed
- **🟡 Warning**: Important issues that should be addressed
- **🔵 Info**: Suggestions for improvement

## What to Look For

### In Example 1 (Climate Prediction):

**Clarity Issues**:
- "important problem" → too vague
- "good results" → needs quantification
- "special architecture" → undefined
- "works well" → subjective

**Rigor Issues**:
- No statistical significance tests
- Baseline comparisons lack detail
- Missing dataset descriptions
- Experimental setup incomplete
- Claims without evidence

### In Example 2 (Quantum Computing):

**Clarity Issues**:
- "fast and efficient" → needs Big-O notation
- Quantum walk operator not explained
- "hard classically" → complexity class undefined

**Rigor Issues**:
- **Theorem stated without proof**
- **Lemma without proof**
- Complexity analysis incomplete
- Experimental results lack statistical rigor
- Assumptions not explicitly stated

## Tips for Testing

1. **Start Simple**: Try Example 1 first to understand the interface

2. **Compare Sections**: Notice how suggestions differ between Introduction, Methodology, and Results

3. **Check Severity**: See how different issues get different severity levels

4. **Iterate**: Make improvements based on suggestions, then re-run to see if issues are resolved

5. **Explore Filters**: Use the suggestion type badges to filter by Clarity or Rigor

## Creating Your Own Examples

Want to add more examples? Here's the structure:

```
examples/
├── example3/
│   ├── your_paper.tex
│   └── README.md
```

Guidelines for good examples:
- Use only standard LaTeX packages (amsmath, amssymb, amsthm)
- Include various section types (intro, methods, results, discussion)
- Add deliberate issues for Peerly to catch
- Document expected suggestions in README

## Troubleshooting

### "No suggestions yet"
- Make sure the LaTeX content is substantial (>100 lines)
- Check that the backend is running (`curl http://localhost:8000/api/health`)
- Wait the full 5-10 seconds for processing

### "Failed to connect to backend"
- Ensure services are running: `./start.sh`
- Check logs: `cat logs/peerly-backend.log`
- Verify `.env` has `OPENAI_API_KEY` set

### Compilation errors
- These examples don't require external packages
- If PDF compilation fails, you may need to install Tectonic
- PDF compilation is separate from AI suggestions

## Next Steps

After trying these examples:
1. ✅ Upload your own research paper
2. ✅ Make iterative improvements based on suggestions
3. ✅ Explore the API at http://localhost:8000/docs
4. ✅ Read the full documentation in the main README.md

## Contributing Examples

Have a great example paper? Consider adding it:
1. Create a new `exampleN/` directory
2. Add your `.tex` file
3. Document expected suggestions in README.md
4. Make sure it uses only standard packages

Happy writing! 📝