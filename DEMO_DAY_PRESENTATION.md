# Peerly - Demo Day Presentation Ideas

## 1. What is the Problem?

### The Pain Points (Personal Story)
- **The Late-Night Submission Panic**: As a PhD student, I've been there - 24 hours before a conference deadline, paper "done", but quality concerns keep you up
- **The Reviewer Roulette**: You never know what you'll get - sometimes insightful feedback, sometimes "this is unclear" with no specifics
- **The Clarity Paradox**: You've spent months on this research - of course it's clear to YOU. But to a fresh reader?
- **The Lonely Writer**: Most feedback comes AFTER submission. Co-authors are busy. Your advisor has 20 other students.

### Specific Problems
1. **No Real-time Feedback Loop**: Unlike code (which has linters, tests, CI/CD), academic writing has no immediate quality checks
2. **Inconsistent Quality**: First drafts often have:
   - Undefined jargon and assumptions
   - Weak experimental validation
   - Unclear methodology descriptions
   - Missing statistical rigor
3. **Time-Intensive Review Cycles**: Waiting days/weeks for advisor feedback, then major revisions
4. **High Stakes**: Rejected papers = delayed graduation, missed opportunities, wasted months
5. **Domain-Specific Nuance**: Generic grammar tools like Grammarly don't understand:
   - Mathematical rigor requirements
   - Experimental validation standards
   - CS/Math writing conventions
   - Statistical appropriateness

### The Cost
- **Personal**: Stress, imposter syndrome, delayed graduations
- **Academic**: Lower quality publications, desk rejections, multiple resubmissions
- **Financial**: Extended PhD timelines = lost earnings, additional tuition

---

## 2. Who Are the Users?

### Primary Users
1. **PhD Students & Early Career Researchers**
   - Writing first papers
   - Learning academic writing conventions
   - Limited access to frequent advisor feedback
   - High pressure to publish

2. **International Students**
   - English as second language
   - Understanding domain-specific writing norms
   - Cultural differences in academic writing

3. **Interdisciplinary Researchers**
   - Writing for audiences outside their primary field
   - Balancing rigor across multiple domains

### Secondary Users
4. **Advisors & Professors**
   - Want to provide better feedback faster
   - Managing multiple students
   - Ensuring consistent quality standards

5. **Research Teams**
   - Collaborative writing
   - Maintaining consistency across authors
   - Pre-submission quality checks

### Market Size (Rough Estimates)
- ~3M PhD students worldwide in STEM
- ~8M researchers globally
- Growing pressure to publish ("publish or perish")
- Conference deadlines create urgent demand

---

## 3. What Does Success Mean? What is the Solution?

### Success Metrics

**For Users:**
- **Time Saved**: Reduce feedback cycles from days → minutes
- **Quality Improvement**: Catch issues before submission
- **Confidence Boost**: Submit knowing your paper has been reviewed
- **Learning Tool**: Understand academic writing conventions

**Measurable Success:**
- Reduce desk rejections by 30%+
- Cut revision time by 50%
- Improve clarity scores (readability metrics)
- Increase first-submission acceptance rates

### The Solution: Peerly

**Core Value Proposition:**
"Grammarly for Academic Research Writing" - Real-time, AI-powered peer review that understands technical writing

**Key Features:**

1. **Multi-Agent Intelligence**
   - **Clarity Agent**: Finds unclear statements, undefined jargon, complex sentences
   - **Rigor Agent**: Validates experimental/mathematical rigor, statistical methods
   - **Orchestrator**: Prioritizes, validates, and synthesizes feedback

2. **Section-Aware Analysis**
   - Different standards for Introduction vs. Methodology
   - Context-aware suggestions
   - Structured feedback by paper section

3. **RAG-Powered Guidelines**
   - Learns from top-tier publications
   - Domain-specific writing standards
   - Best practices database

4. **Real-time, Interactive Feedback**
   - Split-view interface (write | review)
   - Color-coded severity (Info/Warning/Error)
   - Filterable by type and severity
   - Fast: 5-10 seconds for typical papers

**Why It Works:**
- Combines LLM reasoning with domain knowledge
- Catches both surface-level AND deep structural issues
- Available 24/7, never tired or busy
- Learns from academic writing best practices

---

## 4. Infrastructure Diagram & How It Works

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      USER INTERFACE                         │
│  ┌────────────────────┐      ┌──────────────────────────┐  │
│  │  LaTeX Editor      │      │  Suggestions Panel       │  │
│  │  (Write Paper)     │      │  (Review Feedback)       │  │
│  └────────────────────┘      └──────────────────────────┘  │
│              │                           │                  │
│              └───────────┬───────────────┘                  │
│                          │ React + Vite                     │
└──────────────────────────┼──────────────────────────────────┘
                           │ HTTP/WebSocket
