# Feature: Web Interface with 3-Panel Layout for Project Management and SCAR Monitoring

The following plan should be complete, but it's important that you validate documentation and codebase patterns and task sanity before you start implementing.

Pay special attention to naming of existing utils types and models. Import from the right files etc.

## Feature Description

Build a comprehensive web-based user interface for the Project Orchestrator system that provides a unified workspace with three resizable panels:
- **Left Panel (20%)**: Project navigator with tree structure showing all projects, issues (open/closed), and discoverable documents
- **Middle Panel (40%)**: Chat interface for conversing with @po (Project Orchestrator) without explicit @mentions
- **Right Panel (40%)**: Real-time SCAR activity feed displaying @po → SCAR → Claude communications with configurable verbosity

This interface serves as the primary visual workspace for users to manage projects, interact with the AI assistant, and monitor development workflows in real-time.

## User Story

As a **non-technical user managing software projects**
I want to **interact with Project Orchestrator through a visual web interface with dedicated panels for navigation, chat, and monitoring**
So that **I can efficiently manage multiple projects, communicate with the AI assistant, and observe real-time development activity without juggling multiple tools**

## Problem Statement

The current Project Orchestrator relies on Telegram for chat and GitHub for project management, creating a fragmented experience. Users need to:
- Switch between Telegram and GitHub to manage projects
- Lack visibility into SCAR agent activities in real-time
- Cannot easily browse project documents or navigate issue hierarchies
- Miss important workflow updates when not actively checking multiple platforms

A unified web interface consolidates these workflows into a single, cohesive workspace with dedicated panels for each concern.

## Solution Statement

Build a React TypeScript web application with FastAPI backend that provides:
1. **Persistent WebSocket connections** for real-time bidirectional communication (chat + SCAR feed)
2. **Three resizable panels** using react-resizable-panels library (20%-40%-40% default split)
3. **REST API endpoints** for project/issue data, document retrieval, and project creation
4. **Database-backed state** leveraging existing PostgreSQL models
5. **Server-Sent Events (SSE)** for streaming SCAR output to the activity feed
6. **Document viewer** with reader-friendly formatting for vision docs and plans

## Feature Metadata

**Feature Type**: New Capability (Major)
**Estimated Complexity**: High
**Primary Systems Affected**: 
- Backend API (new endpoints)
- Database models (minor additions for WebSocket session tracking)
- Frontend (entirely new React application)
- Real-time communication layer (WebSocket + SSE)
**Dependencies**: 
- React 18+, TypeScript 5+
- react-resizable-panels (panel layout)
- react-markdown (document rendering)
- FastAPI WebSocket support (built-in)
- sse-starlette (Server-Sent Events)

---

## CONTEXT REFERENCES

### Relevant Codebase Files - IMPORTANT: YOU MUST READ THESE FILES BEFORE IMPLEMENTING!

**Backend Patterns:**
- `src/main.py` (lines 1-100) - FastAPI app initialization, middleware, lifespan management
- `src/config.py` (lines 1-60) - Configuration management with Pydantic Settings
- `src/database/models.py` (lines 1-200) - Database models: Project, ConversationMessage, WorkflowPhase, ApprovalGate
- `src/database/connection.py` (lines 1-80) - Async database session management pattern
- `src/services/workflow_orchestrator.py` (lines 1-150) - Service layer pattern for business logic
- `src/agent/orchestrator_agent.py` (lines 1-100) - PydanticAI agent integration pattern
- `src/integrations/telegram_bot.py` (lines 1-100) - Messaging interface pattern to mirror
- `src/integrations/github_client.py` - GitHub API integration pattern
- `tests/conftest.py` (lines 1-100) - Testing patterns with async fixtures

**Testing Patterns:**
- `tests/agent/test_orchestrator_agent.py` - Agent testing examples
- `tests/integrations/test_github_webhook.py` - Integration testing with FastAPI

### New Files to Create

**Backend:**
- `src/api/websocket.py` - WebSocket connection manager and endpoints
- `src/api/sse.py` - Server-Sent Events endpoints for SCAR activity feed
- `src/api/projects.py` - REST API endpoints for project/issue data
- `src/api/documents.py` - REST API endpoints for document retrieval
- `src/services/project_service.py` - Project data aggregation service
- `src/services/websocket_manager.py` - WebSocket session and broadcast management
- `src/services/scar_feed_service.py` - SCAR activity feed aggregation and streaming
- `tests/api/test_websocket.py` - WebSocket endpoint tests
- `tests/api/test_projects.py` - Project API endpoint tests
- `tests/services/test_websocket_manager.py` - WebSocket manager tests

**Frontend (new directory):**
- `frontend/package.json` - Node dependencies and scripts
- `frontend/tsconfig.json` - TypeScript configuration
- `frontend/vite.config.ts` - Vite build configuration
- `frontend/src/main.tsx` - React application entry point
- `frontend/src/App.tsx` - Root component with 3-panel layout
- `frontend/src/components/LeftPanel/ProjectNavigator.tsx` - Project tree component
- `frontend/src/components/MiddlePanel/ChatInterface.tsx` - Chat UI component
- `frontend/src/components/RightPanel/ScarActivityFeed.tsx` - SCAR feed component
- `frontend/src/services/websocket.ts` - WebSocket client service
- `frontend/src/services/api.ts` - REST API client service
- `frontend/src/hooks/useWebSocket.ts` - WebSocket React hook
- `frontend/src/hooks/useScarFeed.ts` - SSE connection hook for SCAR feed
- `frontend/src/types/project.ts` - TypeScript types for project data
- `frontend/src/types/message.ts` - TypeScript types for chat messages

### Relevant Documentation - YOU SHOULD READ THESE BEFORE IMPLEMENTING!

- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
  - Section: WebSocket endpoint definition and connection handling
  - Why: Required for implementing real-time chat interface

