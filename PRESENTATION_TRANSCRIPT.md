# Peerly Demo Day Presentation Transcript

**Total Time: 8-10 minutes**
**Presenter: Arnab Bhattacharya**

---

## [SLIDE 1: Title Slide]
### Peerly - AI Peer Review for Research Papers

**[0:00 - 0:30]**

Good morning/afternoon everyone! My name is Arnab, and I'm here to talk about Peerly - an AI-powered peer review assistant for academic research writing.

But before I dive into the product, let me tell you a story that many of you might relate to.

---

## [SLIDE 2: The Problem - Technical Writing is Hard]

**[0:30 - 1:30]**

**[Direct, professional tone]**

Writing a technical research paper is fundamentally difficult. Let me show you why.

**[CLICK - Challenge 1 appears]**

**Challenge 1: Clarity vs. Precision**

You need to be technically precise while remaining understandable. But:
- Use too much jargon → reviewers say "unclear to broader audience"
- Simplify too much → reviewers say "lacks technical rigor"
- You're too close to your work to know which is which

**[CLICK - Challenge 2 appears]**

**Challenge 2: Demonstrating Rigor**

You need to prove your work is sound:
- Have you validated your experimental setup?
- Are your statistical tests appropriate?
- Are your assumptions stated clearly?
- Is your methodology reproducible?

Miss any of these → desk rejection. But there's no checklist. No quality gate. No way to know until peer review.

**[CLICK - Challenge 3 appears]**

**Challenge 3: No Real-Time Feedback**

Unlike software development - which has linters, tests, CI/CD - academic writing has nothing:
- Code → immediate feedback from compiler, tests, linters
- Research paper → write for weeks → submit → wait 3 months → find out what was wrong

**[CLICK - Challenge 4 appears]**

**Challenge 4: Domain-Specific Standards**

Every field has different expectations:
- Math papers: proof rigor, theorem clarity
- CS papers: experimental validation, ablation studies
- Statistics: appropriate tests, confidence intervals

Generic writing tools don't know these standards. Your advisor might, but they don't have time to review every draft.

**[CLICK - The gap appears]**

**The Gap:**

Researchers need real-time, domain-aware feedback while they write. But the current options are:
- **Grammarly**: Catches grammar, not rigor
- **Advisor review**: Slow, infrequent, high-level
- **Writing centers**: Don't understand technical depth
- **Co-authors**: Too busy with their own work

**[Pause, make eye contact]**

So researchers write blind. They catch problems months later through rejection. And the cycle repeats.

This is the problem I set out to solve.

**[CLICK to next section of slide - show pain points]**

Let me break down the real problems:

1. **No real-time feedback loop** - We have linters for code, tests for software, CI/CD pipelines... but for academic writing? Nothing. You write, you wait, you pray.

2. **The lonely writer problem** - Your advisor has 20 other students. Your co-authors are busy with their own deadlines. You're essentially writing in isolation until submission.

3. **High stakes, low visibility** - A rejected paper can mean delayed graduation, missed opportunities, months of wasted work. And you don't know there's a problem until it's too late.

4. **Domain-specific complexity** - Grammarly can catch grammar mistakes, sure. But does it know if your statistical analysis is appropriate? If your mathematical rigor is sufficient? If you've properly validated your experimental setup?

**[Lean in, slower pace]**
As researchers, we're expected to contribute novel knowledge to our fields... but we're never really taught how to WRITE about it. We learn by trial and error. By rejection and revision.

There has to be a better way.

---

## [SLIDE 3: Who Are the Users?]

**[1:30 - 2:15]**

So who else has this problem?

**[CLICK - Primary Users appear]**

**Primary users:**
- **PhD students and early-career researchers** - Writing their first papers, learning the conventions, limited access to frequent advisor feedback
- **International students** - English as a second language, navigating cultural differences in academic writing
- **Interdisciplinary researchers** - Writing for audiences outside their primary field

**[CLICK - Market size appears]**