┌──────────────────────────┼──────────────────────────────────┐
│                    FASTAPI BACKEND                          │
│  ┌────────────────────────────────────────────────────┐    │
│  │              API Routers                           │    │
│  │  /analyze (POST) | /health (GET) | WebSocket      │    │
│  └──────────────┬─────────────────────────────────────┘    │
│                 │                                           │
│  ┌──────────────┴──────────────────────────────────────┐   │
│  │         LangGraph Orchestration Layer              │   │
│  │                                                     │   │
│  │  ┌─────────────────────────────────────────────┐  │   │
│  │  │         StateGraph Workflow                 │  │   │
│  │  │                                             │  │   │
│  │  │   ┌──────────────┐    ┌─────────────────┐  │  │   │
│  │  │   │ Clarity Agent│    │  Rigor Agent    │  │  │   │
│  │  │   │              │    │                 │  │  │   │
│  │  │   │ - Jargon     │    │ - Experiments   │  │  │   │
│  │  │   │ - Clarity    │    │ - Math rigor    │  │  │   │
│  │  │   │ - Sentences  │    │ - Statistics    │  │  │   │
│  │  │   └──────┬───────┘    └────────┬────────┘  │  │   │
│  │  │          │                     │            │  │   │
│  │  │          └──────────┬──────────┘            │  │   │
│  │  │                     │                       │  │   │
│  │  │          ┌──────────▼──────────┐            │  │   │
│  │  │          │ Orchestrator Agent  │            │  │   │
│  │  │          │                     │            │  │   │
│  │  │          │ - Validation        │            │  │   │
│  │  │          │ - Prioritization    │            │  │   │
│  │  │          │ - Deduplication     │            │  │   │
│  │  │          └─────────────────────┘            │  │   │
│  │  └─────────────────────────────────────────────┘  │   │
│  └──────────────┬──────────────────────────────────┬─┘   │
│                 │                                  │     │
│      ┌──────────▼──────────┐         ┌───────────▼─────┐│
│      │   RAG Pipeline      │         │   OpenAI API    ││
│      │                     │         │   GPT-4/3.5     ││
│      │ - Embedding Model   │         └─────────────────┘│
│      │ - Query Processing  │                            │
│      └──────────┬──────────┘                            │
│                 │                                        │
└─────────────────┼────────────────────────────────────────┘
                  │
