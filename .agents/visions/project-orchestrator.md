# Project Manager - Vision Document

## What It Is

An AI-powered project management agent that helps non-technical people build complete software projects by translating natural language conversations into structured development workflows. Think of it as a friendly project manager that sits between you and technical AI coding assistants, handling all the complex command syntax and workflow management.

## Who It's For

**Primary Users:**
- Non-coders who have great product ideas but can't code
- Product managers who want to prototype quickly
- Entrepreneurs validating MVP concepts
- Designers who want to build their visions
- Anyone intimidated by technical development workflows

**Secondary Users:**
- Developers who want to automate repetitive project setup
- Teams wanting standardized project workflows
- Technical mentors helping non-technical founders

## The Problem

Building software today requires understanding complex workflows:
- Remembering specific command syntax (`/command-invoke plan-feature-github`)
- Knowing when to plan vs. execute vs. commit vs. merge
- Understanding technical jargon (PRD, CI/CD, feature branches)
- Managing state across multiple phases
- Coordinating between GitHub issues, branches, and PRs
- Knowing what questions to ask during planning

**Result:** Great ideas never get built because the process is too intimidating.

## The Solution

A conversational AI agent that:
1. **Brainstorms** with you in plain English about your project idea
2. **Creates** a simple, readable vision document (not technical)
3. **Manages** the entire development workflow automatically
4. **Translates** your natural language into precise technical commands
5. **Tracks** what phase you're in and what comes next
6. **Notifies** you at decision points with simple yes/no questions
7. **Handles** all the technical complexity behind the scenes

## Key Features

### 1. Conversational Brainstorming
**What users experience:**
- Chat naturally about their idea
- Agent asks clarifying questions
- No need to know technical terms
- Feels like talking to a product consultant

**Example:**
```
You: I want to build a meal planning app

Agent: Great! Tell me more:
- Who would use this?
- What's the main problem it solves?
- How would someone use it daily?

You: Busy parents who waste food and can't decide what to cook

Agent: Perfect! Let's explore the features...
```

### 2. Vision Document Generation
**What users get:**
- 2-3 page readable document
- Describes WHAT, not HOW
- Features in plain English
- User experience walkthrough
- No technical jargon
- Success metrics they understand

**Example sections:**
- "What It Is" - One paragraph overview
- "Key Features" - Bullet points anyone can understand
- "User Journey" - Story of how someone uses it
- "Success Looks Like" - Clear, measurable goals

### 3. Approval Gates
**Decision points where user controls flow:**

**After Vision Doc:**
```
Agent: Here's what we're building [shows doc]
Approve to continue?

You: Yes
```

**After Each Phase:**
```
Agent: ✅ Phase 1 Done: User can sign up and log in
Start Phase 2: Meal suggestions?

You: Yes
```

**After Issues Found:**
```
Agent: Found a problem: Login fails on mobile
Should I fix it before continuing?

You: Yes
```