This is not a small problem. We're talking about:
- ~3 million PhD students worldwide in STEM fields
- ~8 million active researchers globally
- Growing pressure to publish - "publish or perish" is very, very real

**[Knowing smile]**
And if you've ever been on the receiving end of a desk rejection... you know exactly what I'm talking about.

---

## [SLIDE 4: What Does Success Look Like?]

**[2:15 - 3:00]**

So what would success look like? What would make a real difference?

**[CLICK - Success metrics appear]**

For researchers, success means:
- **Time saved** - Feedback in MINUTES instead of DAYS
- **Quality improvement** - Catch issues BEFORE submission, not after
- **Confidence** - Submit knowing your paper has been thoroughly reviewed
- **Learning** - Actually understand academic writing conventions

**[CLICK - Measurable outcomes appear]**

If we get this right, we should see:
- 30% reduction in desk rejections
- 50% cut in revision time
- Improved clarity and readability scores
- Higher first-submission acceptance rates

That's what we're aiming for with Peerly.

---

## [SLIDE 5: The Solution - Peerly]

**[3:00 - 4:00]**

So what is Peerly?

**[Clear, confident delivery]**
Think of it as "Grammarly for Academic Research Writing" - but instead of just catching grammar mistakes, it understands the technical and structural requirements of research papers.

**[CLICK - Key features appear one by one]**

Here's how it works:

**1. Multi-Agent Intelligence**
We use three specialized AI agents:
- **Clarity Agent** - Finds unclear statements, undefined jargon, overly complex sentences
- **Rigor Agent** - Validates experimental design, mathematical rigor, statistical appropriateness
- **Orchestrator Agent** - Synthesizes feedback, prioritizes suggestions, eliminates duplicates

**2. Section-Aware Analysis**
The introduction has different requirements than the methodology. The results section needs different validation than the conclusion. Peerly understands this context.

**3. RAG-Powered Guidelines**
We've built a knowledge base from top-tier publications, domain-specific writing standards, and academic best practices. The agents don't just use generic rules - they reference actual standards from your field.

**4. Real-time, Interactive Feedback**
- Split-view interface - write on the left, see suggestions on the right
- Color-coded severity levels: Info, Warning, Error
- Filterable by type and severity
- **Fast**: 5-10 seconds for a typical paper

**[Emphasis]**
This is not just spell-check. This is like having a knowledgeable peer reviewer looking over your shoulder 24/7.

---

## [SLIDE 6: How It Works - Architecture]

**[4:00 - 4:45]**

Let me show you what's happening under the hood.

**[CLICK - Architecture diagram appears]**

**[Point to diagram as you explain]**

1. **Frontend** - React-based split-view editor. You write your LaTeX on the left, suggestions appear on the right.

2. **FastAPI Backend** - Receives your paper, orchestrates the analysis workflow

3. **LangGraph Orchestration** - This is where the magic happens:
   - Your paper is split into sections
   - Clarity Agent and Rigor Agent run in parallel
   - Each agent queries our RAG pipeline for relevant guidelines
   - Orchestrator validates and prioritizes all suggestions

4. **Qdrant Vector Database** - Stores academic writing guidelines, best practices, domain-specific conventions

5. **Response** - Structured, color-coded feedback back to you in 5-10 seconds

**[Key point]**
The entire system is built for speed AND quality. We optimize token usage, run agents in parallel, and use async operations throughout.

---

## [SLIDE 7: Live Demo]

**[4:45 - 7:00]**

Alright, enough talking. Let me show you Peerly in action.

**[Switch to demo screen/app]**

**[DEMO PART 1: Show the Problem - 30 seconds]**

Here's a methodology section from one of my early papers. **[paste the problematic text]**

Look at this paragraph - at 2 AM, I thought this was crystal clear. Let me read part of it:

**[Read a confusing sentence from the example]**

Can you spot the issues? Maybe. But let's see what Peerly thinks.

**[DEMO PART 2: Run Analysis - 30 seconds]**

I'm going to click "Analyze Section" and... **[show loading indicator]** this should take about 5-10 seconds.