- [sse-starlette Documentation](https://github.com/sysid/sse-starlette)
  - Section: EventSourceResponse and ServerSentEvent usage
  - Why: Needed for streaming SCAR activity feed

- [react-resizable-panels](https://github.com/bvaughn/react-resizable-panels)
  - Section: Panel, PanelGroup, PanelResizeHandle components
  - Why: Core layout implementation for 3-panel interface

- [react-markdown](https://remarkjs.github.io/react-markdown/)
  - Section: Component usage and custom renderers
  - Why: Document rendering with reader-friendly formatting

- [Vite React TypeScript Guide](https://vitejs.dev/guide/)
  - Section: Project setup and build configuration
  - Why: Frontend build tooling setup

### Patterns to Follow

**Naming Conventions:**
```python
# Backend files: snake_case
src/api/websocket.py
src/services/project_service.py

# Backend classes: PascalCase
class WebSocketManager:
class ProjectService:

# Backend functions: snake_case
async def get_projects_with_issues():
async def broadcast_message():
```

**Error Handling Pattern:**
```python
# From src/database/connection.py
async with async_session_maker() as session:
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
```

**Logging Pattern:**
```python
# From src/main.py
import logging
logger = logging.getLogger(__name__)
logger.info("Application startup complete")
logger.error(f"Error: {error_message}")
```

**FastAPI Dependency Injection:**
```python
# From src/database/connection.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

async def endpoint(session: AsyncSession = Depends(get_session)):
    # Use session
    pass
```

**Frontend TypeScript Conventions:**
```typescript
// Components: PascalCase
export const ProjectNavigator: React.FC = () => {}

// Hooks: camelCase starting with 'use'
export const useWebSocket = (url: string) => {}

// Types/Interfaces: PascalCase
interface Project {
  id: string;
  name: string;
}

// Files: kebab-case
project-navigator.tsx
use-websocket.ts
```

---

## IMPLEMENTATION PLAN

### Phase 1: Backend Foundation - REST API & Database Extensions

Establish REST API endpoints for project/issue data retrieval and document access. Extend database models if needed for WebSocket session tracking.

**Tasks:**
- Create REST API router structure following existing patterns
- Implement project service layer for data aggregation
- Add API endpoints for project list, issue hierarchy, document retrieval
- Extend configuration for frontend serving and CORS

### Phase 2: Real-Time Communication - WebSocket & SSE

Implement WebSocket infrastructure for bidirectional chat communication and Server-Sent Events for one-way SCAR activity streaming.

**Tasks:**
- Create WebSocket connection manager for session tracking
- Implement WebSocket endpoints for chat messaging
- Integrate chat messages with existing conversation storage
- Create SSE endpoint for SCAR activity feed streaming
- Implement SCAR feed service to aggregate and format activity logs

### Phase 3: Frontend Setup - React TypeScript Application

Initialize React TypeScript application with Vite, establish project structure, and configure development environment.

**Tasks:**
- Initialize Vite + React + TypeScript project in frontend/ directory
- Configure TypeScript strict mode and path aliases
- Set up ESLint and Prettier for code quality
- Create base component structure and routing (if needed)
- Configure API and WebSocket base URLs for development/production

### Phase 4: Core UI - 3-Panel Resizable Layout

Build the three-panel layout using react-resizable-panels with proper state persistence and responsive behavior.

**Tasks:**
- Implement PanelGroup with horizontal orientation
- Create three Panel components with default 20%-40%-40% sizing
- Add PanelResizeHandle between panels
- Implement panel size persistence to localStorage
- Add responsive behavior for mobile/tablet viewports

### Phase 5: Left Panel - Project Navigator

Build the project tree navigator with expand/collapse, issue filtering, and document discovery.

**Tasks:**
- Fetch project data from REST API
- Implement tree structure with expandable nodes
- Add "+" button for quick project creation modal
- Implement issue grouping (open vs closed folders)
- Add document discovery and linking (open in new tab)

### Phase 6: Middle Panel - Chat Interface

Create the chat interface with WebSocket connection, message display, and conversation history.

**Tasks:**
- Implement WebSocket connection with automatic reconnection
- Create message list component with auto-scroll
- Add input field with Enter-to-send functionality
- Display conversation history from API on mount
- Handle connection status indicators (connected/disconnected)

### Phase 7: Right Panel - SCAR Activity Feed

Build real-time activity feed using SSE to stream SCAR communications with configurable verbosity.

**Tasks:**
- Implement SSE connection using EventSource API
- Create activity log display with color-coded message types
- Add verbosity control (slider/dropdown: Low/Medium/High)
- Implement tabbed view for multiple concurrent phases
- Add auto-scroll with pause-on-scroll-up behavior

### Phase 8: Document Viewer Integration

Implement reader-friendly document rendering for vision docs and plans opened from the project navigator.

**Tasks:**
- Create document viewer component with react-markdown
- Apply reader-friendly CSS styling (typography, spacing, max-width)
- Implement syntax highlighting for code blocks
- Add support for opening documents in new browser tab
- Handle markdown formatting for headers, lists, tables

### Phase 9: Integration & Polish

Connect all components, add error handling, loading states, and polish the user experience.

**Tasks:**
- Add loading skeletons for async data
- Implement error boundaries for graceful failure handling
- Add toast notifications for user feedback
- Implement context-aware chat (reflect selected project in left panel)
- Add keyboard shortcuts (Ctrl+K for quick project search, etc.)
- Configure production build and deployment to po.153.se

### Phase 10: Testing & Validation

Comprehensive testing of all components, API endpoints, and real-time features.

**Tasks:**
- Write unit tests for backend API endpoints
- Write unit tests for WebSocket manager
- Write integration tests for SSE streaming
- Add frontend component tests with React Testing Library
- Perform end-to-end testing of complete workflow
- Load testing for WebSocket and SSE connections

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute every task in order, top to bottom. Each task is atomic and independently testable.

### CREATE src/api/projects.py

- **IMPLEMENT**: REST API router for project and issue data endpoints
- **PATTERN**: Mirror routing structure from `src/main.py` (lines 60-100)
- **IMPORTS**: 
  ```python
  from fastapi import APIRouter, Depends, HTTPException
  from sqlalchemy.ext.asyncio import AsyncSession
  from src.database.connection import get_session
  from src.database.models import Project, ProjectStatus
  from sqlalchemy import select
  from typing import List, Optional
  from pydantic import BaseModel
  from uuid import UUID
  ```
- **ENDPOINTS**:
  - `GET /api/projects` - List all projects with issue counts
  - `GET /api/projects/{project_id}` - Get single project details
  - `GET /api/projects/{project_id}/issues` - Get issues for project (if using GitHub integration)
  - `POST /api/projects` - Create new project
- **GOTCHA**: Use async session from dependency injection, follow existing session management pattern
- **VALIDATE**: `uv run python -c "from src.api.projects import router; print('✓ Projects API router imports valid')"`

### CREATE src/services/project_service.py

- **IMPLEMENT**: Service layer for project data aggregation and business logic
- **PATTERN**: Mirror service structure from `src/services/workflow_orchestrator.py` (lines 1-150)
- **IMPORTS**:
  ```python
  from sqlalchemy.ext.asyncio import AsyncSession
  from sqlalchemy import select, func
  from src.database.models import Project, ConversationMessage, WorkflowPhase
  from typing import List, Dict, Optional
  from uuid import UUID
  from pydantic import BaseModel
  ```
- **FUNCTIONS**:
  - `async def get_all_projects(session: AsyncSession) -> List[Dict]`
  - `async def get_project_with_stats(session: AsyncSession, project_id: UUID) -> Dict`
  - `async def create_project(session: AsyncSession, name: str, description: Optional[str]) -> Project`
- **GOTCHA**: Use `session.execute()` then `.scalars().all()` pattern for queries
- **VALIDATE**: `uv run python -c "from src.services.project_service import get_all_projects; print('✓ Project service imports valid')"`

### CREATE src/api/documents.py

- **IMPLEMENT**: REST API router for document retrieval (vision docs, plans)
- **PATTERN**: Follow FastAPI router pattern from `src/api/projects.py`
- **IMPORTS**:
  ```python
  from fastapi import APIRouter, Depends, HTTPException, Response
  from fastapi.responses import PlainTextResponse
  from sqlalchemy.ext.asyncio import AsyncSession
  from src.database.connection import get_session
  from src.database.models import Project
  from pathlib import Path
  import json
  ```
- **ENDPOINTS**:
  - `GET /api/documents/vision/{project_id}` - Get vision document as markdown
  - `GET /api/documents/plans/{project_id}` - Get implementation plans
  - `GET /api/documents/list/{project_id}` - List all available documents for project
- **GOTCHA**: Vision documents stored as JSONB in `Project.vision_document`, convert to markdown
- **VALIDATE**: `uv run python -c "from src.api.documents import router; print('✓ Documents API router imports valid')"`

### CREATE src/services/websocket_manager.py

- **IMPLEMENT**: WebSocket connection manager for tracking active sessions and broadcasting
- **PATTERN**: Use Python dict for in-memory connection tracking (simple MVP approach)
- **IMPORTS**:
  ```python
  from fastapi import WebSocket
  from typing import Dict, List, Optional
  from uuid import UUID
  import logging
  import json
  from datetime import datetime
  ```
- **CLASS**: `WebSocketManager`
  - `active_connections: Dict[str, WebSocket]` - Map connection_id to websocket
  - `async def connect(connection_id: str, websocket: WebSocket) -> None`
  - `async def disconnect(connection_id: str) -> None`
  - `async def send_personal_message(message: dict, connection_id: str) -> None`
  - `async def broadcast(message: dict) -> None`
- **GOTCHA**: Handle WebSocket exceptions gracefully, auto-remove dead connections
- **VALIDATE**: `uv run python -c "from src.services.websocket_manager import WebSocketManager; print('✓ WebSocket manager imports valid')"`

### CREATE src/api/websocket.py

- **IMPLEMENT**: WebSocket endpoint for bidirectional chat communication
- **PATTERN**: Follow FastAPI WebSocket pattern from official docs
- **IMPORTS**:
  ```python
  from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
  from sqlalchemy.ext.asyncio import AsyncSession
  from src.database.connection import get_session
  from src.services.websocket_manager import WebSocketManager
  from src.agent.orchestrator_agent import run_orchestrator
  from src.database.models import MessageRole, Project
  from uuid import UUID
  import logging
  import json
  ```
- **ENDPOINT**: `WebSocket /api/ws/chat/{project_id}`
  - Accept WebSocket connection
  - Register in WebSocketManager
  - Listen for incoming messages (user chat)
  - Run orchestrator agent on user messages
  - Send agent responses back to client
  - Handle disconnection cleanup
- **GOTCHA**: Use `async with get_session() as session:` inside websocket loop for each message
- **VALIDATE**: Start server and test with wscat: `wscat -c ws://localhost:8000/api/ws/chat/{uuid}`

### CREATE src/services/scar_feed_service.py

- **IMPLEMENT**: Service to aggregate SCAR activity logs and format for streaming
- **PATTERN**: Mirror service pattern from `src/services/workflow_orchestrator.py`
- **IMPORTS**:
  ```python
  from sqlalchemy.ext.asyncio import AsyncSession
  from sqlalchemy import select, desc
  from src.database.models import ScarCommandExecution, WorkflowPhase, Project
  from typing import List, Dict, AsyncGenerator
  from uuid import UUID
  from datetime import datetime
  import json
  ```
- **FUNCTIONS**:
  - `async def get_recent_scar_activity(session: AsyncSession, project_id: UUID, limit: int = 50) -> List[Dict]`
  - `async def stream_scar_activity(session: AsyncSession, project_id: UUID) -> AsyncGenerator[Dict, None]`
- **GOTCHA**: Query `ScarCommandExecution` table (see `src/database/models.py`), format output as structured JSON
- **VALIDATE**: `uv run python -c "from src.services.scar_feed_service import get_recent_scar_activity; print('✓ SCAR feed service imports valid')"`

### CREATE src/api/sse.py

- **IMPLEMENT**: Server-Sent Events endpoint for streaming SCAR activity feed
- **PATTERN**: Use sse-starlette library (add to dependencies)
- **IMPORTS**:
  ```python
  from fastapi import APIRouter, Depends
  from sse_starlette.sse import EventSourceResponse
  from sqlalchemy.ext.asyncio import AsyncSession
  from src.database.connection import get_session
  from src.services.scar_feed_service import stream_scar_activity
  from uuid import UUID
  import asyncio
  import json
  ```
- **ENDPOINT**: `GET /api/sse/scar/{project_id}`
  - Return EventSourceResponse with async generator
  - Stream SCAR activity updates every 2 seconds
  - Include heartbeat ping every 30 seconds to keep connection alive
- **GOTCHA**: SSE requires `Content-Type: text/event-stream`, sse-starlette handles this
- **VALIDATE**: Start server and test with curl: `curl -N http://localhost:8000/api/sse/scar/{uuid}`

### UPDATE src/main.py

- **IMPLEMENT**: Register new API routers (projects, documents, websocket, sse)
- **PATTERN**: Follow existing router registration at end of `src/main.py`
- **IMPORTS**:
  ```python
  from src.api.projects import router as projects_router
  from src.api.documents import router as documents_router
  from src.api.websocket import router as websocket_router
  from src.api.sse import router as sse_router
  ```
- **REGISTRATION**:
  ```python
  app.include_router(projects_router, prefix="/api", tags=["Projects"])
  app.include_router(documents_router, prefix="/api", tags=["Documents"])
  app.include_router(websocket_router, prefix="/api", tags=["WebSocket"])
  app.include_router(sse_router, prefix="/api", tags=["SSE"])
  ```
- **ADD CORS**: Update CORS middleware to allow frontend origin (e.g., `http://localhost:5173` for Vite dev server)
- **GOTCHA**: Preserve existing import order for any side-effect imports (no side-effects here, safe to add at end)
- **VALIDATE**: `uv run python -m src.main` (server should start without errors)

### UPDATE pyproject.toml

- **IMPLEMENT**: Add sse-starlette dependency
- **ADD DEPENDENCY**:
  ```toml
  dependencies = [
      # ... existing dependencies ...
      "sse-starlette>=2.1.0",  # Server-Sent Events
  ]
  ```
- **VALIDATE**: `uv sync && uv run python -c "import sse_starlette; print('✓ sse-starlette installed')"`

### CREATE frontend/package.json

- **IMPLEMENT**: Initialize Node.js project with React, TypeScript, Vite dependencies
- **CONTENT**:
  ```json
  {
    "name": "project-orchestrator-frontend",
    "version": "0.1.0",
    "type": "module",
    "scripts": {
      "dev": "vite",
      "build": "tsc && vite build",
      "preview": "vite preview",
      "lint": "eslint src --ext ts,tsx",
      "format": "prettier --write src"
    },
    "dependencies": {
      "react": "^18.2.0",
      "react-dom": "^18.2.0",
      "react-resizable-panels": "^2.0.0",
      "react-markdown": "^9.0.0",
      "remark-gfm": "^4.0.0",
      "react-syntax-highlighter": "^15.5.0"
    },
    "devDependencies": {
      "@types/react": "^18.2.0",
      "@types/react-dom": "^18.2.0",
      "@types/react-syntax-highlighter": "^15.5.0",
      "@typescript-eslint/eslint-plugin": "^6.0.0",
      "@typescript-eslint/parser": "^6.0.0",
      "@vitejs/plugin-react": "^4.2.0",
      "eslint": "^8.56.0",
      "eslint-plugin-react-hooks": "^4.6.0",
      "prettier": "^3.2.0",
      "typescript": "^5.3.0",
      "vite": "^5.0.0"
    }
  }
  ```
- **VALIDATE**: `cd frontend && npm install && npm run build`

### CREATE frontend/tsconfig.json

- **IMPLEMENT**: TypeScript configuration with strict mode and path aliases
- **CONTENT**:
  ```json
  {
    "compilerOptions": {
      "target": "ES2020",
      "useDefineForClassFields": true,
      "lib": ["ES2020", "DOM", "DOM.Iterable"],
      "module": "ESNext",
      "skipLibCheck": true,
      "moduleResolution": "bundler",
      "allowImportingTsExtensions": true,
      "resolveJsonModule": true,
      "isolatedModules": true,
      "noEmit": true,
      "jsx": "react-jsx",
      "strict": true,
      "noUnusedLocals": true,
      "noUnusedParameters": true,
      "noFallthroughCasesInSwitch": true,
      "baseUrl": ".",
      "paths": {
        "@/*": ["./src/*"]
      }
    },
    "include": ["src"],
    "references": [{ "path": "./tsconfig.node.json" }]
  }
  ```
- **VALIDATE**: `cd frontend && npx tsc --noEmit`

### CREATE frontend/vite.config.ts

- **IMPLEMENT**: Vite build configuration with React plugin and proxy
- **CONTENT**:
  ```typescript
  import { defineConfig } from 'vite'
  import react from '@vitejs/plugin-react'
  import path from 'path'
  
  export default defineConfig({
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      port: 5173,
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
  })
  ```
- **VALIDATE**: `cd frontend && npm run dev` (dev server should start on port 5173)

### CREATE frontend/src/types/project.ts

- **IMPLEMENT**: TypeScript type definitions for project data
- **CONTENT**:
  ```typescript
  export interface Project {
    id: string;
    name: string;
    description?: string;
    status: ProjectStatus;
    github_repo_url?: string;
    telegram_chat_id?: number;
    created_at: string;
    updated_at: string;
    open_issues_count?: number;
    closed_issues_count?: number;
  }
  
  export enum ProjectStatus {
    BRAINSTORMING = 'BRAINSTORMING',
    VISION_REVIEW = 'VISION_REVIEW',
    PLANNING = 'PLANNING',
    IN_PROGRESS = 'IN_PROGRESS',
    PAUSED = 'PAUSED',
    COMPLETED = 'COMPLETED',
  }
  
  export interface Issue {
    number: number;
    title: string;
    state: 'open' | 'closed';
    created_at: string;
  }
  
  export interface Document {
    id: string;
    name: string;
    type: 'vision' | 'plan' | 'other';
    url: string;
  }
  ```
- **VALIDATE**: `cd frontend && npx tsc --noEmit`

### CREATE frontend/src/types/message.ts

- **IMPLEMENT**: TypeScript type definitions for chat messages
- **CONTENT**:
  ```typescript
  export interface ChatMessage {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: string;
  }
  
  export interface WebSocketMessage {
    type: 'chat' | 'status' | 'error';
    data: ChatMessage | StatusUpdate | ErrorMessage;
  }
  
  export interface StatusUpdate {
    status: 'connected' | 'disconnected' | 'reconnecting';
    message?: string;
  }
  
  export interface ErrorMessage {
    code: string;
    message: string;
  }
  ```
- **VALIDATE**: `cd frontend && npx tsc --noEmit`

### CREATE frontend/src/services/api.ts

- **IMPLEMENT**: REST API client service using fetch
- **CONTENT**:
  ```typescript
  import { Project, Issue, Document } from '@/types/project';
  
  const API_BASE_URL = '/api';
  
  export const api = {
    // Projects
    getProjects: async (): Promise<Project[]> => {
      const response = await fetch(`${API_BASE_URL}/projects`);
      if (!response.ok) throw new Error('Failed to fetch projects');
      return response.json();
    },
    
    getProject: async (projectId: string): Promise<Project> => {
      const response = await fetch(`${API_BASE_URL}/projects/${projectId}`);
      if (!response.ok) throw new Error('Failed to fetch project');
      return response.json();
    },
    
    createProject: async (name: string, description?: string): Promise<Project> => {
      const response = await fetch(`${API_BASE_URL}/projects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, description }),
      });
      if (!response.ok) throw new Error('Failed to create project');
      return response.json();
    },
    
    // Documents
    getVisionDocument: async (projectId: string): Promise<string> => {
      const response = await fetch(`${API_BASE_URL}/documents/vision/${projectId}`);
      if (!response.ok) throw new Error('Failed to fetch vision document');
      return response.text();
    },
    
    listDocuments: async (projectId: string): Promise<Document[]> => {
      const response = await fetch(`${API_BASE_URL}/documents/list/${projectId}`);
      if (!response.ok) throw new Error('Failed to fetch documents');
      return response.json();
    },
  };
  ```
- **VALIDATE**: `cd frontend && npx tsc --noEmit`

### CREATE frontend/src/hooks/useWebSocket.ts

- **IMPLEMENT**: React hook for WebSocket connection management
- **CONTENT**:
  ```typescript
  import { useEffect, useRef, useState } from 'react';
  import { ChatMessage, WebSocketMessage } from '@/types/message';
  
  export const useWebSocket = (projectId: string) => {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [isConnected, setIsConnected] = useState(false);
    const wsRef = useRef<WebSocket | null>(null);
  
    useEffect(() => {
      const wsUrl = `ws://localhost:8000/api/ws/chat/${projectId}`;
      const ws = new WebSocket(wsUrl);
  
      ws.onopen = () => {
        setIsConnected(true);
        console.log('WebSocket connected');
      };
  
      ws.onmessage = (event) => {
        const wsMessage: WebSocketMessage = JSON.parse(event.data);
        if (wsMessage.type === 'chat') {
          setMessages((prev) => [...prev, wsMessage.data as ChatMessage]);
        }
      };
  
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
  
      ws.onclose = () => {
        setIsConnected(false);
        console.log('WebSocket disconnected');
      };
  
      wsRef.current = ws;
  
      return () => {
        ws.close();
      };
    }, [projectId]);
  
    const sendMessage = (content: string) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ content }));
      }
    };
  
    return { messages, isConnected, sendMessage };
  };
  ```
- **VALIDATE**: `cd frontend && npx tsc --noEmit`

### CREATE frontend/src/hooks/useScarFeed.ts

- **IMPLEMENT**: React hook for SSE connection to SCAR activity feed
- **CONTENT**:
  ```typescript
  import { useEffect, useState } from 'react';
  
  export interface ScarActivity {
    id: string;
    timestamp: string;
    source: 'po' | 'scar' | 'claude';
    message: string;
    phase?: string;
  }
  
  export const useScarFeed = (projectId: string) => {
    const [activities, setActivities] = useState<ScarActivity[]>([]);
    const [isConnected, setIsConnected] = useState(false);
  
    useEffect(() => {
      const eventSource = new EventSource(`/api/sse/scar/${projectId}`);
  
      eventSource.onopen = () => {
        setIsConnected(true);
        console.log('SSE connected');
      };
  
      eventSource.onmessage = (event) => {
        const activity: ScarActivity = JSON.parse(event.data);
        setActivities((prev) => [...prev, activity]);
      };
  
      eventSource.onerror = (error) => {
        console.error('SSE error:', error);
        setIsConnected(false);
      };
  
      return () => {
        eventSource.close();
      };
    }, [projectId]);
  
    return { activities, isConnected };
  };
  ```
- **VALIDATE**: `cd frontend && npx tsc --noEmit`

### CREATE frontend/src/components/LeftPanel/ProjectNavigator.tsx

- **IMPLEMENT**: Project tree navigator component
- **CONTENT**:
  ```typescript
  import React, { useEffect, useState } from 'react';
  import { api } from '@/services/api';
  import { Project } from '@/types/project';
  
  interface ProjectNavigatorProps {
    onProjectSelect: (projectId: string) => void;
  }
  
  export const ProjectNavigator: React.FC<ProjectNavigatorProps> = ({ onProjectSelect }) => {
    const [projects, setProjects] = useState<Project[]>([]);
    const [expandedProjects, setExpandedProjects] = useState<Set<string>>(new Set());
    const [loading, setLoading] = useState(true);
  
    useEffect(() => {
      const fetchProjects = async () => {
        try {
          const data = await api.getProjects();
          setProjects(data);
        } catch (error) {
          console.error('Failed to fetch projects:', error);
        } finally {
          setLoading(false);
        }
      };
      fetchProjects();
    }, []);
  
    const toggleProject = (projectId: string) => {
      setExpandedProjects((prev) => {
        const next = new Set(prev);
        if (next.has(projectId)) {
          next.delete(projectId);
        } else {
          next.add(projectId);
        }
        return next;
      });
    };
  
    if (loading) return <div>Loading projects...</div>;
  
    return (
      <div className="project-navigator">
        <div className="header">
          <h2>Projects</h2>
          <button onClick={() => {/* TODO: open create modal */}}>+</button>
        </div>
        <ul className="project-list">
          {projects.map((project) => (
            <li key={project.id}>
              <div onClick={() => toggleProject(project.id)}>
                {expandedProjects.has(project.id) ? '▼' : '▶'} {project.name}
              </div>
              {expandedProjects.has(project.id) && (
                <ul className="issue-list">
                  <li>Open Issues ({project.open_issues_count || 0})</li>
                  <li>Closed Issues ({project.closed_issues_count || 0})</li>
                  <li>Documents</li>
                </ul>
              )}
            </li>
          ))}
        </ul>
      </div>
    );
  };
  ```
- **VALIDATE**: `cd frontend && npx tsc --noEmit`

### CREATE frontend/src/components/MiddlePanel/ChatInterface.tsx

- **IMPLEMENT**: Chat interface component with WebSocket integration
- **CONTENT**:
  ```typescript
  import React, { useState, useRef, useEffect } from 'react';
  import { useWebSocket } from '@/hooks/useWebSocket';
  
  interface ChatInterfaceProps {
    projectId: string;
  }
  
  export const ChatInterface: React.FC<ChatInterfaceProps> = ({ projectId }) => {
    const { messages, isConnected, sendMessage } = useWebSocket(projectId);
    const [input, setInput] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);
  
    useEffect(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);
  
    const handleSend = () => {
      if (input.trim()) {
        sendMessage(input);
        setInput('');
      }
    };
  
    const handleKeyPress = (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    };
  
    return (
      <div className="chat-interface">
        <div className="chat-header">
          <h2>Chat with @po</h2>
          <span className={`status ${isConnected ? 'connected' : 'disconnected'}`}>
            {isConnected ? '● Connected' : '○ Disconnected'}
          </span>
        </div>
        <div className="messages">
          {messages.map((msg) => (
            <div key={msg.id} className={`message ${msg.role}`}>
              <div className="role">{msg.role}</div>
              <div className="content">{msg.content}</div>
              <div className="timestamp">{new Date(msg.timestamp).toLocaleTimeString()}</div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
        <div className="input-area">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Message @po..."
            rows={3}
          />
          <button onClick={handleSend} disabled={!isConnected}>Send</button>
        </div>
      </div>
    );
  };
  ```
- **VALIDATE**: `cd frontend && npx tsc --noEmit`

### CREATE frontend/src/components/RightPanel/ScarActivityFeed.tsx

- **IMPLEMENT**: SCAR activity feed component with SSE integration
- **CONTENT**:
  ```typescript
  import React, { useState, useRef, useEffect } from 'react';
  import { useScarFeed } from '@/hooks/useScarFeed';
  
  interface ScarActivityFeedProps {
    projectId: string;
  }
  
  export const ScarActivityFeed: React.FC<ScarActivityFeedProps> = ({ projectId }) => {
    const { activities, isConnected } = useScarFeed(projectId);
    const [verbosity, setVerbosity] = useState<'low' | 'medium' | 'high'>('medium');
    const activitiesEndRef = useRef<HTMLDivElement>(null);
  
    useEffect(() => {
      activitiesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [activities]);
  
    const getSourceColor = (source: string) => {
      switch (source) {
        case 'po': return '#4CAF50';
        case 'scar': return '#2196F3';
        case 'claude': return '#FF9800';
        default: return '#999';
      }
    };
  
    return (
      <div className="scar-feed">
        <div className="feed-header">
          <h2>SCAR Activity</h2>
          <select value={verbosity} onChange={(e) => setVerbosity(e.target.value as any)}>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
          <span className={`status ${isConnected ? 'connected' : 'disconnected'}`}>
            {isConnected ? '● Live' : '○ Disconnected'}
          </span>
        </div>
        <div className="activities">
          {activities.map((activity) => (
            <div key={activity.id} className="activity-item">
              <span className="source" style={{ color: getSourceColor(activity.source) }}>
                [{activity.source}]
              </span>
              <span className="timestamp">
                {new Date(activity.timestamp).toLocaleTimeString()}
              </span>
              <div className="message">{activity.message}</div>
              {activity.phase && <div className="phase">Phase: {activity.phase}</div>}
            </div>
          ))}
          <div ref={activitiesEndRef} />
        </div>
      </div>
    );
  };
  ```
- **VALIDATE**: `cd frontend && npx tsc --noEmit`

### CREATE frontend/src/App.tsx

- **IMPLEMENT**: Root component with 3-panel resizable layout
- **CONTENT**:
  ```typescript
  import React, { useState } from 'react';
  import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
  import { ProjectNavigator } from '@/components/LeftPanel/ProjectNavigator';
  import { ChatInterface } from '@/components/MiddlePanel/ChatInterface';
  import { ScarActivityFeed } from '@/components/RightPanel/ScarActivityFeed';
  import './App.css';
  
  function App() {
    const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  
    return (
      <div className="app">
        <PanelGroup direction="horizontal">
          <Panel defaultSize={20} minSize={15} maxSize={40}>
            <ProjectNavigator onProjectSelect={setSelectedProjectId} />
          </Panel>
          <PanelResizeHandle className="resize-handle" />
          <Panel defaultSize={40} minSize={30}>
            {selectedProjectId ? (
              <ChatInterface projectId={selectedProjectId} />
            ) : (
              <div className="empty-state">Select a project to start chatting</div>
            )}
          </Panel>
          <PanelResizeHandle className="resize-handle" />
          <Panel defaultSize={40} minSize={30}>
            {selectedProjectId ? (
              <ScarActivityFeed projectId={selectedProjectId} />
            ) : (
              <div className="empty-state">Select a project to view activity</div>
            )}
          </Panel>
        </PanelGroup>
      </div>
    );
  }
  
  export default App;
  ```
- **VALIDATE**: `cd frontend && npx tsc --noEmit`

### CREATE frontend/src/main.tsx

- **IMPLEMENT**: React application entry point
- **CONTENT**:
  ```typescript
  import React from 'react';
  import ReactDOM from 'react-dom/client';
  import App from './App';
  import './index.css';
  
  ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
  );
  ```
- **VALIDATE**: `cd frontend && npx tsc --noEmit`

### CREATE frontend/src/App.css

- **IMPLEMENT**: Base styles for 3-panel layout
- **CONTENT**:
  ```css
  .app {
    height: 100vh;
    width: 100vw;
    overflow: hidden;
  }
  
  .resize-handle {
    width: 8px;
    background: #e0e0e0;
    cursor: col-resize;
    transition: background 0.2s;
  }
  
  .resize-handle:hover {
    background: #bdbdbd;
  }
  
  .project-navigator,
  .chat-interface,
  .scar-feed {
    height: 100%;
    display: flex;
    flex-direction: column;
    padding: 1rem;
    overflow: hidden;
  }
  
  .empty-state {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #999;
    font-size: 1.1rem;
  }
  
  .status.connected {
    color: #4CAF50;
  }
  
  .status.disconnected {
    color: #f44336;
  }
  ```
- **VALIDATE**: `cd frontend && npm run build`

### CREATE frontend/index.html

- **IMPLEMENT**: HTML entry point for Vite
- **CONTENT**:
  ```html
  <!DOCTYPE html>
  <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <title>Project Orchestrator</title>
    </head>
    <body>
      <div id="root"></div>
      <script type="module" src="/src/main.tsx"></script>
    </body>
  </html>
  ```
- **VALIDATE**: `cd frontend && npm run dev`

### UPDATE src/config.py

- **IMPLEMENT**: Add configuration for frontend serving and CORS origins
- **ADD SETTINGS**:
  ```python
  # Frontend
  frontend_url: str = "http://localhost:5173"  # Vite dev server
  serve_frontend: bool = False  # Set to True in production
  ```
- **VALIDATE**: `uv run python -c "from src.config import settings; print(f'✓ Frontend URL: {settings.frontend_url}')"`

### CREATE tests/api/test_projects.py

- **IMPLEMENT**: Unit tests for project API endpoints
- **PATTERN**: Mirror test structure from `tests/integrations/test_github_webhook.py`
- **IMPORTS**:
  ```python
  import pytest
  from httpx import AsyncClient
  from sqlalchemy.ext.asyncio import AsyncSession
  from src.database.models import Project, ProjectStatus
  ```
- **TESTS**:
  - `test_get_projects_empty`
  - `test_get_projects_with_data`
  - `test_get_project_by_id`
  - `test_create_project`
  - `test_get_project_not_found`
- **VALIDATE**: `uv run pytest tests/api/test_projects.py -v`

### CREATE tests/api/test_websocket.py

- **IMPLEMENT**: Integration tests for WebSocket chat endpoint
- **PATTERN**: Use FastAPI TestClient with WebSocket support
- **IMPORTS**:
  ```python
  import pytest
  from fastapi.testclient import TestClient
  from src.main import app
  from uuid import uuid4
  ```
- **TESTS**:
  - `test_websocket_connect`
  - `test_websocket_send_receive`
  - `test_websocket_disconnect`
- **GOTCHA**: Use synchronous TestClient for WebSocket testing (AsyncClient doesn't support WebSocket)
- **VALIDATE**: `uv run pytest tests/api/test_websocket.py -v`

### CREATE tests/services/test_websocket_manager.py

- **IMPLEMENT**: Unit tests for WebSocket manager
- **PATTERN**: Test connection tracking, broadcasting, cleanup
- **IMPORTS**:
  ```python
  import pytest
  from unittest.mock import AsyncMock, MagicMock
  from src.services.websocket_manager import WebSocketManager
  ```
- **TESTS**:
  - `test_connect`
  - `test_disconnect`
  - `test_broadcast`
  - `test_send_personal_message`
- **VALIDATE**: `uv run pytest tests/services/test_websocket_manager.py -v`

### CREATE docker-compose.override.yml

- **IMPLEMENT**: Docker Compose override for frontend development
- **CONTENT**:
  ```yaml
  version: '3.8'
  
  services:
    frontend:
      build:
        context: ./frontend
        dockerfile: Dockerfile.dev
      ports:
        - "5173:5173"
      volumes:
        - ./frontend:/app
        - /app/node_modules
      environment:
        - VITE_API_URL=http://localhost:8000
      depends_on:
        - app
  ```
- **VALIDATE**: `docker-compose -f docker-compose.yml -f docker-compose.override.yml config`

### CREATE frontend/Dockerfile.dev

- **IMPLEMENT**: Dockerfile for frontend development container
- **CONTENT**:
  ```dockerfile
  FROM node:20-alpine
  
  WORKDIR /app
  
  COPY package*.json ./
  RUN npm install
  
  COPY . .
  
  EXPOSE 5173
  
  CMD ["npm", "run", "dev", "--", "--host"]
  ```
- **VALIDATE**: `docker build -f frontend/Dockerfile.dev -t po-frontend:dev frontend/`

### UPDATE README.md

- **IMPLEMENT**: Add WebUI documentation section
- **ADD SECTION**:
  ```markdown
  ## Web Interface
  
  Access the web UI at http://localhost:5173 (development) or http://po.153.se (production).
  
  ### Features
  - **Left Panel**: Project navigator with expandable issue trees
  - **Middle Panel**: Chat interface with @po (no @mention required)
  - **Right Panel**: Real-time SCAR activity feed
  
  ### Development
  
  Start the frontend dev server:
  ```bash
  cd frontend
  npm install
  npm run dev
  ```
  
  Start the backend:
  ```bash
  uv run python -m src.main
  ```
  ```
- **VALIDATE**: `cat README.md | grep "Web Interface" && echo "✓ README updated"`

---

## TESTING STRATEGY

### Unit Tests

**Backend API Endpoints:**
- Test all REST endpoints with valid/invalid inputs
- Verify proper error handling and HTTP status codes
- Test authentication/authorization if implemented

**Backend Services:**
- Test WebSocketManager connection lifecycle
- Test project service data aggregation
- Test SCAR feed service formatting

**Frontend Components:**
- Test ProjectNavigator rendering and interactions
- Test ChatInterface message display and input
- Test ScarActivityFeed filtering by verbosity
- Test hooks (useWebSocket, useScarFeed) with mocks

### Integration Tests

**WebSocket Communication:**
- Test full chat flow: connect → send → receive → disconnect
- Test multiple concurrent connections
- Test reconnection logic

**SSE Streaming:**
- Test SSE connection establishment
- Test streaming multiple events
- Test connection cleanup on client disconnect

**End-to-End Workflow:**
- User selects project → chat loads → messages sent/received
- User changes verbosity → SCAR feed filters correctly
- User creates project → appears in navigator immediately

### Edge Cases

**Network Failures:**
- WebSocket disconnects mid-chat
- SSE connection drops and reconnects
- API requests timeout

**State Management:**
- Multiple tabs open (shared state via database)
- Project deleted while viewing
- Rapid project switching

**Performance:**
- 100+ projects in navigator
- 1000+ messages in chat history
- High-frequency SCAR activity updates

---

## VALIDATION COMMANDS

Execute every command to ensure zero regressions and 100% feature correctness.

### Level 1: Import Validation (CRITICAL)

**Verify all backend imports resolve:**

```bash
uv run python -c "from src.api.projects import router; print('✓ Projects API valid')"
uv run python -c "from src.api.documents import router; print('✓ Documents API valid')"
uv run python -c "from src.api.websocket import router; print('✓ WebSocket API valid')"
uv run python -c "from src.api.sse import router; print('✓ SSE API valid')"
uv run python -c "from src.services.websocket_manager import WebSocketManager; print('✓ WebSocket manager valid')"
uv run python -c "from src.services.scar_feed_service import get_recent_scar_activity; print('✓ SCAR feed service valid')"
```

**Expected:** All print "✓" messages (no ModuleNotFoundError or ImportError)

**Why:** Catches incorrect imports immediately before running tests.

### Level 2: Syntax & Style

**Backend linting and type checking:**

```bash
uv run ruff check src/api/ src/services/
uv run mypy src/api/ src/services/
uv run black --check src/api/ src/services/
```

**Expected:** No errors, all checks pass

**Frontend linting and type checking:**

```bash
cd frontend
npm run lint
npx tsc --noEmit
npm run format -- --check
```

**Expected:** No errors, all checks pass

### Level 3: Unit Tests

**Backend unit tests:**

```bash
uv run pytest tests/api/ -v
uv run pytest tests/services/ -v
```

**Expected:** All tests pass, 0 failures

**Frontend unit tests (if implemented):**

```bash
cd frontend
npm test
```

**Expected:** All tests pass

### Level 4: Integration Tests

**Backend integration tests:**

```bash
uv run pytest tests/api/test_websocket.py -v
uv run pytest tests/ -v --cov=src --cov-report=term-missing
```

**Expected:** All tests pass, >80% coverage for new code

### Level 5: Manual Validation

**Backend server startup:**

```bash
uv run python -m src.main
```

**Expected:** Server starts without errors, logs show "Application startup complete"

**Frontend dev server:**

```bash
cd frontend
npm run dev
```

**Expected:** Vite dev server starts on port 5173, no compilation errors

**WebSocket connection test:**

```bash
# Install wscat if not available: npm install -g wscat
wscat -c ws://localhost:8000/api/ws/chat/00000000-0000-0000-0000-000000000001
# Send a message: {"content": "Hello"}
# Expected: Receive response from orchestrator agent
```

**SSE connection test:**

```bash
curl -N http://localhost:8000/api/sse/scar/00000000-0000-0000-0000-000000000001
# Expected: Stream of SCAR activity events (or empty stream if no activity)
```

**Browser testing:**

1. Open http://localhost:5173
2. Verify 3-panel layout renders correctly
3. Verify panels are resizable by dragging handles
4. Create a test project via "+" button
5. Select project and verify chat interface loads
6. Send a message and verify response appears
7. Verify SCAR activity feed updates in real-time
8. Test verbosity dropdown changes filtering
9. Verify document links open in new tab with reader-friendly formatting

### Level 6: Build Validation

**Frontend production build:**

```bash
cd frontend
npm run build
npm run preview
```

**Expected:** Build completes successfully, preview server runs without errors

**Docker build (if using containers):**

```bash
docker-compose -f docker-compose.yml -f docker-compose.override.yml build
docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d
```

**Expected:** All services start successfully, web UI accessible

---

## ACCEPTANCE CRITERIA

- [ ] Three resizable panels render correctly (20%-40%-40% default)
- [ ] Left panel displays all projects in tree structure
- [ ] Projects expand to show open/closed issue folders
- [ ] "+" button creates new project successfully
- [ ] Documents discoverable and open in new tab with reader-friendly formatting
- [ ] Middle panel chat interface connects via WebSocket
- [ ] Chat messages send and receive without @mentions
- [ ] Conversation history loads from database on project selection
- [ ] Chat displays connection status (connected/disconnected)
- [ ] Right panel connects via SSE for SCAR activity
- [ ] SCAR feed displays real-time updates from @po → SCAR → Claude
- [ ] Verbosity control filters activity detail (Low/Medium/High)
- [ ] Tabbed view supports multiple concurrent phases (if applicable)
- [ ] All API endpoints return correct data and status codes
- [ ] WebSocket handles reconnection gracefully
- [ ] SSE connection includes heartbeat to prevent timeout
- [ ] All validation commands pass with zero errors
- [ ] Frontend builds for production without errors
- [ ] Responsive design works on desktop (1920x1080 minimum)
- [ ] No console errors in browser developer tools
- [ ] Code follows existing project patterns and conventions
- [ ] Unit test coverage meets requirements (>80% for new code)
- [ ] Integration tests verify end-to-end workflows
- [ ] Documentation updated with WebUI setup instructions

---

## COMPLETION CHECKLIST

- [ ] All backend API endpoints implemented and tested
- [ ] WebSocket manager handles connections and broadcasting
- [ ] SSE endpoint streams SCAR activity correctly
- [ ] Frontend React application built with TypeScript
- [ ] Three resizable panels implemented with react-resizable-panels
- [ ] Project navigator fetches and displays data
- [ ] Chat interface connects and communicates via WebSocket
- [ ] SCAR activity feed connects and displays via SSE
- [ ] Document viewer renders markdown with reader-friendly styles
- [ ] All validation commands executed successfully
- [ ] Unit tests pass for backend and frontend
- [ ] Integration tests verify WebSocket and SSE flows
- [ ] Manual browser testing confirms all features work
- [ ] Production build completes without errors
- [ ] Code reviewed for quality and maintainability
- [ ] README updated with WebUI documentation
- [ ] Ready for deployment to po.153.se

---

## NOTES

### Design Decisions

**WebSocket vs SSE:**
- **WebSocket** chosen for chat (middle panel) due to bidirectional requirements (user sends, agent responds)
- **SSE** chosen for SCAR feed (right panel) due to one-way streaming from server (simpler, more efficient)

**Frontend Framework:**
- **React + TypeScript** chosen for type safety and component reusability
- **Vite** chosen over Create React App for faster builds and modern tooling

**Panel Library:**
- **react-resizable-panels** chosen over react-split-pane for better performance and simpler API

**State Management:**
- **Local component state** sufficient for MVP (no Redux/Zustand needed yet)
- **Database as source of truth** for all persistent data

### Trade-offs

**In-Memory WebSocket Manager:**
- Pro: Simple implementation for MVP
- Con: Doesn't scale across multiple server instances
- Future: Migrate to Redis-backed pub/sub for production scaling

**Document Viewer:**
- MVP: Markdown rendering with react-markdown (simple, fast)
- Future: Rich text editor for in-app editing (MDXEditor integration)

**Verbosity Filtering:**
- MVP: Client-side filtering (all data sent, filtered in browser)
- Future: Server-side filtering (reduce bandwidth)

### Future Enhancements

- **Authentication**: Add user login (currently assumes single-user deployment)
- **Multi-tenancy**: Support multiple users with project access control
- **Keyboard shortcuts**: Cmd+K quick search, Cmd+/ focus chat
- **Dark mode**: Toggle between light/dark themes
- **Mobile responsive**: Optimize for tablet/phone viewports
- **Notifications**: Browser notifications for important events
- **Offline support**: Service worker for offline chat history viewing

### Deployment Considerations

**Production Environment:**
- Deploy backend to po.153.se with HTTPS (Let's Encrypt)
- Serve frontend static build from FastAPI using StaticFiles middleware
- Configure WebSocket reverse proxy in Nginx/Caddy
- Set up PostgreSQL with proper connection pooling
- Configure environment variables for production URLs

**Performance:**
- Enable gzip compression for static assets
- Implement connection pooling for database
- Add rate limiting for WebSocket connections
- Cache project list data (invalidate on create/update)

**Security:**
- Add CORS whitelist for production domain
- Implement WebSocket authentication (token-based)
- Sanitize user input before database storage
- Add CSP headers for XSS protection