┌─────────────────▼────────────────────────────────────────┐
│              QDRANT VECTOR DATABASE                      │
│                                                           │
│  ┌────────────────────────────────────────────────────┐  │
│  │     Academic Writing Guidelines                    │  │
│  │     - Best practices                               │  │
│  │     - Top-tier paper examples                      │  │
│  │     - Domain-specific conventions                  │  │
│  │     - Statistical standards                        │  │
│  └────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────┘
```

### Workflow Explanation

1. **User Input**: Researcher writes LaTeX in split-view editor
2. **Analysis Request**: Frontend sends paper sections to FastAPI backend
3. **LangGraph Orchestration**:
   - Splits document into sections (Intro, Methods, Results, etc.)
   - Initializes StateGraph with Pydantic state management
   - Runs parallel agent analysis:
     - **Clarity Agent** → checks readability, jargon, sentence structure
     - **Rigor Agent** → validates experiments, math, statistics
4. **RAG Enhancement**: Agents query Qdrant for relevant guidelines
5. **Orchestrator Validation**: Final agent validates, prioritizes, deduplicates suggestions
6. **Response**: Structured feedback returned to frontend (5-10 sec)
7. **Display**: Color-coded, filterable suggestions shown alongside text

### Technical Highlights
- **Fast**: Optimized token usage, parallel agent processing
- **Scalable**: Async FastAPI + WebSockets for streaming
- **Extensible**: Easy to add new agents (Structure, Citations, etc.)
- **Smart**: RAG retrieval ensures domain-relevant feedback

---

## 5. Actual Live Demo

### Demo Script

**Setup:**
- Have a sample research paper ready (maybe your own paper excerpt?)
- Show both good and bad examples

**Demo Flow:**

1. **The Problem (30 sec)**
   - Show a paragraph with issues: "Here's a typical methodology section I wrote at 2am"
   - Point out: undefined terms, weak validation, unclear sentences

2. **Peerly in Action (2-3 min)**

   **Step 1: Paste and Analyze**
   - Paste the problematic paragraph into Peerly
   - Click "Analyze" → show the 5-10 second processing time

   **Step 2: Review Suggestions**
   - **Clarity Suggestions** (Info/Warning):
     - "Term 'XYZ' is not defined - reader may not understand"
     - "Sentence exceeds 30 words - consider splitting"
   - **Rigor Suggestions** (Warning/Error):
     - "No validation methodology described for experimental results"
     - "Statistical significance not reported for comparison"

   **Step 3: Filter and Focus**
   - Filter by severity (show only Errors)
   - Filter by type (show only Rigor issues)

   **Step 4: Apply Fixes**
   - Show the original vs. revised paragraph side-by-side
   - "This would have taken my advisor 2 days to review - Peerly did it in 7 seconds"

3. **Show Different Sections**
   - Paste an Introduction → different types of suggestions
   - Show how section-aware analysis works

**Pro Tips for Demo:**
- Use real examples from your PhD work
- Show personality: "This is literally from my first paper - reviewer 2 would have loved this"
- Have a backup screenshot in case of tech issues
- Time yourself beforehand

---

## 6. Business Opportunities & Market

### Business Model Options

**1. Freemium SaaS**
- **Free Tier**: 5 paper analyses/month, basic suggestions
- **Pro Tier** ($19/month): Unlimited analyses, advanced agents, priority support
- **Team Tier** ($49/user/month): Shared style guides, team collaboration
- **Institution Tier** (Custom): University-wide licenses

**2. Usage-Based Pricing**
- Pay per paper analysis
- Tiered pricing by paper length
- Good for occasional users

**3. Add-On Services**
- Premium domain-specific models (Medical, Physics, Economics)
- Custom RAG knowledge bases for research groups
- Integration with Overleaf, LaTeX editors
- API access for institutional tools

### Market Opportunity

**TAM (Total Addressable Market):**
- 3M+ PhD students globally × $200/year = $600M
- 8M+ researchers × $150/year = $1.2B
- **Combined TAM: ~$1.8B**

**SAM (Serviceable Available Market):**
- English-writing STEM researchers: ~30% of TAM = $540M
- Initial focus: CS, Math, Physics, Engineering

**SOM (Serviceable Obtainable Market - Year 1):**
- Target: 10,000 users × $100 avg = $1M ARR
- Realistic with university partnerships and PhD networks

### Competitive Landscape

**Direct Competitors:**
- Writefull: Academic writing assistant (less technical depth)
- Trinka AI: Grammar for academic writing (no rigor checking)
- Paperpal: AI writing assistant (generic feedback)

**Peerly's Differentiation:**
1. **Multi-agent intelligence** - not just grammar
2. **Domain-specific rigor** - understands CS/Math/Stats
3. **Section-aware analysis** - contextual feedback
4. **RAG-powered** - learns from best papers
5. **Built by researchers, for researchers**

**Indirect Competitors:**
- Grammarly (general writing)
- Human peer reviewers (slow, expensive)
- University writing centers (limited technical expertise)

### Go-to-Market Strategy

**Phase 1: MVP & Validation (Months 1-3)**
- Launch with beta users (your PhD network)
- Free tier to gather feedback
- Focus on CS/Math papers
- Iterate on agent quality

**Phase 2: Early Adopters (Months 4-6)**
- Target one university (maybe your institution?)
- Partnership with graduate writing programs
- Content marketing: blog posts on academic writing
- Student ambassador program

**Phase 3: Scale (Months 7-12)**
- Expand to 5-10 universities
- Launch paid tiers
- Add more domain agents (Physics, Bio, Econ)
- Integration with Overleaf

**Distribution Channels:**
- PhD student communities (Reddit, Discord, Twitter)
- Academic writing workshops
- University partnerships
- Conference sponsorships
- Advisor/professor referrals

### Key Metrics to Track

**Product:**
- Average suggestions per paper
- User acceptance rate of suggestions
- Time to analyze (keep < 10 sec)
- Agent accuracy (user feedback)

**Business:**
- User acquisition cost (CAC)
- Conversion rate (free → paid)
- Retention rate
- Net Promoter Score (NPS)
- Papers analyzed per user

---

## 7. Next Steps

### Technical Roadmap

**Short-term (1-3 months):**
- [ ] Add more domain-specific agents:
  - Citation quality agent
  - Structure/flow agent
  - Reproducibility agent
- [ ] Improve RAG knowledge base:
  - Scrape top-tier conference papers
  - Add domain-specific guidelines
  - Include reviewer feedback patterns
- [ ] Performance optimization:
  - Reduce analysis time to < 5 sec
  - Add caching for repeated analyses
  - Implement streaming responses
- [ ] User experience:
  - One-click fixes for simple suggestions
  - Explanation for each suggestion
  - Progress tracking for multi-section papers

**Medium-term (3-6 months):**
- [ ] Integrations:
  - Overleaf plugin
  - VS Code extension for LaTeX
  - Google Docs add-on
- [ ] Collaboration features:
  - Team workspaces
  - Shared style guides
  - Comments and discussions
- [ ] Advanced features:
  - Version comparison
  - Plagiarism detection
  - Reference management
  - Figure/table quality checks

**Long-term (6-12 months):**
- [ ] Multi-language support (expand beyond English)
- [ ] More domains (Biology, Economics, Social Sciences)
- [ ] API for institutional tools
- [ ] Mobile app for on-the-go reviews
- [ ] AI-powered writing suggestions (not just critique)

### Business Next Steps

**Immediate (Post-Demo Day):**
1. **Validate with real users**:
   - Get 50 beta users from PhD network
   - Conduct user interviews
   - Measure key metrics
2. **Build waiting list**:
   - Create landing page
   - Email capture
   - Early access program
3. **Partnerships**:
   - Reach out to 3 university writing centers
   - Connect with academic writing instructors
   - Explore Overleaf integration

**Near-term (1-3 months):**
1. **Pricing experiments**:
   - Test different price points
   - A/B test free vs. paid features
   - Gather willingness-to-pay data
2. **Content marketing**:
   - Blog: "10 mistakes in academic writing"
   - YouTube: Demo videos
   - Twitter: Tips and tricks
3. **Fundraising prep** (if desired):
   - Pitch deck refinement
   - Financial projections
   - Competitive analysis

### Potential Pivots/Extensions

**Adjacent Opportunities:**
- **Grant writing assistant**: Same tech, different domain
- **Technical documentation reviewer**: For engineering teams
- **Patent writing assistant**: High-value, specialized market
- **Scientific journalism**: Help writers understand research

### Success Definition (12 months out)

**Product:**
- 10,000+ active users
- 4.5+ star average rating
- < 5 sec average analysis time
- 85%+ suggestion acceptance rate

**Business:**
- $500K ARR
- 1000 paying customers
- 5 university partnerships
- Break-even or path to profitability

**Impact:**
- Help 100+ students submit better papers
- Reduce rejection rates by 25%
- Save collective 10,000+ hours of revision time

---

## Problem Framing (For Presentation)

**Opening - The Real Challenges of Technical Writing:**

"Writing a technical research paper is fundamentally difficult. Here's why:

**Challenge 1: Clarity vs. Precision**
- Too much jargon → 'unclear to broader audience'
- Too simple → 'lacks technical rigor'
- You're too close to your work to know which is which

**Challenge 2: Demonstrating Rigor**
- Is your experimental setup validated?
- Are statistical tests appropriate?
- Are assumptions clearly stated?
- Is methodology reproducible?
Miss one → desk rejection. But there's no checklist. No quality gate until peer review.

**Challenge 3: No Real-Time Feedback**
Unlike software development:
- Code → immediate feedback (compiler, tests, linters)
- Research paper → write for weeks → submit → wait 3 months → find out what was wrong

**Challenge 4: Domain-Specific Standards**
- Math papers: proof rigor, theorem clarity
- CS papers: experimental validation, ablation studies
- Statistics: appropriate tests, confidence intervals
Generic tools don't know these standards."

**The Gap:**
"Researchers need real-time, domain-aware feedback while writing. Current options:
- Grammarly: catches grammar, not rigor
- Advisor review: slow, infrequent, high-level
- Writing centers: no technical depth
- Co-authors: too busy

Result: Researchers write blind. Problems discovered months later through rejection. Cycle repeats."

**The Solution:**
"What if there was a linter for research papers? Real-time feedback that understands both clarity AND rigor. Knows domain standards. Available 24/7 while you write. That's Peerly."

**The Vision:**
"Bring software engineering's quality gates to academic writing. Catch issues during writing, not after submission. Make feedback immediate, not a 3-month wait."

**Call to Action:**
- "Try Peerly at [demo link]"
- "Join the beta waiting list"
- "Get real-time peer review while you write"

---

## Slide Deck Outline

1. **Title Slide**: Peerly - AI Peer Review for Research Papers
2. **The Problem - Technical Writing Challenges** (4 key challenges with builds)
3. **Who We Serve** (PhD students, researchers, market size)
4. **What Does Success Look Like?** (Metrics, outcomes)
5. **The Solution** (Multi-agent AI review, key features)
6. **How It Works** (Architecture diagram)
7. **Live Demo** (Show it working!)
8. **Market Opportunity** ($1.8B TAM, competitive landscape)
9. **Business Model** (Freemium SaaS, GTM strategy)
10. **Traction & Next Steps** (Beta users, roadmap)
11. **Vision & Thank You** (Quality gates for academic writing)

---

## Additional Notes

### What Makes This Personal
- Use YOUR papers as examples
- Share YOUR rejection stories
- Talk about YOUR advisor's feedback patterns
- Show before/after from YOUR writing

### Authenticity Wins
- Don't oversell - acknowledge limitations
- Share what you learned building this
- Be honest about challenges ahead
- Show genuine passion for solving this problem

### Remember
You're not just pitching a product. You're sharing a solution to a problem you've personally lived. That authenticity is your competitive advantage.

Good luck with the demo! 🚀