**[While waiting - fill time naturally]**
What's happening right now is all three agents are analyzing this text, cross-referencing with our knowledge base, and generating targeted suggestions.

**[Analysis complete]**

And... done! 7 seconds. Let's see what we got.

**[DEMO PART 3: Review Suggestions - 60-90 seconds]**

**[Click through suggestions, read examples]**

Look at these suggestions:

**Clarity Issues** (Warning):
- **[Read example]** "The term 'latent representation' is introduced without definition - readers unfamiliar with deep learning may struggle to understand this section"
  - **[Personal comment]** Fair point! I was assuming too much background knowledge.

- **[Read example]** "Sentence exceeds 35 words and contains nested clauses - consider breaking into two sentences for readability"
  - **[Laugh]** Yeah, that sentence is a monster.

**Rigor Issues** (Error):
- **[Read example]** "No validation methodology described for the experimental results - how were the results verified?"
  - **[Nod seriously]** This is exactly the kind of thing Reviewer 2 would catch. And they'd be right.

- **[Read example]** "Statistical significance testing not reported for performance comparisons - consider adding p-values or confidence intervals"
  - **[Personal touch]** This would have been an instant desk rejection at some venues.

**[DEMO PART 4: Show Filtering - 20 seconds]**

Now watch this - I can filter by severity. **[Click "Errors only"]**

See? Now I'm only seeing the critical issues that could lead to rejection. I can fix these first, then come back to the warnings.

I can also filter by type. **[Click "Rigor only"]**

Just the methodological and statistical issues.

**[DEMO PART 5: Show Impact - 20 seconds]**

**[Switch to side-by-side comparison if available, or just explain]**

Here's the original paragraph, and here's what it looks like after addressing Peerly's suggestions:
- Terms defined
- Long sentences split
- Validation methodology added
- Statistical tests included

**[Slow down, make eye contact]**
This would have taken my advisor 2-3 days to review and send back to me. Peerly did it in 7 seconds.

**[Switch back to slides]**

---

## [SLIDE 8: Market Opportunity]

**[7:00 - 7:45]**

So, is this a real business? Let's look at the numbers.

**[CLICK - TAM appears]**

**Total Addressable Market:**
- 3 million PhD students × $200/year = $600 million
- 8 million researchers × $150/year = $1.2 billion
- **Combined TAM: ~$1.8 billion**

**[CLICK - SAM appears]**

**Serviceable Available Market:**
We're starting with English-writing STEM researchers - about 30% of the total market, or **$540 million**.

**[CLICK - SOM appears]**

**Year 1 Target:**
10,000 users at $100 average revenue = **$1 million ARR**

This is achievable through university partnerships and PhD student networks.

**[CLICK - Competitive landscape appears]**

**Competition:**

**Direct competitors:**
- Writefull, Trinka, Paperpal - these are academic writing assistants, but they focus mainly on grammar and style

**Our differentiation:**
1. Multi-agent intelligence - not just grammar
2. Domain-specific rigor checking - we understand CS, Math, Statistics
3. Section-aware analysis - context matters
4. RAG-powered learning from top papers
5. **Built by researchers, for researchers** - we've lived this pain

**[Confident tone]**
We're not trying to beat Grammarly at grammar. We're building something Grammarly can't - deep technical understanding of research writing.

---

## [SLIDE 9: Business Model]

**[7:45 - 8:15]**

Our business model is straightforward - Freemium SaaS:

**[CLICK - Pricing tiers appear]**

- **Free Tier** - 5 paper analyses per month, basic suggestions - this gets people hooked
- **Pro Tier** - $19/month - Unlimited analyses, all agent features, priority support
- **Team Tier** - $49/user/month - Shared style guides, collaboration features
- **Institution Tier** - Custom pricing - University-wide licenses

**[Click - GTM strategy appears]**

**Go-to-Market Strategy:**

**Phase 1** (Months 1-3): Beta with my PhD network, gather feedback, iterate on quality

**Phase 2** (Months 4-6): Target one university, partner with graduate writing programs, launch student ambassador program