### 4. Automated Workflow Management
**What happens automatically (user doesn't see):**
- Creates GitHub repository
- Generates technical PRD
- Plans implementation phases
- Executes code changes
- Runs tests
- Creates pull requests
- Manages git branches
- Handles errors and retries

**What user sees:**
```
Agent: Starting build process...
⏳ Phase 1: Setting up project (2 min)
✅ Phase 1: Complete!
⏳ Phase 2: Building backend (15 min)
```

### 5. Natural Language Interface
**User never needs to remember commands:**

Instead of:
```
@scar /command-invoke plan-feature-github "Add user authentication with JWT"
```

Just say:
```
Add login functionality
```

Agent translates and executes the right commands.

### 6. Progress Tracking & Notifications
**Users always know status:**

**On Telegram:**
```
Agent: 🎉 Phase 3 complete!
Shopping list feature is working.
Test it here: [link]

Continue to Phase 4?
```

**On GitHub:**
- Status updates on issue
- Links to PRs
- Test deployment URLs
- Clear next steps

### 7. Smart Phase Management
**Agent decides when to:**
- Move to next phase
- Run additional tests
- Iterate on current phase
- Wait for user approval
- Handle errors gracefully

## User Experience Journey

### First Time: Building a Meal Planner App

**Day 1 - Morning (10 minutes):**
```
User creates GitHub repo "meal-planner"
Opens Issue #1: "Build meal planning app"

User: I want to help busy parents plan healthy meals

Agent: Great idea! Let me ask a few questions...
(10 back-and-forth messages)

Agent: Perfect! I've created a Vision Document.
(Shows readable 2-page doc)

User: Looks perfect! Build it.

Agent: Starting build process!
You'll get updates at each phase.
Feel free to close this tab - I'll notify you.
```

**Day 1 - Afternoon:**
```
Telegram notification:
✅ Phase 1 Complete: Project setup done
✅ Phase 2 Complete: Database ready
✅ Phase 3 Complete: User authentication working

You can test login here: meal-planner-staging.app
Continue to Phase 4 (meal suggestions)?
```

**Day 2:**
```
✅ Phase 4 Complete: Meal suggestion engine working
Try it: meal-planner-staging.app

Here's what it does:
- Takes your ingredient list
- Suggests 3 meal options
- Shows recipes

Test it and let me know if it matches your vision.
Ready for Phase 5?
```

**Day 3:**
```
🎉 All 6 phases complete!

Your app is live: meal-planner.app

Features working:
✅ User signup/login
✅ Ingredient tracking
✅ Meal suggestions
✅ Shopping lists
✅ Recipe database
✅ Weekly planning

Deployed to production.
Repository: github.com/you/meal-planner

Want to add more features?
```

### Ongoing: Adding New Features

```
User: Can we add meal prep scheduling?

Agent: Great idea! Let me understand what you want...
(brainstorms the feature)

Agent: Here's what I'll add:
- Calendar view of meals
- Prep time estimates
- Batch cooking suggestions

Approve?

User: Yes

Agent: Building it now...
(20 minutes later)

Agent: ✅ Meal prep scheduler added!
Live at: meal-planner.app/schedule
```

## Success Metrics

### User Success
- **90% completion rate** - Projects started actually get finished
- **<5 minute onboarding** - From idea to first phase executing
- **<24 hour MVP** - Working prototype in one day
- **Zero command memorization** - Users never look up syntax
- **80% satisfaction** - Users feel in control of the process

### Technical Success
- **95% phase success rate** - Phases complete without errors
- **<2 iterations average** - Features work on first or second try
- **100% git hygiene** - Clean branches, proper commits, no conflicts
- **All tests passing** - Every phase validated before continuation

### Experience Success
- **Users feel empowered** - "I built this!" not "The AI did it"
- **Clear communication** - Always know what's happening
- **Confidence building** - Each success builds trust
- **Learning happens** - Users understand their product better

## What Success Looks Like

**Week 1:**
```
User: "I had an idea on Monday. By Friday I had a working app
       with 5 features. I didn't write a single line of code
       or remember any commands. The agent just asked me questions
       and kept me updated. I feel like a product manager!"
```

**Month 1:**
```
User: "I've built 3 different prototypes to test different ideas.
       Each took 2-3 days. I just talk to the agent about what I want,
       approve the vision, and it handles everything. I've learned so
       much about product development just by watching it work."
```

**Month 6:**
```
User: "My meal planner app has 100 real users. I've added 15 features
       based on their feedback. The agent makes it easy to iterate.
       I'm not intimidated by development anymore - I understand how
       it all works now, even though I still can't code."
```

## Out of Scope (For MVP)

❌ Writing the actual code (SCAR does that)
❌ Designing UI/UX (user describes, agent implements)
❌ Project management for teams (single user focused)
❌ Custom code review (relies on SCAR's validation)
❌ Deployment configuration (uses standard setups)
❌ Database optimization (uses sensible defaults)

---

## Document Workflow

This vision document lives in `.agents/visions/` and flows through the development process:

```
.agents/visions/project-manager.md (this file)
  ↓ (user approves)
docs/PRD.md (generated by SCAR)
  ↓ (technical planning)
.agents/plans/project-manager.plan.md (implementation plan)
  ↓ (execution)
Working code in repository
```

**Next Steps:**
1. User reviews and approves this vision
2. Agent creates detailed PRD
3. Agent generates technical implementation plan
4. Agent executes the plan phase by phase
5. User approves at each phase gate
