# Plan: WebUI for Project Organizer

## Summary

Build a web-based user interface for the Project Organizer with a 3-panel layout inspired by VSCode. The left panel (20%) shows a project navigator with expandable issues and markdown docs, the middle panel (40%) provides direct chat with @po, and the right panel (40%) displays a real-time feed of SCAR interactions. The interface features resizable panels, simple username/password authentication, markdown doc viewing in a readable format, and mobile-friendly design. Deploy to po.153.se or po.153.se/webui.

## Intent

The Project Organizer currently has no web interface, forcing users to rely entirely on Telegram or GitHub issues for interaction. This WebUI will provide a unified dashboard where users can:
1. **Visualize project structure** - See all projects, issues (open/closed), and documentation in one place
2. **Chat directly with PM** - Conversational interface without needing to @mention
3. **Monitor SCAR activity** - Real-time visibility into the AI agent's work
4. **Access from anywhere** - Web-based interface accessible from any device, potentially replacing Telegram integration

This addresses the limitation of fragmented workflows and provides a centralized command center for managing AI-assisted development projects.

## Persona

**Primary User:** Non-technical entrepreneur or product manager who has ideas but can't code
- Uses multiple devices (desktop, tablet, phone) throughout the day
- Wants to see the "big picture" of their projects at a glance
- Prefers visual interfaces over command-line tools
- Needs to monitor AI agent progress without being glued to Telegram
- Values simplicity and clarity over technical complexity

**Usage Pattern:**
- Morning: Check project status from phone while commuting
- Afternoon: Chat with PM from desktop browser to refine features
- Evening: Review SCAR feed to understand what was built
- Weekend: Browse markdown docs to understand technical decisions

## UX

### Before Implementation

**Current State:**
```
User workflow is fragmented across multiple platforms:

1. GitHub Issues
   └─ Create issue with feature description
   └─ Mention @remote-agent
   └─ Wait for comment responses
   └─ Hard to see all projects at once
   └─ Can't monitor real-time SCAR activity

2. Telegram Topics
   └─ Chat with @po in separate threads
   └─ No visual project overview
   └─ Search through messages to find docs
   └─ SCAR feed not visible
   └─ Limited to one platform

3. Documentation scattered
   └─ Markdown files in GitHub repos
   └─ Hard to discover all docs
   └─ No reader-friendly view
```

**Pain Points:**
- User must switch between GitHub and Telegram constantly
- No single view of all projects and their status
- Cannot see SCAR working in real-time
- Markdown docs hard to read in raw GitHub view
- Mobile experience is poor (GitHub UI not optimized)
- No way to "just chat" without @mentioning

### After Implementation

**New State:**
```
┌──────────────────────────────────────────────────────────────────────────┐
│ Project Organizer - po.153.se                          [user] [settings] │
├────────────┬─────────────────────────────┬──────────────────────────────┤
│            │                             │                              │
│ PROJECTS   │   CHAT WITH @PM             │   SCAR FEED (Live)           │
│ (20%)      │   (40%)                     │   (40%)                      │
│            │                             │                              │
│ ├─📂 meal- │  You: I want to add a dark  │  [11:23:45] PM → SCAR       │
│ │  planner │      mode feature           │  Plan: Dark mode toggle     │
│ │  ├─ #1   │                             │                              │
│ │  │  ❓ open│  @po: Great idea! Let me   │  [11:23:47] SCAR → Claude   │
│ │  │  "Add  │       analyze your app...   │  Analyzing codebase...      │
│ │  │  auth" │                             │                              │
│ │  │        │  You: Make it purple/white  │  [11:24:12] Claude output   │
│ │  ├─ #2   │                             │  Found 3 components that    │
│ │  │  🔓 open│  @po: Perfect! I'll update │  need theme support:        │
│ │  │  "Dark"│       the plan...           │  - Header.tsx               │
│ │  │        │                             │  - Sidebar.tsx              │
│ │  ├─ 📁 docs│                            │  - Button.tsx               │
│ │  │  ├─ 📄 │  [Typing indicator...]      │                              │
│ │  │  │  PRD│                             │  [11:24:30] SCAR → Claude   │
│ │  │  ├─ 📄 │                             │  Implement dark mode        │
│ │  │  │  API│                             │                              │
│ │  ├─ 📁 × 1│                            │  [11:24:45] Claude output   │
│ │     ╰─ #0 │                             │  Creating DarkModeContext   │
│ │        ✅  │                             │  ✅ DarkModeContext.tsx     │
│ │        "Fix│                            │  ✅ useTheme.ts             │
│ │        bug"│                             │  ⏳ Updating Header.tsx    │
│ ├─📂 todo- │                             │                              │
│ │  app     │                             │  [Auto-scroll ⬇]            │
│ │  ├─ #5   │                             │                              │
│ │  │  🔓 open│                             │                              │
│ │  ├─ 📁 × 3│                             │                              │
│ ├─➕ New   │                             │                              │
│    Project │                             │                              │
│            │                             │                              │
│ [Resizable │←→ [Resizable divider] ←→   │                              │
│  divider]  │                             │                              │
└────────────┴─────────────────────────────┴──────────────────────────────┘

Interactions:
1. Click project → Expand to show issues and docs folder
2. Click issue → Opens in new browser tab (GitHub)
3. Click doc → Opens in readable markdown viewer (Google Docs-like)
4. Click "New Project" → Modal to create project
5. Type in chat → Direct message to @po (no @mention needed)
6. SCAR feed auto-scrolls as new events arrive
7. Drag dividers to resize panel proportions
8. Responsive: Collapses to single panel on mobile
```

**Mobile View (< 768px):**
```
┌─────────────────────────────────┐
│ Project Organizer     ☰ [menu] │
├─────────────────────────────────┤
│                                 │
│  [Tab: Projects | Chat | Feed] │
│                                 │
│  Active Tab Content             │
│  (full width)                   │
│                                 │
│                                 │
│                                 │
└─────────────────────────────────┘

- Tabs instead of side-by-side panels
- Swipe to switch tabs
- Same functionality, optimized for touch
```

**New Capabilities:**
✅ Single unified view of all projects
✅ Direct chat without @mentions
✅ Real-time visibility into SCAR work
✅ Beautiful markdown doc reader
✅ Mobile-friendly interface
✅ Resizable panels for custom layout
✅ Click to create new projects
✅ See open vs closed issues clearly
✅ Access from any device with a browser

## External Research

### Documentation