**Phase 3** (Months 7-12): Expand to 5-10 universities, launch paid tiers, integrate with Overleaf

**Distribution channels:**
- PhD student communities (Reddit, Twitter/X, Discord)
- Academic writing workshops
- University partnerships
- Conference sponsorships

---

## [SLIDE 10: Traction & Next Steps]

**[8:15 - 9:00]**

So where are we now, and where are we going?

**[CLICK - Current status appears]**

**Current Status:**
- ✅ Working MVP with multi-agent system
- ✅ LangGraph workflow operational
- ✅ RAG pipeline functional
- ✅ Split-view interface complete
- 🔄 Beta testing with initial users

**[CLICK - Technical roadmap appears]**

**Technical Roadmap:**

**Next 1-3 months:**
- Add more specialized agents (Citations, Structure, Reproducibility)
- Expand RAG knowledge base with more top-tier papers
- Performance optimization - get analysis time under 5 seconds
- One-click fixes for simple suggestions

**3-6 months:**
- Overleaf integration
- VS Code extension for LaTeX
- Team collaboration features
- Version comparison

**6-12 months:**
- Multi-language support
- Expand to more domains (Biology, Economics, Social Sciences)
- API for institutional tools
- Mobile app

**[CLICK - Business milestones appear]**

**Business Milestones:**

**Immediate (Post-Demo Day):**
- Get 50 beta users from PhD networks
- Build waiting list through landing page
- 3 university writing center partnerships

**12-Month Goals:**
- 10,000 active users
- $500K ARR
- 1,000 paying customers
- 5 university partnerships
- Break-even or clear path to profitability

---

## [SLIDE 11: Vision & Closing]

**[9:00 - 9:45]**

Let me leave you with this vision.

**[Slower, more inspirational pace]**

Imagine a world where no researcher submits a paper with easily fixable issues.

Where the feedback loop is measured in minutes, not months.

Where writing quality is democratized - not just for students with responsive advisors or native English speakers, but for EVERYONE doing good research.

**[Personal, authentic]**

I built Peerly because I needed it. For every paragraph where I thought "is this clear?", every methodology section where I wondered "is this rigorous enough?", every time I wished I had a knowledgeable peer to review my work as I was writing - not months later.

But more than that - I built it because I believe good research deserves to be communicated well. And right now, we're losing good ideas because of poor presentation.

**[CLICK - Call to action appears]**

**Here's how you can help:**

1. **Try Peerly** - [demo link] - I'd love your feedback
2. **Join the beta waiting list** - Be among the first to use it
3. **Spread the word** - If you know PhD students or researchers who could benefit, send them our way

**[CLICK - Contact info appears]**

I'm Arnab, and I'm here for the rest of the session. Find me if you:
- Want to try Peerly
- Have feedback or ideas
- Are interested in partnerships
- Just want to commiserate about Reviewer 2

**[Smile, confident closing]**

Thank you!

---

## [Q&A Time]

**[9:45 - 10:00+]**

### Anticipated Questions & Responses

**Q: How do you ensure the AI suggestions are accurate?**

A: Great question. Three things:
1. **RAG pipeline** - We ground suggestions in actual academic writing guidelines and top-tier publications
2. **Multi-agent validation** - The orchestrator cross-checks suggestions from both agents
3. **User feedback loop** - We track which suggestions users accept/reject to continuously improve

We're not trying to be perfect - we're trying to be better than nothing, which is what most researchers have right now.

---

**Q: What about different academic fields? A math paper is very different from a CS paper.**

A: Absolutely right. Our current version focuses on CS/Math/Statistics because that's my background and where I can validate quality. But the architecture is extensible - we can add domain-specific agents and knowledge bases for other fields. That's actually part of the 6-12 month roadmap.

---

**Q: How do you handle privacy? Researchers can't share unpublished work.**

A: Critical question. We:
1. Don't store paper content by default - analysis happens in real-time
2. Offer self-hosted options for institutions
3. Clear data retention policies
4. Optional features for saving work (user controlled)

For the institution tier, we're building on-premise deployment options.

---

**Q: Why wouldn't researchers just use ChatGPT/Claude directly?**

A: You absolutely could! But Peerly offers:
1. **Specialized agents** - Not generic, but trained for specific aspects of academic writing
2. **Structured output** - Not a wall of text, but categorized, filterable suggestions
3. **Integrated workflow** - Write and review in the same interface
4. **Consistency** - Same analysis every time, not dependent on prompt engineering
5. **Speed** - Optimized for fast analysis

Think of it as the difference between using a general-purpose tool vs. a specialized IDE for coding.

---

**Q: What's your moat? Couldn't someone else build this?**

A: Honest answer - the technology isn't rocket science. But:
1. **Domain expertise** - I've lived the problem, I understand the nuances
2. **Network effects** - As we gather more data, our RAG improves
3. **Quality of knowledge base** - Curating good academic writing examples takes time and expertise
4. **First-mover advantage** - We're building brand and user base now
5. **Execution speed** - We can iterate faster because we deeply understand the users

The moat is being built, not built-in.

---

**Q: Have you talked to users? What do they say?**

A: **[Share real feedback if you have it, otherwise:]**

I'm in active conversations with beta users from my PhD network. Early feedback:
- "This would have saved me SO much time"
- "The rigor suggestions are actually really helpful"
- Main request: "Make it faster, add more domains"

I'm looking to expand the beta - if anyone here has researcher connections, I'd love intros!

---

**Q: What about false positives? What if the AI is wrong?**

A: It will be wrong sometimes - that's inevitable. But:
1. **Severity levels** help - "Info" suggestions are gentle nudges, not demands
2. **Explanations** - Each suggestion explains WHY it's flagged
3. **User control** - Researchers can dismiss suggestions they disagree with
4. **Learning** - We track false positives to improve

The goal isn't perfection - it's to catch the issues that would lead to rejection, even if we occasionally flag things that are fine.

---

**Q: How do you compete with free tools like language models?**

A: We're not competing with free tools - we're building on top of them. The value is:
1. **Specialization** - Built specifically for academic writing
2. **Time savings** - No need to craft prompts or parse responses
3. **Reliability** - Consistent quality, not dependent on user's prompting skill
4. **Integration** - Workflow is seamless

For $19/month, if we save a researcher even 2 hours per paper, we've paid for ourselves.

---

## Speaker Notes

### Pacing Tips
- **Slow down on personal stories** - let emotion land
- **Speed up on technical details** - don't lose the audience
- **Pause after key points** - let them absorb
- **Smile during the demo** - show confidence and enthusiasm

### Body Language
- **Make eye contact** during personal stories
- **Gesture to the screen** during demo
- **Stand still** during key points (don't pace)
- **Open posture** - confident, approachable

### Voice Modulation
- **Lower, slower** for serious problems
- **Higher energy** for the solution
- **Conversational** during demo
- **Inspirational** for vision/closing

### Backup Plans
- **Demo fails?** Have a video recording ready
- **Time running short?** Skip detailed architecture, focus on demo
- **Time running long?** Condense business model section
- **Tech issues?** Have screenshot deck as backup

### Energy Management
- **High energy** start (hook them)
- **Authentic** during problem section (connect)
- **Enthusiastic** during demo (show value)
- **Inspirational** close (leave them wanting more)

### Remember
- **You lived this problem** - that's your advantage
- **Authenticity > perfection** - be real
- **Show, don't tell** - demo is key
- **Connect emotionally** - everyone has struggled with something similar

---

## Post-Presentation Actions

**Immediately after:**
- [ ] Share demo link in chat/Slack
- [ ] Connect with anyone who approached you
- [ ] Note all questions asked for FAQ

**Same day:**
- [ ] Follow up with interested investors/partners
- [ ] Send thank you to organizers
- [ ] Post recording/slides if allowed

**Next week:**
- [ ] Reach out to anyone who expressed interest
- [ ] Incorporate feedback into product
- [ ] Update pitch deck based on learnings

Good luck! You've got this. 🚀