**React Resizable Panels:**
- [react-resizable-panels GitHub](https://github.com/bvaughn/react-resizable-panels) - Official library
- [react-resizable-panels npm](https://www.npmjs.com/package/react-resizable-panels) - Package documentation
- Key features: No dependencies, 12.8 kB bundle size, supports pixels/percentages/REMs
- Server rendering: Specify `defaultSize` prop to avoid layout flicker
- Conditional rendering: Supply `id` and `order` props when panels are conditionally rendered
- Layout persistence: Use `autoSaveId` to persist layouts via localStorage

**Real-Time Updates:**
- [WebSockets vs SSE - Ably Blog](https://ably.com/blog/websockets-vs-sse) - Comparison guide
- [Server-Sent Events 2025](https://medium.com/@ntiinsd/server-sent-events-powering-real-time-updates-without-websockets-in-2025-c08f5df9471c) - Modern SSE usage
- WebSockets: Full-duplex, bidirectional, complex protocol
- SSE: Unidirectional (server→client), HTTP-based, auto-reconnect built-in
- **Recommendation for SCAR feed: SSE** - Simpler, perfect for server→client streaming, automatic reconnection

**Markdown Rendering:**
- [Google Docs Markdown Support](https://support.google.com/docs/answer/12014036?hl=en) - Native support
- [Markdown Viewer and Editor](https://workspace.google.com/marketplace/app/markdown_viewer_and_editor/446183214552) - GFM support
- [StackEdit](https://stackedit.io/) - In-browser collaborative Markdown editor
- **Recommendation:** Use `react-markdown` with `remark-gfm` for GitHub Flavored Markdown
- Styling: Google Docs-like CSS (serif font, wide margins, heading navigation)

**Authentication:**
- [Passport.js](https://www.passportjs.org/) - Authentication middleware for Node.js
- [Node.js Authentication Guide](https://www.loginradius.com/blog/engineering/guest-post/nodejs-authentication-guide) - Comprehensive guide
- Simple username/password: Session-based auth with Passport Local Strategy
- Security: bcrypt for password hashing, express-session for sessions
- Single user: Hardcoded credentials in environment variables (MVP)

**Next.js 15 Project Structure:**
- [Best Practices for Next.js 15 2025](https://dev.to/bajrayejoon/best-practices-for-organizing-your-nextjs-15-2025-53ji) - Current patterns
- [Next.js Official Docs - Project Structure](https://nextjs.org/docs/app/getting-started/project-structure) - Official guide
- Feature-based organization: Group by feature, not file type
- Use `src/` directory for cleaner separation
- App Router: `app/` directory with route-based structure
- Components: `ui/` for primitives, `sections/` for composed components

### Gotchas & Best Practices

**React Resizable Panels:**
- ✅ Always specify `defaultSize` for SSR compatibility (Next.js)
- ✅ Use `autoSaveId` to persist user's panel layout preferences
- ✅ Provide `id` and `order` for conditionally rendered panels
- ⚠️ Don't nest too deep - performance degrades with many nested groups

**Server-Sent Events:**
- ✅ Built on HTTP - easy debugging, no special protocols
- ✅ Auto-reconnect out of the box via EventSource API
- ✅ 15,000 messages/sec throughput on modern hardware
- ⚠️ One-directional only (server→client) - need HTTP requests for client→server
- ⚠️ Browser limit: ~6 concurrent SSE connections per domain

**Next.js 15:**
- ✅ TypeScript is essential for large projects - catches errors early
- ✅ Use PascalCase for components, camelCase for props/methods
- ✅ Feature-based folders: `features/projects/`, `features/chat/`, `features/scar-feed/`
- ⚠️ Don't put all code in `app/` directory - use `src/`
- ⚠️ Avoid single `utils.ts` file - break into logical groups

**Authentication:**
- ✅ Always use HTTPS in production
- ✅ Hash passwords with bcrypt (salt + hash)
- ✅ Use express-session with secure, httpOnly cookies
- ⚠️ Never log or expose tokens/credentials
- ⚠️ For MVP: Hardcoded admin credentials in env vars is acceptable

**Mobile Responsiveness:**
- ✅ Mobile-first CSS: Start with mobile styles, add desktop via media queries
- ✅ Use Tailwind's responsive prefixes: `md:flex`, `lg:w-1/3`
- ✅ Touch targets: Minimum 44x44px for mobile tap areas
- ⚠️ Side-by-side panels don't work on mobile - use tabs instead

## Patterns to Mirror

Since this is a new codebase (no existing project-manager source code yet), we'll mirror patterns from:
1. **Telegram bot example** (`.agents/examples/codex-telegram-bot/`) - TypeScript, modular structure
2. **PRD architecture** (`.agents/PRD.md`) - Database schema, platform patterns
3. **Next.js best practices** (external research)

### Pattern 1: TypeScript Project Structure

**FROM: `.agents/examples/codex-telegram-bot/`**

```typescript
// File structure pattern:
src/
├── index.ts                 // Main entry point
├── config/
│   └── env.ts              // Environment validation
├── bot/
│   ├── commands/           // Command handlers
│   ├── handlers/           // Message handlers
│   └── utils/              // Utilities
├── session/
│   ├── manager.ts          // Session management
│   └── types.ts            // Type definitions
└── codex/
    ├── client.ts           // API client wrapper
    └── events.ts           // Event handling

// We mirror this as:
src/
├── server.ts               // Main entry point
├── config/
│   └── env.ts              // Environment validation
├── lib/
│   ├── db.ts              // Database client
│   └── auth.ts            // Authentication
├── features/
│   ├── projects/          // Project navigator feature
│   ├── chat/              // Chat with @po feature
│   └── scar-feed/         // SCAR real-time feed feature
└── api/
    ├── routes/            // API endpoints
    └── middleware/        // Express middleware
```

**Justification:** Modular, feature-based structure scales well and mirrors proven Telegram bot pattern.

### Pattern 2: Environment Configuration

**FROM: `.agents/examples/codex-telegram-bot/package.json:28-32`**

```typescript
// FROM: src/config/env.ts (inferred from package.json)
import dotenv from 'dotenv';
dotenv.config();

export function getEnvironment() {
  const required = {
    telegramBotToken: process.env.TELEGRAM_BOT_TOKEN,
    codexIdToken: process.env.CODEX_ID_TOKEN,
    // ... other required vars
  };

  // Validate all required vars exist
  for (const [key, value] of Object.entries(required)) {
    if (!value) {
      throw new Error(`Missing required environment variable: ${key}`);
    }
  }

  return required;
}

// We mirror this as:
// src/config/env.ts
export function getEnvironment() {
  const required = {
    databaseUrl: process.env.DATABASE_URL,
    jwtSecret: process.env.JWT_SECRET,
    adminUsername: process.env.ADMIN_USERNAME,
    adminPassword: process.env.ADMIN_PASSWORD_HASH,
    // ... other required vars
  };

  // Validate and return
}
```

**Justification:** Early environment validation prevents runtime errors. Pattern proven in Telegram bot.

### Pattern 3: Database Schema with Prefixes

**FROM: `.agents/PRD.md:26-108`**

```sql
-- Pattern: All tables use prefix to avoid conflicts
CREATE TABLE remote_agent_conversations (
  id UUID PRIMARY KEY,
  platform_type VARCHAR(20),
  -- ...
);

CREATE TABLE remote_agent_codebases (
  id UUID PRIMARY KEY,
  name VARCHAR(255),
  -- ...
);

CREATE TABLE remote_agent_sessions (
  id UUID PRIMARY KEY,
  conversation_id UUID REFERENCES remote_agent_conversations(id),
  -- ...
);
```

**We mirror this pattern:** Use `remote_agent_` prefix for all new tables (or reuse existing schema).

**Justification:** Follows established schema conventions, avoids table name conflicts.

### Pattern 4: API Client Wrapper Pattern

**FROM: `.agents/examples/codex-telegram-bot/src/codex/client.ts` (inferred)**

```typescript
// Pattern: Wrap external SDK with clean interface
export class CodexClient {
  private sdk: CodexSDK;

  constructor(config: CodexConfig) {
    this.sdk = new CodexSDK(config);
  }

  async sendMessage(message: string): Promise<void> {
    // Wrap SDK calls with error handling
    try {
      await this.sdk.send(message);
    } catch (error) {
      // Log and re-throw
    }
  }
}

// We mirror this for database queries:
// src/lib/db.ts
export class DatabaseClient {
  private pool: Pool;

  constructor(connectionString: string) {
    this.pool = new Pool({ connectionString });
  }

  async getProjects(userId: string): Promise<Project[]> {
    const result = await this.pool.query(
      'SELECT * FROM remote_agent_codebases WHERE user_id = $1',
      [userId]
    );
    return result.rows;
  }
}
```

**Justification:** Encapsulation, easier testing, cleaner error handling.

## Files to Change

Since this is a **new project** (no existing source code in `src/`), all files are **CREATE** operations.

| File | Action | Justification |
|------|--------|---------------|
| `package.json` | CREATE | Define dependencies (Next.js, React, TypeScript, Postgres, SSE, etc.) |
| `tsconfig.json` | CREATE | TypeScript configuration for Next.js |
| `.env.example` | CREATE | Template for required environment variables |
| `src/app/layout.tsx` | CREATE | Root Next.js App Router layout |
| `src/app/page.tsx` | CREATE | Main WebUI page with 3-panel layout |
| `src/app/api/auth/login/route.ts` | CREATE | Login endpoint for username/password auth |
| `src/app/api/auth/logout/route.ts` | CREATE | Logout endpoint |
| `src/app/api/projects/route.ts` | CREATE | API to fetch all projects |
| `src/app/api/projects/[id]/issues/route.ts` | CREATE | API to fetch issues for a project |
| `src/app/api/projects/[id]/docs/route.ts` | CREATE | API to fetch docs for a project |
| `src/app/api/chat/route.ts` | CREATE | POST messages to @po, GET chat history |
| `src/app/api/scar-feed/route.ts` | CREATE | SSE endpoint for real-time SCAR feed |
| `src/components/ui/ResizablePanels.tsx` | CREATE | Wrapper for react-resizable-panels |
| `src/components/sections/ProjectNavigator.tsx` | CREATE | Left panel - project tree view |
| `src/components/sections/ChatPanel.tsx` | CREATE | Middle panel - chat interface |
| `src/components/sections/ScarFeed.tsx` | CREATE | Right panel - real-time SCAR feed |
| `src/components/sections/MarkdownViewer.tsx` | CREATE | Modal for viewing markdown docs |
| `src/lib/db.ts` | CREATE | PostgreSQL client (Prisma or pg) |
| `src/lib/auth.ts` | CREATE | Authentication helpers (bcrypt, session) |
| `src/lib/scar-bridge.ts` | CREATE | Bridge to SCAR for real-time events |
| `src/config/env.ts` | CREATE | Environment variable validation |
| `src/types/index.ts` | CREATE | TypeScript type definitions |
| `prisma/schema.prisma` | CREATE | Database schema (if using Prisma) |
| `middleware.ts` | CREATE | Next.js middleware for auth redirect |
| `tailwind.config.ts` | CREATE | Tailwind CSS configuration |
| `Dockerfile` | CREATE | Docker container for deployment |
| `docker-compose.yml` | UPDATE | Add `webui` service to existing compose file |
| `nginx.conf` | CREATE | Nginx reverse proxy config for po.153.se |
| `README.md` | UPDATE | Add WebUI setup instructions |

**Total:** ~25 files (all new except docker-compose.yml and README.md updates)

## NOT Building

To prevent over-engineering, we are **explicitly NOT building**:

- ❌ **Multi-user authentication** - Only single admin user for MVP (username/password in .env)
- ❌ **User registration flow** - No signup, only hardcoded admin login
- ❌ **Project creation from WebUI** - Users create projects via GitHub, WebUI just displays them
- ❌ **Issue editing in WebUI** - Click issue opens GitHub in new tab (read-only in WebUI)
- ❌ **Inline markdown editing** - Docs are read-only, edited via GitHub
- ❌ **Chat message editing/deletion** - Simple append-only chat
- ❌ **SCAR feed filtering/search** - Just real-time stream, no advanced features
- ❌ **Dark mode** - Single light theme for MVP
- ❌ **Notifications** - No push notifications or email alerts
- ❌ **Analytics dashboard** - No usage metrics or charts
- ❌ **Collaborative features** - No multiple users, no presence indicators
- ❌ **Offline mode** - Requires active internet connection
- ❌ **Desktop app** - Web-only, no Electron wrapper
- ❌ **Telegram integration from WebUI** - WebUI is separate, not connected to Telegram
- ❌ **Custom themes** - Default styling only

## Tasks

### Task 1: Initialize Next.js Project with TypeScript

**Why**: Set up the foundation for the WebUI with Next.js 15 (modern React framework with SSR, routing, API routes).

**Mirror**: `.agents/examples/codex-telegram-bot/package.json:1-38` - TypeScript project structure

**Do**:
```bash
# Create Next.js project with TypeScript, Tailwind, App Router
npx create-next-app@latest webui --typescript --tailwind --app --no-src-dir --import-alias "@/*"

cd webui

# Install additional dependencies
npm install pg bcrypt express-session react-resizable-panels react-markdown remark-gfm
npm install -D @types/pg @types/bcrypt @types/express-session

# Alternative: Install Prisma (choose one approach)
npm install prisma @prisma/client
npm install -D prisma
```

**Don't**:
- Install unnecessary UI libraries (Material-UI, Ant Design) - use Tailwind
- Set up complex state management (Redux) - React Context is sufficient for MVP

**Verify**: `npm run dev` starts Next.js development server on http://localhost:3000

---

### Task 2: Environment Configuration and Validation

**Why**: Ensure required environment variables are present before app starts (prevent runtime errors).

**Mirror**: `.agents/examples/codex-telegram-bot/src/config/env.ts` (pattern inferred)

**Do**:

Create `src/config/env.ts`:
```typescript
export interface Environment {
  databaseUrl: string;
  jwtSecret: string;
  adminUsername: string;
  adminPasswordHash: string; // bcrypt hash, not plaintext
  nodeEnv: 'development' | 'production';
  nextPublicBaseUrl: string; // For SSE and API calls
}

export function getEnvironment(): Environment {
  const required = {
    databaseUrl: process.env.DATABASE_URL,
    jwtSecret: process.env.JWT_SECRET,
    adminUsername: process.env.ADMIN_USERNAME,
    adminPasswordHash: process.env.ADMIN_PASSWORD_HASH,
    nodeEnv: (process.env.NODE_ENV || 'development') as 'development' | 'production',
    nextPublicBaseUrl: process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3000',
  };

  // Validate all required vars exist
  const missing: string[] = [];
  for (const [key, value] of Object.entries(required)) {
    if (!value) {
      missing.push(key.toUpperCase());
    }
  }

  if (missing.length > 0) {
    throw new Error(`Missing required environment variables: ${missing.join(', ')}`);
  }

  return required;
}
```

Create `.env.example`:
```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/remote_coding_agent

# Authentication
JWT_SECRET=your-secret-key-min-32-chars
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=<bcrypt hash - use scripts/hash-password.ts>

# Next.js
NODE_ENV=development
NEXT_PUBLIC_BASE_URL=http://localhost:3000
```

Create `scripts/hash-password.ts`:
```typescript
import bcrypt from 'bcrypt';

const password = process.argv[2];
if (!password) {
  console.error('Usage: tsx scripts/hash-password.ts <password>');
  process.exit(1);
}

const hash = bcrypt.hashSync(password, 10);
console.log('Bcrypt hash:', hash);
console.log('\nAdd to .env:');
console.log(`ADMIN_PASSWORD_HASH=${hash}`);
```

**Don't**:
- Store plaintext passwords in environment variables
- Skip validation - fail fast if config is wrong

**Verify**: `tsx scripts/hash-password.ts mypassword` generates bcrypt hash

---

### Task 3: Database Client Setup

**Why**: Connect to existing PostgreSQL database (from PRD schema) to read projects, issues, conversations.

**Mirror**: `.agents/examples/codex-telegram-bot/src/codex/client.ts` - Client wrapper pattern

**Do**:

Create `src/lib/db.ts`:
```typescript
import { Pool } from 'pg';
import { getEnvironment } from '@/config/env';

const env = getEnvironment();

// Singleton connection pool
let pool: Pool | null = null;

export function getPool(): Pool {
  if (!pool) {
    pool = new Pool({
      connectionString: env.databaseUrl,
      max: 20, // Maximum connections
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: 2000,
    });
  }
  return pool;
}

// Database query helpers
export interface Project {
  id: string;
  name: string;
  repository_url: string;
  default_cwd: string;
  ai_assistant_type: string;
  created_at: Date;
}

export interface Issue {
  number: number;
  title: string;
  state: 'open' | 'closed';
  labels: string[];
  created_at: Date;
}

export async function getAllProjects(): Promise<Project[]> {
  const pool = getPool();
  const result = await pool.query(
    'SELECT * FROM remote_agent_codebases ORDER BY created_at DESC'
  );
  return result.rows;
}

export async function getProject(id: string): Promise<Project | null> {
  const pool = getPool();
  const result = await pool.query(
    'SELECT * FROM remote_agent_codebases WHERE id = $1',
    [id]
  );
  return result.rows[0] || null;
}

// More query functions as needed...
```

**Don't**:
- Create new connections for every query - use connection pool
- Expose raw SQL in API routes - abstract queries in db.ts

**Verify**: `tsx -r dotenv/config scripts/test-db.ts` successfully connects to database

---

### Task 4: Authentication Middleware

**Why**: Protect WebUI with username/password login, create session management.

**Mirror**: Session pattern from PRD, bcrypt best practices from research

**Do**:

Create `src/lib/auth.ts`:
```typescript
import bcrypt from 'bcrypt';
import { getEnvironment } from '@/config/env';

const env = getEnvironment();

export async function verifyPassword(username: string, password: string): Promise<boolean> {
  if (username !== env.adminUsername) {
    return false;
  }

  return await bcrypt.compare(password, env.adminPasswordHash);
}

export function generateToken(): string {
  // Simple JWT or session token
  // For MVP: Could use jose library or just session cookies
  return crypto.randomUUID();
}
```

Create `middleware.ts` (Next.js middleware):
```typescript
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const session = request.cookies.get('session');
  const isLoginPage = request.nextUrl.pathname === '/login';

  // Redirect to login if no session and not already on login page
  if (!session && !isLoginPage) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  // Redirect to home if has session and on login page
  if (session && isLoginPage) {
    return NextResponse.redirect(new URL('/', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
```

**Don't**:
- Implement complex JWT validation for MVP - simple session cookies are fine
- Allow registration - single admin user only

**Verify**: Accessing `/` without login redirects to `/login`

---

### Task 5: Login Page and API Route

**Why**: Provide login form and authentication endpoint.

**Mirror**: Telegram bot command structure - simple handlers

**Do**:

Create `src/app/login/page.tsx`:
```typescript
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });

    if (res.ok) {
      router.push('/');
    } else {
      setError('Invalid username or password');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white shadow-md rounded-lg p-8">
        <h1 className="text-2xl font-bold mb-6 text-center">
          Project Organizer
        </h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-3 py-2 border rounded-md"
              autoComplete="username"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border rounded-md"
              autoComplete="current-password"
            />
          </div>
          {error && <p className="text-red-600 text-sm">{error}</p>}
          <button
            type="submit"
            className="w-full bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700"
          >
            Login
          </button>
        </form>
      </div>
    </div>
  );
}
```

Create `src/app/api/auth/login/route.ts`:
```typescript
import { NextRequest, NextResponse } from 'next/server';
import { verifyPassword } from '@/lib/auth';

export async function POST(request: NextRequest) {
  const { username, password } = await request.json();

  const isValid = await verifyPassword(username, password);

  if (!isValid) {
    return NextResponse.json(
      { error: 'Invalid credentials' },
      { status: 401 }
    );
  }

  // Create session cookie
  const response = NextResponse.json({ success: true });
  response.cookies.set('session', crypto.randomUUID(), {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    maxAge: 60 * 60 * 24 * 7, // 7 days
    path: '/',
  });

  return response;
}
```

**Don't**:
- Store session data in cookies (security risk) - use server-side sessions
- Allow brute force - add rate limiting in production

**Verify**: Login with correct credentials redirects to `/`, wrong credentials shows error

---

### Task 6: Main Page Layout with Resizable Panels

**Why**: Create the 3-panel layout (projects, chat, SCAR feed) with resizable dividers.

**Mirror**: react-resizable-panels pattern from research

**Do**:

Create `src/app/page.tsx`:
```typescript
'use client';

import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import ProjectNavigator from '@/components/sections/ProjectNavigator';
import ChatPanel from '@/components/sections/ChatPanel';
import ScarFeed from '@/components/sections/ScarFeed';

export default function HomePage() {
  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="bg-white border-b px-4 py-3 flex justify-between items-center">
        <h1 className="text-xl font-bold">Project Organizer</h1>
        <div className="flex gap-4 items-center">
          <span className="text-sm text-gray-600">admin</span>
          <form action="/api/auth/logout" method="POST">
            <button className="text-sm text-blue-600 hover:underline">
              Logout
            </button>
          </form>
        </div>
      </header>

      {/* Main 3-panel layout */}
      <main className="flex-1 overflow-hidden">
        {/* Desktop: Side-by-side panels */}
        <div className="hidden md:block h-full">
          <PanelGroup direction="horizontal" autoSaveId="main-layout">
            {/* Left Panel: Projects (20%) */}
            <Panel defaultSize={20} minSize={15} maxSize={40} id="projects">
              <ProjectNavigator />
            </Panel>

            <PanelResizeHandle className="w-1 bg-gray-200 hover:bg-blue-400 transition-colors" />

            {/* Middle Panel: Chat (40%) */}
            <Panel defaultSize={40} minSize={30} id="chat">
              <ChatPanel />
            </Panel>

            <PanelResizeHandle className="w-1 bg-gray-200 hover:bg-blue-400 transition-colors" />

            {/* Right Panel: SCAR Feed (40%) */}
            <Panel defaultSize={40} minSize={30} id="scar-feed">
              <ScarFeed />
            </Panel>
          </PanelGroup>
        </div>

        {/* Mobile: Tabs */}
        <div className="md:hidden h-full">
          {/* TODO: Implement tabbed view for mobile */}
          <p className="p-4 text-gray-600">Mobile view coming soon</p>
        </div>
      </main>
    </div>
  );
}
```

**Don't**:
- Build mobile tabs in this task - focus on desktop first
- Add complex styling - keep it minimal, functional

**Verify**: Page loads with 3 resizable panels, dividers can be dragged

---

### Task 7: Project Navigator Component (Left Panel)

**Why**: Display tree view of projects with expandable issues and docs.

**Mirror**: GitHub file tree pattern, recursive component structure

**Do**:

Create `src/components/sections/ProjectNavigator.tsx`:
```typescript
'use client';

import { useEffect, useState } from 'react';

interface Project {
  id: string;
  name: string;
  repository_url: string;
}

export default function ProjectNavigator() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [expandedProjects, setExpandedProjects] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetch('/api/projects')
      .then(res => res.json())
      .then(data => setProjects(data));
  }, []);

  const toggleProject = (id: string) => {
    setExpandedProjects(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  return (
    <div className="h-full bg-gray-50 border-r overflow-y-auto p-4">
      <h2 className="text-lg font-semibold mb-4">Projects</h2>

      <div className="space-y-2">
        {projects.map(project => (
          <div key={project.id}>
            {/* Project header */}
            <div
              className="flex items-center gap-2 cursor-pointer hover:bg-gray-200 p-2 rounded"
              onClick={() => toggleProject(project.id)}
            >
              <span>{expandedProjects.has(project.id) ? '▼' : '▶'}</span>
              <span className="font-medium">📂 {project.name}</span>
            </div>

            {/* Expanded content */}
            {expandedProjects.has(project.id) && (
              <div className="ml-6 mt-2 space-y-1">
                <div className="text-sm text-gray-600">Issues loading...</div>
                <div className="text-sm text-gray-600">Docs loading...</div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* New Project Button */}
      <button className="mt-4 w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700">
        ➕ New Project
      </button>
    </div>
  );
}
```

Create `src/app/api/projects/route.ts`:
```typescript
import { NextResponse } from 'next/server';
import { getAllProjects } from '@/lib/db';

export async function GET() {
  const projects = await getAllProjects();
  return NextResponse.json(projects);
}
```

**Don't**:
- Implement issue fetching yet - placeholder text is fine
- Add search/filter - keep it simple

**Verify**: Projects load and can be expanded/collapsed

---

### Task 8: Fetch and Display Issues for Projects

**Why**: Show open and closed issues for each project, grouped in folders.

**Mirror**: GitHub API issue fetching pattern

**Do**:

Update `src/lib/db.ts` with GitHub fetching helper:
```typescript
// Add Octokit for GitHub API
import { Octokit } from '@octokit/rest';

const octokit = new Octokit({
  auth: process.env.GITHUB_TOKEN
});

export async function getIssuesForRepo(repoUrl: string): Promise<Issue[]> {
  // Parse owner/repo from URL
  const match = repoUrl.match(/github\.com\/([^/]+)\/([^/]+)/);
  if (!match) return [];

  const [, owner, repo] = match;

  const { data } = await octokit.issues.listForRepo({
    owner,
    repo: repo.replace('.git', ''),
    state: 'all', // Get both open and closed
    per_page: 100,
  });

  return data.map(issue => ({
    number: issue.number,
    title: issue.title,
    state: issue.state as 'open' | 'closed',
    labels: issue.labels.map(l => typeof l === 'string' ? l : l.name || ''),
    created_at: new Date(issue.created_at),
  }));
}
```

Create `src/app/api/projects/[id]/issues/route.ts`:
```typescript
import { NextRequest, NextResponse } from 'next/server';
import { getProject, getIssuesForRepo } from '@/lib/db';

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const project = await getProject(params.id);
  if (!project) {
    return NextResponse.json({ error: 'Project not found' }, { status: 404 });
  }

  const issues = await getIssuesForRepo(project.repository_url);
  return NextResponse.json(issues);
}
```

Update `ProjectNavigator.tsx` to fetch issues when expanded:
```typescript
// Add state for issues
const [issues, setIssues] = useState<Record<string, Issue[]>>({});

// Fetch issues when project is expanded
const toggleProject = async (id: string) => {
  const next = new Set(expandedProjects);
  if (next.has(id)) {
    next.delete(id);
  } else {
    next.add(id);
    // Fetch issues if not already loaded
    if (!issues[id]) {
      const res = await fetch(`/api/projects/${id}/issues`);
      const data = await res.json();
      setIssues(prev => ({ ...prev, [id]: data }));
    }
  }
  setExpandedProjects(next);
};

// Render issues in expanded view
{expandedProjects.has(project.id) && (
  <div className="ml-6 mt-2 space-y-1">
    {/* Open Issues */}
    {issues[project.id]?.filter(i => i.state === 'open').map(issue => (
      <div key={issue.number} className="text-sm">
        <a
          href={`${project.repository_url}/issues/${issue.number}`}
          target="_blank"
          className="text-blue-600 hover:underline"
        >
          #{issue.number} {issue.title}
        </a>
      </div>
    ))}

    {/* Closed Issues Folder */}
    <details className="text-sm">
      <summary className="cursor-pointer">📁 Closed Issues ({issues[project.id]?.filter(i => i.state === 'closed').length || 0})</summary>
      <div className="ml-4 mt-1 space-y-1">
        {issues[project.id]?.filter(i => i.state === 'closed').map(issue => (
          <div key={issue.number}>
            <a
              href={`${project.repository_url}/issues/${issue.number}`}
              target="_blank"
              className="text-gray-600 hover:underline"
            >
              #{issue.number} {issue.title}
            </a>
          </div>
        ))}
      </div>
    </details>
  </div>
)}
```

**Don't**:
- Cache issues indefinitely - refetch on expand or use SWR/React Query
- Show all 1000 issues - limit to recent 100

**Verify**: Expanding project loads issues from GitHub, clicking issue opens GitHub in new tab

---

### Task 9: Chat Panel Component (Middle Panel)

**Why**: Direct chat interface with @po without needing to @mention.

**Mirror**: Telegram message handler pattern

**Do**:

Create `src/components/sections/ChatPanel.tsx`:
```typescript
'use client';

import { useState, useEffect, useRef } from 'react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export default function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input }),
      });

      const data = await res.json();
      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: data.response,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="border-b px-4 py-3">
        <h2 className="text-lg font-semibold">Chat with @po</h2>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map(msg => (
          <div
            key={msg.id}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] px-4 py-2 rounded-lg ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.content}</p>
              <p className="text-xs mt-1 opacity-70">
                {msg.timestamp.toLocaleTimeString()}
              </p>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 px-4 py-2 rounded-lg">
              <p className="text-gray-500">Typing...</p>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={sendMessage} className="border-t p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Message @po..."
            className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loading}
          />
          <button
            type="submit"
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            disabled={loading || !input.trim()}
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
}
```

Create `src/app/api/chat/route.ts`:
```typescript
import { NextRequest, NextResponse } from 'next/server';

// TODO: Integrate with actual @po backend
// For MVP: Mock response
export async function POST(request: NextRequest) {
  const { message } = await request.json();

  // Simulate processing delay
  await new Promise(resolve => setTimeout(resolve, 1000));

  // Mock response
  const response = `I received your message: "${message}". This is a mock response. Integration with @po backend coming soon.`;

  return NextResponse.json({ response });
}

export async function GET(request: NextRequest) {
  // TODO: Fetch chat history from database
  return NextResponse.json([]);
}
```

**Don't**:
- Implement full @po integration in this task - mock response is fine
- Add file uploads yet - text-only chat for MVP

**Verify**: Can type message, click send, receive mock response, messages auto-scroll

---

### Task 10: SCAR Feed Component with Server-Sent Events (Right Panel)

**Why**: Real-time visibility into SCAR activity (what PM sends to SCAR, SCAR's responses).

**Mirror**: SSE pattern from research, EventSource API

**Do**:

Create `src/components/sections/ScarFeed.tsx`:
```typescript
'use client';

import { useEffect, useState, useRef } from 'react';

interface ScarEvent {
  id: string;
  timestamp: Date;
  type: 'po_to_scar' | 'scar_to_claude' | 'claude_output';
  content: string;
}

export default function ScarFeed() {
  const [events, setEvents] = useState<ScarEvent[]>([]);
  const eventSourceRef = useRef<EventSource | null>(null);
  const eventsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Connect to SSE endpoint
    const eventSource = new EventSource('/api/scar-feed');
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (e) => {
      const event: ScarEvent = JSON.parse(e.data);
      setEvents(prev => [...prev, event]);
    };

    eventSource.onerror = (error) => {
      console.error('SSE connection error:', error);
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    eventsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events]);

  const getEventColor = (type: ScarEvent['type']) => {
    switch (type) {
      case 'po_to_scar': return 'text-blue-600';
      case 'scar_to_claude': return 'text-purple-600';
      case 'claude_output': return 'text-green-600';
    }
  };

  const getEventLabel = (type: ScarEvent['type']) => {
    switch (type) {
      case 'po_to_scar': return 'PM → SCAR';
      case 'scar_to_claude': return 'SCAR → Claude';
      case 'claude_output': return 'Claude Output';
    }
  };

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="border-b bg-white px-4 py-3">
        <h2 className="text-lg font-semibold">SCAR Feed (Live)</h2>
      </div>

      {/* Events */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {events.length === 0 && (
          <p className="text-gray-500 text-sm">Waiting for SCAR activity...</p>
        )}
        {events.map(event => (
          <div key={event.id} className="bg-white p-3 rounded shadow-sm">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs text-gray-500">
                {event.timestamp.toLocaleTimeString()}
              </span>
              <span className={`text-xs font-semibold ${getEventColor(event.type)}`}>
                {getEventLabel(event.type)}
              </span>
            </div>
            <p className="text-sm whitespace-pre-wrap">{event.content}</p>
          </div>
        ))}
        <div ref={eventsEndRef} />
      </div>
    </div>
  );
}
```

Create `src/app/api/scar-feed/route.ts`:
```typescript
import { NextRequest } from 'next/server';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const encoder = new TextEncoder();

  // Create a readable stream for SSE
  const stream = new ReadableStream({
    start(controller) {
      // Send initial connection message
      const data = JSON.stringify({
        id: crypto.randomUUID(),
        timestamp: new Date(),
        type: 'claude_output',
        content: 'Connected to SCAR feed',
      });
      controller.enqueue(encoder.encode(`data: ${data}\n\n`));

      // TODO: Subscribe to actual SCAR events
      // For MVP: Send mock events every 5 seconds
      const interval = setInterval(() => {
        const mockEvent = {
          id: crypto.randomUUID(),
          timestamp: new Date(),
          type: ['po_to_scar', 'scar_to_claude', 'claude_output'][
            Math.floor(Math.random() * 3)
          ],
          content: `Mock event at ${new Date().toLocaleTimeString()}`,
        };
        controller.enqueue(encoder.encode(`data: ${JSON.stringify(mockEvent)}\n\n`));
      }, 5000);

      // Cleanup on connection close
      request.signal.addEventListener('abort', () => {
        clearInterval(interval);
        controller.close();
      });
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  });
}
```

**Don't**:
- Implement full SCAR integration - mock events are fine for MVP
- Store all events indefinitely - limit to last 100 in memory

**Verify**: SCAR feed connects via SSE, receives mock events every 5 seconds, auto-scrolls

---

### Task 11: Markdown Viewer Modal

**Why**: Display markdown docs (from GitHub) in a readable, Google Docs-like format.

**Mirror**: Google Docs styling from research, react-markdown library

**Do**:

Install dependencies:
```bash
npm install react-markdown remark-gfm
```

Create `src/components/sections/MarkdownViewer.tsx`:
```typescript
'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MarkdownViewerProps {
  content: string;
  filename: string;
  onClose: () => void;
}

export default function MarkdownViewer({ content, filename, onClose }: MarkdownViewerProps) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b px-6 py-4">
          <h2 className="text-xl font-semibold">{filename}</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-8">
          <article className="prose prose-lg max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {content}
            </ReactMarkdown>
          </article>
        </div>
      </div>
    </div>
  );
}
```

Add Google Docs-like styling to `tailwind.config.ts`:
```typescript
export default {
  theme: {
    extend: {
      typography: {
        DEFAULT: {
          css: {
            fontFamily: 'Georgia, serif',
            lineHeight: '1.7',
            fontSize: '16px',
            h1: {
              fontFamily: 'system-ui, sans-serif',
              fontWeight: '600',
              marginTop: '2em',
              marginBottom: '0.5em',
            },
            h2: {
              fontFamily: 'system-ui, sans-serif',
              fontWeight: '600',
              marginTop: '1.5em',
              marginBottom: '0.5em',
            },
            // ... more heading styles
          },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
};
```

Update `ProjectNavigator.tsx` to show docs and open modal:
```typescript
// Add state for markdown viewer
const [markdownViewer, setMarkdownViewer] = useState<{
  content: string;
  filename: string;
} | null>(null);

// Fetch and display markdown file
const openMarkdownFile = async (projectId: string, filepath: string) => {
  const res = await fetch(`/api/projects/${projectId}/docs?path=${encodeURIComponent(filepath)}`);
  const data = await res.json();
  setMarkdownViewer({
    content: data.content,
    filename: filepath,
  });
};

// Render modal
{markdownViewer && (
  <MarkdownViewer
    content={markdownViewer.content}
    filename={markdownViewer.filename}
    onClose={() => setMarkdownViewer(null)}
  />
)}
```

Create `src/app/api/projects/[id]/docs/route.ts`:
```typescript
import { NextRequest, NextResponse } from 'next/server';
import { getProject } from '@/lib/db';
import { Octokit } from '@octokit/rest';

const octokit = new Octokit({ auth: process.env.GITHUB_TOKEN });

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const project = await getProject(params.id);
  if (!project) {
    return NextResponse.json({ error: 'Project not found' }, { status: 404 });
  }

  const path = request.nextUrl.searchParams.get('path');
  if (!path) {
    return NextResponse.json({ error: 'Path required' }, { status: 400 });
  }

  // Parse owner/repo from URL
  const match = project.repository_url.match(/github\.com\/([^/]+)\/([^/]+)/);
  if (!match) {
    return NextResponse.json({ error: 'Invalid repo URL' }, { status: 400 });
  }

  const [, owner, repo] = match;

  try {
    const { data } = await octokit.repos.getContent({
      owner,
      repo: repo.replace('.git', ''),
      path,
    });

    if ('content' in data) {
      const content = Buffer.from(data.content, 'base64').toString('utf-8');
      return NextResponse.json({ content });
    } else {
      return NextResponse.json({ error: 'Not a file' }, { status: 400 });
    }
  } catch (error) {
    return NextResponse.json({ error: 'Failed to fetch file' }, { status: 500 });
  }
}
```

**Don't**:
- Allow editing markdown - read-only viewer
- Support all file types - only .md files

**Verify**: Clicking markdown doc opens modal with styled, readable markdown

---

### Task 12: Mobile Responsive Layout with Tabs

**Why**: Provide usable interface on mobile devices (3 panels side-by-side doesn't work on small screens).

**Mirror**: Tailwind responsive breakpoints, common tab pattern

**Do**:

Update `src/app/page.tsx` to add mobile tab view:
```typescript
'use client';

import { useState } from 'react';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import ProjectNavigator from '@/components/sections/ProjectNavigator';
import ChatPanel from '@/components/sections/ChatPanel';
import ScarFeed from '@/components/sections/ScarFeed';

type Tab = 'projects' | 'chat' | 'feed';

export default function HomePage() {
  const [activeTab, setActiveTab] = useState<Tab>('projects');

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="bg-white border-b px-4 py-3 flex justify-between items-center">
        <h1 className="text-xl font-bold">Project Organizer</h1>
        <div className="flex gap-4 items-center">
          <span className="text-sm text-gray-600">admin</span>
          <form action="/api/auth/logout" method="POST">
            <button className="text-sm text-blue-600 hover:underline">
              Logout
            </button>
          </form>
        </div>
      </header>

      {/* Mobile: Tabs */}
      <div className="md:hidden border-b bg-white flex">
        <button
          onClick={() => setActiveTab('projects')}
          className={`flex-1 py-3 text-sm font-medium ${
            activeTab === 'projects'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-600'
          }`}
        >
          Projects
        </button>
        <button
          onClick={() => setActiveTab('chat')}
          className={`flex-1 py-3 text-sm font-medium ${
            activeTab === 'chat'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-600'
          }`}
        >
          Chat
        </button>
        <button
          onClick={() => setActiveTab('feed')}
          className={`flex-1 py-3 text-sm font-medium ${
            activeTab === 'feed'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-600'
          }`}
        >
          SCAR Feed
        </button>
      </div>

      {/* Main layout */}
      <main className="flex-1 overflow-hidden">
        {/* Desktop: Side-by-side panels */}
        <div className="hidden md:block h-full">
          <PanelGroup direction="horizontal" autoSaveId="main-layout">
            <Panel defaultSize={20} minSize={15} maxSize={40} id="projects">
              <ProjectNavigator />
            </Panel>

            <PanelResizeHandle className="w-1 bg-gray-200 hover:bg-blue-400 transition-colors" />

            <Panel defaultSize={40} minSize={30} id="chat">
              <ChatPanel />
            </Panel>

            <PanelResizeHandle className="w-1 bg-gray-200 hover:bg-blue-400 transition-colors" />

            <Panel defaultSize={40} minSize={30} id="scar-feed">
              <ScarFeed />
            </Panel>
          </PanelGroup>
        </div>

        {/* Mobile: Active tab content */}
        <div className="md:hidden h-full">
          {activeTab === 'projects' && <ProjectNavigator />}
          {activeTab === 'chat' && <ChatPanel />}
          {activeTab === 'feed' && <ScarFeed />}
        </div>
      </main>
    </div>
  );
}
```

**Don't**:
- Add swipe gestures - simple tap is fine for MVP
- Persist active tab - reset to projects on reload

**Verify**: On mobile (<768px), see tabs instead of panels; clicking tab switches view

---

### Task 13: Docker and Deployment Configuration

**Why**: Package WebUI for deployment to po.153.se.

**Mirror**: PRD Dockerfile pattern, Docker Compose profiles

**Do**:

Create `Dockerfile`:
```dockerfile
FROM node:20-slim

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --production=false

# Copy source
COPY . .

# Build Next.js app
RUN npm run build

# Expose port
EXPOSE 3000

# Start app
CMD ["npm", "start"]
```

Update `docker-compose.yml` (add webui service):
```yaml
services:
  webui:
    build:
      context: ./webui
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - JWT_SECRET=${JWT_SECRET}
      - ADMIN_USERNAME=${ADMIN_USERNAME}
      - ADMIN_PASSWORD_HASH=${ADMIN_PASSWORD_HASH}
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - NEXT_PUBLIC_BASE_URL=https://po.153.se
    depends_on:
      - postgres
    restart: unless-stopped

  # ... existing services (postgres, app, etc.)
```

Create `nginx.conf` for reverse proxy:
```nginx
server {
    listen 80;
    server_name po.153.se;

    location / {
        proxy_pass http://webui:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;

        # SSE support
        proxy_buffering off;
        proxy_read_timeout 24h;
    }
}
```

**Don't**:
- Configure HTTPS in nginx - use Cloudflare or Let's Encrypt separately
- Add complex nginx caching - keep it simple

**Verify**: `docker-compose up webui` builds and starts WebUI on port 3000

---

## Validation Strategy

### Automated Checks

- [ ] `npm run type-check` - TypeScript types are valid (no errors)
- [ ] `npm run lint` - ESLint passes (Next.js default config)
- [ ] `npm run build` - Next.js build succeeds without errors
- [ ] `docker build -t webui .` - Docker image builds successfully

### New Tests to Write

Since this is a new codebase with MVP scope, we'll start with manual testing. Unit tests can be added in future iterations.

**If adding tests (optional for MVP):**

| Test File | Test Case | What It Validates |
|-----------|-----------|-------------------|
| `__tests__/lib/auth.test.ts` | `verifyPassword()` with correct credentials | Returns true |
| `__tests__/lib/auth.test.ts` | `verifyPassword()` with wrong credentials | Returns false |
| `__tests__/lib/db.test.ts` | `getAllProjects()` | Fetches projects from database |
| `__tests__/api/login.test.ts` | POST `/api/auth/login` with valid creds | Returns 200 and sets cookie |
| `__tests__/api/login.test.ts` | POST `/api/auth/login` with invalid creds | Returns 401 |

**Test Framework (if implemented):** Jest or Vitest with React Testing Library

### Manual/E2E Validation

**Environment Setup:**
```bash
# 1. Set up environment
cp .env.example .env
# Edit .env with real values

# 2. Generate password hash
tsx scripts/hash-password.ts mypassword
# Copy hash to .env as ADMIN_PASSWORD_HASH

# 3. Start database (or use existing)
docker-compose --profile with-db up postgres -d

# 4. Start dev server
npm run dev
```

**Test Cases:**

1. **Authentication Flow**
   - [ ] Navigate to http://localhost:3000
   - [ ] Should redirect to `/login`
   - [ ] Enter wrong username/password → Shows error
   - [ ] Enter correct username/password → Redirects to `/`
   - [ ] Session persists on page reload
   - [ ] Click "Logout" → Redirects to `/login`

2. **Project Navigator (Left Panel)**
   - [ ] Projects load from database
   - [ ] Click project name → Expands to show issues
   - [ ] Open issues displayed with # and title
   - [ ] Closed issues grouped in collapsible "Closed Issues" folder
   - [ ] Click issue → Opens GitHub issue in new tab
   - [ ] "New Project" button visible (can be non-functional for MVP)

3. **Chat Panel (Middle Panel)**
   - [ ] Type message in input field
   - [ ] Click "Send" → Message appears on right (blue background)
   - [ ] Mock response appears on left (gray background)
   - [ ] "Typing..." indicator shows while waiting
   - [ ] Messages auto-scroll to bottom
   - [ ] Timestamps displayed for each message

4. **SCAR Feed (Right Panel)**
   - [ ] "Connected to SCAR feed" message appears
   - [ ] Mock events arrive every 5 seconds
   - [ ] Events color-coded (blue/purple/green)
   - [ ] Timestamps displayed
   - [ ] Auto-scrolls to bottom as new events arrive

5. **Resizable Panels (Desktop)**
   - [ ] Drag left divider → Projects panel resizes
   - [ ] Drag right divider → Chat/Feed panels resize
   - [ ] Panel sizes persist on page reload (via localStorage)
   - [ ] Minimum/maximum sizes enforced

6. **Mobile Responsive (< 768px)**
   - [ ] Tabs visible instead of side-by-side panels
   - [ ] Click "Projects" tab → Shows project navigator
   - [ ] Click "Chat" tab → Shows chat panel
   - [ ] Click "SCAR Feed" tab → Shows SCAR feed
   - [ ] All functionality works in tabbed view

7. **Markdown Viewer**
   - [ ] Click markdown file in project docs folder
   - [ ] Modal opens with styled markdown
   - [ ] Markdown rendered with headings, lists, code blocks
   - [ ] Click X or outside modal → Closes
   - [ ] Google Docs-like styling (serif font, wide margins)

8. **SSE Connection**
   - [ ] Open browser DevTools → Network tab
   - [ ] Filter for `scar-feed`
   - [ ] Should show EventStream connection (pending)
   - [ ] Events appear in real-time
   - [ ] Refresh page → Reconnects automatically

### Edge Cases

- [ ] **No projects in database** - Shows empty state message
- [ ] **GitHub API rate limit** - Shows error, degrades gracefully
- [ ] **Database connection fails** - Shows error page, doesn't crash
- [ ] **Very long issue titles** - Truncates or wraps properly
- [ ] **Markdown with special characters** - Renders correctly
- [ ] **SSE connection drops** - EventSource auto-reconnects
- [ ] **Rapid panel resizing** - No visual glitches
- [ ] **Mobile viewport rotation** - Layout adjusts correctly
- [ ] **Browser back button after login** - Doesn't break session
- [ ] **Session expires** - Redirects to login

### Regression Check

Since this is a new project with no existing functionality:
- [ ] Verify existing database schema not modified (read-only access to `remote_agent_*` tables)
- [ ] Existing GitHub repos/issues not affected
- [ ] No conflicts with existing services in docker-compose.yml

### Performance Validation

- [ ] **Initial page load** - < 3 seconds on 3G connection
- [ ] **Time to interactive** - < 5 seconds
- [ ] **SSE message latency** - < 500ms from server to UI
- [ ] **Panel resize** - Smooth 60fps animation
- [ ] **Fetch 100 issues** - < 2 seconds
- [ ] **Lighthouse score** - Performance > 80, Accessibility > 90

### Security Validation

- [ ] **Password never logged** - Check server logs
- [ ] **Session cookie is httpOnly** - Check browser DevTools → Application → Cookies
- [ ] **Session cookie is secure in production** - Only sent over HTTPS
- [ ] **API routes require authentication** - Test with `curl` without cookie
- [ ] **CORS properly configured** - No unauthorized origins
- [ ] **Environment variables not exposed** - Check page source
- [ ] **SQL injection not possible** - Parameterized queries only
- [ ] **XSS not possible** - Markdown sanitized, user input escaped

## Risks

### Technical Risks

1. **GitHub API Rate Limits**
   - **Risk:** Fetching issues/docs exceeds GitHub's rate limit (5000/hour authenticated)
   - **Impact:** Features stop working, users see errors
   - **Mitigation:** Cache issue/doc data, show cached data with "Last updated" timestamp, implement exponential backoff

2. **SSE Connection Stability**
   - **Risk:** Long-lived SSE connections may drop due to proxies, firewalls, or server restarts
   - **Impact:** SCAR feed stops updating
   - **Mitigation:** EventSource auto-reconnect handles most cases, show "Reconnecting..." indicator, buffer recent events

3. **Database Schema Changes**
   - **Risk:** PRD database schema evolves, breaking WebUI queries
   - **Impact:** Projects/issues fail to load
   - **Mitigation:** Use abstraction layer (db.ts), version database schema, write migration-friendly queries

4. **Next.js SSR Hydration Errors**
   - **Risk:** Mismatch between server and client rendering (especially with dynamic data)
   - **Impact:** Console errors, potential UI bugs
   - **Mitigation:** Use `'use client'` for dynamic components, specify `defaultSize` for panels, avoid window/localStorage in SSR

### Integration Risks

1. **@po Backend Not Implemented**
   - **Risk:** Chat panel has no real backend to send messages to
   - **Impact:** Feature incomplete
   - **Mitigation:** Use mock responses for MVP, document integration API contract, add TODO comments

2. **SCAR Event Bridge Not Implemented**
   - **Risk:** No real-time events from SCAR to display
   - **Impact:** SCAR feed shows only mock data
   - **Mitigation:** Use mock events for MVP, design SSE API contract, add integration point in comments

### Deployment Risks

1. **Nginx Configuration Errors**
   - **Risk:** Misconfigured proxy breaks SSE or sessions
   - **Impact:** WebUI unreachable or partially broken
   - **Mitigation:** Test locally with nginx before deploying, verify SSE works through proxy, monitor logs

2. **Docker Port Conflicts**
   - **Risk:** Port 3000 already in use on server
   - **Impact:** Container fails to start
   - **Mitigation:** Use environment variable for port, check docker-compose port mappings, use nginx as reverse proxy (80/443)

### User Experience Risks

1. **Mobile Keyboard Covers Input**
   - **Risk:** Virtual keyboard on mobile devices covers chat input
   - **Impact:** Poor mobile UX
   - **Mitigation:** Test on real mobile devices, use viewport units, add padding when keyboard appears

2. **Large Project Trees Slow to Render**
   - **Risk:** Projects with 100+ issues cause UI lag
   - **Impact:** Navigator feels sluggish
   - **Mitigation:** Virtualize long lists, paginate issues, lazy-load closed issues

---

## Summary

This plan provides a complete implementation guide for building a WebUI for the Project Organizer. The approach mirrors proven patterns from the existing Telegram bot, follows Next.js 15 best practices, and uses modern web technologies (React, SSE, Tailwind).

**Key Technologies:**
- **Frontend:** Next.js 15 (App Router), React, TypeScript, Tailwind CSS
- **Backend:** Next.js API Routes, PostgreSQL, Server-Sent Events (SSE)
- **UI:** react-resizable-panels, react-markdown, Tailwind Typography
- **Auth:** bcrypt, session cookies, simple username/password
- **Deployment:** Docker, Nginx, deployed to po.153.se

**Implementation Phases:**
1. **Phase 1 (Tasks 1-5):** Foundation - Next.js setup, auth, database, environment config
2. **Phase 2 (Tasks 6-8):** Left Panel - Project navigator with GitHub integration
3. **Phase 3 (Tasks 9-10):** Middle & Right Panels - Chat interface and SCAR feed
4. **Phase 4 (Tasks 11-12):** Enhancements - Markdown viewer, mobile responsive
5. **Phase 5 (Task 13):** Deployment - Docker, Nginx, production config

**MVP Scope:**
- Single admin user (no registration)
- Read-only project/issue viewing (click opens GitHub)
- Mock chat and SCAR feed (real integration in future)
- Desktop-first with mobile tabs
- Simple, functional design

**Out of Scope (Post-MVP):**
- Multi-user support, project creation from UI, inline editing
- Real-time @po chat integration, actual SCAR event streaming
- Advanced features (dark mode, notifications, analytics)

The plan is ready for implementation. Execute with `/implement .agents/plans/webui-project-organizer.plan.md`.
