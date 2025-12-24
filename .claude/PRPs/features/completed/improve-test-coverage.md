# Feature: Improve Test Coverage and Testing Infrastructure

## Feature Description

Expand the test suite from 15.98% to 80%+ coverage by implementing comprehensive unit tests for untested components, establishing test utilities and mocking patterns, adding coverage thresholds, and setting up CI/CD automation. This will ensure code quality, prevent regressions, and enable confident refactoring.

## User Story

As a developer maintaining this codebase
I want comprehensive test coverage with automated enforcement
So that I can refactor and add features with confidence that existing functionality won't break

## Problem Statement

The current test suite covers only 15.98% of statements and 6.3% of branches. Critical components like the orchestrator (0%), AI clients (0%), and database layer (11-46%) are largely untested. There are no coverage thresholds to prevent regression, no CI/CD pipeline to enforce tests on PRs, and no shared test utilities for common mocking patterns.

## Solution Statement

Implement a phased testing improvement that:
1. Establishes shared test utilities and mocking patterns
2. Adds comprehensive unit tests for all untested components
3. Configures coverage thresholds with gradual enforcement
4. Sets up GitHub Actions CI/CD pipeline for automated testing

## Feature Metadata

**Feature Type**: Enhancement
**Estimated Complexity**: High
**Primary Systems Affected**: All source files in `src/`
**Dependencies**: Jest 29.7.0, ts-jest 29.1.0 (already installed)

---

## CONTEXT REFERENCES

### Relevant Codebase Files

**Existing Test Files (patterns to follow):**
- `src/utils/variable-substitution.test.ts` - Gold standard for pure function testing (100% coverage)
- `src/utils/conversation-lock.test.ts` - Excellent async/concurrency testing patterns (93% coverage)
- `src/adapters/github.test.ts` - Best example of comprehensive mocking strategy
- `src/handlers/command-handler.test.ts` - Good nested describe structure

**Files Requiring Tests:**
- `src/orchestrator/orchestrator.ts` (lines 1-241) - Core message routing, 0% coverage
- `src/utils/tool-formatter.ts` (lines 1-98) - Tool formatting utilities, 0% coverage
- `src/adapters/test.ts` (lines 1-80) - Test adapter, 0% coverage
- `src/clients/factory.ts` (lines 1-20) - Client factory, 0% coverage
- `src/db/conversations.ts` (lines 1-60) - Database conversations, 11% coverage
- `src/db/codebases.ts` (lines 1-70) - Database codebases, 35% coverage
- `src/db/sessions.ts` (lines 1-55) - Database sessions, 46% coverage

**Configuration Files:**
- `jest.config.js` - Current Jest configuration (needs coverage thresholds)
- `package.json` (lines 11-12) - Test scripts (needs `test:coverage` script)

### New Files to Create

- `src/test/setup.ts` - Global test setup and configuration
- `src/test/mocks/database.ts` - Shared database mocking utilities
- `src/test/mocks/platform.ts` - Shared platform adapter mocks
- `src/test/mocks/streaming.ts` - Async streaming test utilities
- `src/utils/tool-formatter.test.ts` - Tool formatter unit tests
- `src/orchestrator/orchestrator.test.ts` - Orchestrator unit tests
- `src/adapters/test.test.ts` - Test adapter unit tests
- `src/clients/factory.test.ts` - Client factory unit tests
- `src/db/conversations.test.ts` - Conversations database tests
- `src/db/codebases.test.ts` - Codebases database tests
- `src/db/sessions.test.ts` - Sessions database tests
- `.github/workflows/test.yml` - CI/CD pipeline configuration

### Relevant Documentation

- [Jest Configuration](https://jestjs.io/docs/configuration)
  - Coverage thresholds configuration
  - Why: Required for enforcing minimum coverage
- [Jest Mock Functions](https://jestjs.io/docs/mock-functions)
  - Manual mocks and jest.mock patterns
  - Why: Database and SDK mocking strategies
- [ts-jest Documentation](https://kulshekhar.github.io/ts-jest/)
  - TypeScript-specific configuration
  - Why: Proper TypeScript compilation in tests

### Patterns to Follow

**Import Pattern (from github.test.ts):**
```typescript
import { ClassName } from './module';

// Mock dependencies at top level BEFORE imports that use them
jest.mock('../orchestrator/orchestrator', () => ({
  handleMessage: jest.fn().mockResolvedValue(undefined),
}));

jest.mock('../db/conversations', () => ({
  getConversation: jest.fn(),
  createConversation: jest.fn(),
}));
```

**Test Organization Pattern:**
```typescript
describe('ModuleName', () => {
  let instance: ClassName;

  beforeEach(() => {
    jest.clearAllMocks();
    instance = new ClassName('config');
  });

  describe('methodName', () => {
    describe('when condition', () => {
      test('should expected behavior', async () => {
        // Arrange
        const input = 'test';

        // Act
        const result = await instance.method(input);

        // Assert
        expect(result).toBe('expected');
      });
    });
  });
});
```

**Async Generator Mocking Pattern:**
```typescript
const mockStreamEvents = [
  { type: 'text', content: 'Response chunk 1' },
  { type: 'tool', toolName: 'Bash', toolInput: { command: 'npm test' } },
  { type: 'text', content: 'Response chunk 2' },
];

const mockClient = {
  sendMessage: jest.fn(async function* () {
    for (const event of mockStreamEvents) {
      yield event;
    }
  }),
  getType: jest.fn().mockReturnValue('claude'),
};
```

**Database Mock Pattern:**
```typescript
jest.mock('./connection', () => ({
  pool: {
    query: jest.fn(),
  },
}));

import { pool } from './connection';

// In test:
(pool.query as jest.Mock).mockResolvedValueOnce({
  rows: [{ id: '123', name: 'test' }],
  rowCount: 1,
});
```

---

## IMPLEMENTATION PLAN

### Phase 1: Test Infrastructure Setup

Establish shared test utilities, mocking patterns, and Jest configuration updates before writing new tests.

**Tasks:**
- Create test setup file with global configuration
- Create shared database mock utilities
- Create shared platform adapter mocks
- Create async streaming test utilities
- Update Jest config with coverage thresholds
- Add test:coverage npm script

### Phase 2: Utility Tests

Test pure utility functions that have no external dependencies.

**Tasks:**
- Implement tool-formatter.test.ts (formatToolCall, formatThinking)
- Verify 100% coverage on utility functions

### Phase 3: Database Layer Tests

Test database operations with mocked pg pool.

**Tasks:**
- Implement conversations.test.ts
- Implement codebases.test.ts
- Implement sessions.test.ts
- Achieve 90%+ coverage on database layer

### Phase 4: Adapter & Client Tests

Test adapters and client factory with mocked dependencies.

**Tasks:**
- Implement test.test.ts (TestAdapter)
- Implement factory.test.ts (getAssistantClient)
- Enhance existing claude.test.ts and codex.test.ts with actual mocked tests

### Phase 5: Orchestrator Tests

Test the core orchestrator with comprehensive mocking.

**Tasks:**
- Implement orchestrator.test.ts with all code paths
- Test slash command handling
- Test /command-invoke flow
- Test session management
- Test streaming modes (stream vs batch)
- Achieve 80%+ coverage on orchestrator

### Phase 6: CI/CD Setup

Set up automated testing in GitHub Actions.

**Tasks:**
- Create GitHub Actions workflow for tests
- Configure coverage reporting
- Set up branch protection rules (documented)

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute every task in order, top to bottom. Each task is atomic and independently testable.

---

### Phase 1: Test Infrastructure Setup

---

### CREATE src/test/setup.ts

- **IMPLEMENT**: Global test setup with console mock, timeout config, and afterEach cleanup
- **PATTERN**: Standard Jest setup pattern
- **IMPORTS**: None required (global Jest types)
- **GOTCHA**: Don't mock console completely - only suppress expected test noise
- **VALIDATE**: `npm test -- --testPathPattern=setup` (should find no tests, but file loads)

```typescript
// Global test setup and configuration

// Increase default timeout for async tests
jest.setTimeout(10000);

// Clean up mocks after each test
afterEach(() => {
  jest.clearAllMocks();
});

// Restore all mocks after all tests complete
afterAll(() => {
  jest.restoreAllMocks();
});
```

---

### CREATE src/test/mocks/database.ts

- **IMPLEMENT**: Shared mock for pg pool with typed query mock
- **PATTERN**: Manual mock factory pattern
- **IMPORTS**: `jest` globals, `QueryResult` type from pg
- **GOTCHA**: Must export both the mock and a reset function
- **VALIDATE**: Import in a test file and verify types work

```typescript
import type { QueryResult } from 'pg';

export interface MockPool {
  query: jest.Mock<Promise<QueryResult<unknown>>>;
}

export const createMockPool = (): MockPool => ({
  query: jest.fn(),
});

export const mockPool = createMockPool();

export const resetMockPool = (): void => {
  mockPool.query.mockReset();
};

// Helper to create mock query results
export const createQueryResult = <T>(rows: T[], rowCount?: number): QueryResult<T> => ({
  rows,
  rowCount: rowCount ?? rows.length,
  command: 'SELECT',
  oid: 0,
  fields: [],
});
```

---

### CREATE src/test/mocks/platform.ts

- **IMPLEMENT**: Mock platform adapter implementing IPlatformAdapter interface
- **PATTERN**: Class implementing interface with jest.fn() methods
- **IMPORTS**: `IPlatformAdapter` from `../../types`
- **GOTCHA**: Must implement all interface methods
- **VALIDATE**: TypeScript compilation passes

```typescript
import type { IPlatformAdapter } from '../../types';

export class MockPlatformAdapter implements IPlatformAdapter {
  public sendMessage = jest.fn<Promise<void>, [string, string]>().mockResolvedValue(undefined);
  public getStreamingMode = jest.fn<'stream' | 'batch', []>().mockReturnValue('stream');
  public getPlatformType = jest.fn<string, []>().mockReturnValue('mock');
  public start = jest.fn<Promise<void>, []>().mockResolvedValue(undefined);
  public stop = jest.fn<void, []>();

  public reset(): void {
    this.sendMessage.mockClear();
    this.getStreamingMode.mockClear();
    this.getPlatformType.mockClear();
    this.start.mockClear();
    this.stop.mockClear();
  }
}

export const createMockPlatform = (): MockPlatformAdapter => new MockPlatformAdapter();
```

---

### CREATE src/test/mocks/streaming.ts

- **IMPLEMENT**: Async generator utilities for testing streaming responses
- **PATTERN**: Factory functions returning AsyncGenerator
- **IMPORTS**: None (pure utility)
- **GOTCHA**: Must properly type the AsyncGenerator return
- **VALIDATE**: TypeScript compilation passes

```typescript
export interface StreamEvent {
  type: 'text' | 'tool' | 'error' | 'complete';
  content?: string;
  toolName?: string;
  toolInput?: Record<string, unknown>;
  error?: Error;
}

export async function* createMockStream(events: StreamEvent[]): AsyncGenerator<StreamEvent> {
  for (const event of events) {
    yield event;
  }
}

export const createMockAssistantClient = (events: StreamEvent[] = []) => ({
  sendMessage: jest.fn(async function* () {
    for (const event of events) {
      yield event;
    }
  }),
  getType: jest.fn().mockReturnValue('claude'),
  resumeSession: jest.fn(async function* () {
    for (const event of events) {
      yield event;
    }
  }),
});
```

---

### UPDATE jest.config.js

- **IMPLEMENT**: Add setupFilesAfterEnv and coverage thresholds
- **PATTERN**: Jest configuration best practices
- **IMPORTS**: N/A (config file)
- **GOTCHA**: Start with low thresholds (30%) and increase gradually
- **VALIDATE**: `npm test -- --coverage` runs without threshold errors

```javascript
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  testMatch: ['**/*.test.ts'],
  setupFilesAfterEnv: ['<rootDir>/src/test/setup.ts'],
  collectCoverageFrom: [
    'src/**/*.ts',
    '!src/**/*.test.ts',
    '!src/index.ts',
    '!src/test/**/*.ts',
  ],
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov', 'html', 'json-summary'],
  coverageThreshold: {
    global: {
      branches: 30,
      functions: 40,
      lines: 40,
      statements: 40,
    },
  },
  verbose: true,
  transformIgnorePatterns: ['node_modules/(?!(@octokit)/)'],
};
```

---

### UPDATE package.json scripts

- **IMPLEMENT**: Add test:coverage script
- **PATTERN**: npm script convention
- **IMPORTS**: N/A
- **GOTCHA**: Ensure script works with both local and CI environments
- **VALIDATE**: `npm run test:coverage` executes successfully

Add to scripts section:
```json
"test:coverage": "jest --coverage",
"test:ci": "jest --coverage --ci --maxWorkers=2"
```

---

### Phase 2: Utility Tests

---

### CREATE src/utils/tool-formatter.test.ts

- **IMPLEMENT**: Comprehensive tests for formatToolCall and formatThinking
- **PATTERN**: Pure function testing (like variable-substitution.test.ts)
- **IMPORTS**: `formatToolCall`, `formatThinking` from `./tool-formatter`
- **GOTCHA**: Test truncation at exact boundaries (100 chars for commands, 200 for thinking)
- **VALIDATE**: `npm test -- --testPathPattern=tool-formatter --coverage`

Test cases to cover:
1. formatToolCall with Bash command (short and long)
2. formatToolCall with Read/Write/Edit file paths
3. formatToolCall with Glob/Grep patterns
4. formatToolCall with MCP tool (mcp__server__tool format)
5. formatToolCall with unknown tool (JSON fallback)
6. formatToolCall with no toolInput
7. formatToolCall with empty toolInput
8. formatThinking under 200 chars
9. formatThinking over 200 chars (truncation)

---

### Phase 3: Database Layer Tests

---

### CREATE src/db/conversations.test.ts

- **IMPLEMENT**: Tests for getOrCreateConversation and updateConversation
- **PATTERN**: Database mock pattern from github.test.ts
- **IMPORTS**: Functions from `./conversations`, mock pool
- **GOTCHA**: Must mock pool.query before importing module under test
- **VALIDATE**: `npm test -- --testPathPattern=conversations --coverage`

Test cases:
1. getOrCreateConversation - returns existing conversation
2. getOrCreateConversation - creates new conversation with default assistant type
3. getOrCreateConversation - uses codebase's assistant type when provided
4. getOrCreateConversation - uses DEFAULT_AI_ASSISTANT env var
5. updateConversation - updates codebase_id only
6. updateConversation - updates cwd only
7. updateConversation - updates both fields
8. updateConversation - no-op when no updates provided

---

### CREATE src/db/codebases.test.ts

- **IMPLEMENT**: Tests for all codebase CRUD operations
- **PATTERN**: Database mock pattern
- **IMPORTS**: Functions from `./codebases`, mock pool
- **GOTCHA**: Commands are JSONB - test serialization/deserialization
- **VALIDATE**: `npm test -- --testPathPattern=codebases --coverage`

Test cases:
1. createCodebase - creates with all fields
2. createCodebase - creates with optional fields omitted
3. getCodebase - returns existing codebase
4. getCodebase - returns null for non-existent
5. updateCodebaseCommands - serializes commands to JSON
6. getCodebaseCommands - deserializes commands from JSON
7. getCodebaseCommands - returns empty object for non-existent
8. registerCommand - adds new command
9. registerCommand - overwrites existing command
10. findCodebaseByRepoUrl - finds matching codebase
11. findCodebaseByRepoUrl - returns null when not found

---

### CREATE src/db/sessions.test.ts

- **IMPLEMENT**: Tests for session lifecycle operations
- **PATTERN**: Database mock pattern
- **IMPORTS**: Functions from `./sessions`, mock pool
- **GOTCHA**: Metadata uses JSONB merge operator (||)
- **VALIDATE**: `npm test -- --testPathPattern=sessions --coverage`

Test cases:
1. getActiveSession - returns active session
2. getActiveSession - returns null when no active session
3. getActiveSession - returns null for non-existent conversation
4. createSession - creates with all fields
5. createSession - creates with optional fields omitted
6. updateSession - updates assistant_session_id
7. deactivateSession - sets active=false and ended_at
8. updateSessionMetadata - merges metadata correctly

---

### Phase 4: Adapter & Client Tests

---

### CREATE src/adapters/test.test.ts

- **IMPLEMENT**: Tests for TestAdapter IPlatformAdapter implementation
- **PATTERN**: Instance testing pattern from telegram.test.ts
- **IMPORTS**: `TestAdapter` from `./test`
- **GOTCHA**: Test both sendMessage (direction='sent') and receiveMessage (direction='received')
- **VALIDATE**: `npm test -- --testPathPattern=test.test --coverage`

Test cases:
1. sendMessage - stores message with direction='sent'
2. receiveMessage - stores message with direction='received'
3. getMessages - returns all messages for conversation
4. getMessages - returns empty array for unknown conversation
5. getSentMessages - filters to only sent messages
6. clearMessages - clears specific conversation
7. clearMessages - clears all conversations when no id provided
8. getAllConversations - returns all conversation ids
9. getStreamingMode - returns 'stream' by default
10. getPlatformType - returns 'test'
11. start/stop - complete without errors

---

### CREATE src/clients/factory.test.ts

- **IMPLEMENT**: Tests for getAssistantClient factory function
- **PATTERN**: Factory pattern testing with mocked constructors
- **IMPORTS**: `getAssistantClient` from `./factory`
- **GOTCHA**: Must mock ClaudeClient and CodexClient constructors
- **VALIDATE**: `npm test -- --testPathPattern=factory --coverage`

Test cases:
1. Returns ClaudeClient for 'claude' type
2. Returns CodexClient for 'codex' type
3. Throws error for unknown type
4. Throws error for empty string
5. Case sensitivity - 'Claude' should throw
6. Each call returns new instance

---

### UPDATE src/clients/claude.test.ts

- **IMPLEMENT**: Replace placeholder with actual mocked tests
- **PATTERN**: SDK mocking with async generator
- **IMPORTS**: `ClaudeClient` from `./claude`, mock SDK
- **GOTCHA**: Claude SDK uses ESM - may need transformIgnorePatterns
- **VALIDATE**: `npm test -- --testPathPattern=claude.test --coverage`

Test cases:
1. Constructor - initializes with API key
2. getType - returns 'claude'
3. sendMessage - yields text events
4. sendMessage - yields tool events
5. resumeSession - resumes with session ID

---

### UPDATE src/clients/codex.test.ts

- **IMPLEMENT**: Replace placeholder with actual mocked tests
- **PATTERN**: SDK mocking with async generator
- **IMPORTS**: `CodexClient` from `./codex`, mock SDK
- **GOTCHA**: Codex SDK has complex token management
- **VALIDATE**: `npm test -- --testPathPattern=codex.test --coverage`

Test cases:
1. Constructor - initializes with tokens
2. getType - returns 'codex'
3. sendMessage - yields text events
4. sendMessage - handles turn.completed event
5. resumeSession - resumes thread

---

### Phase 5: Orchestrator Tests

---

### CREATE src/orchestrator/orchestrator.test.ts

- **IMPLEMENT**: Comprehensive tests for handleMessage function
- **PATTERN**: Heavy mocking pattern from github.test.ts
- **IMPORTS**: `handleMessage` from `./orchestrator`, all database mocks, platform mock, client mock
- **GOTCHA**: Must mock ALL dependencies before importing handleMessage
- **VALIDATE**: `npm test -- --testPathPattern=orchestrator --coverage`

Mock requirements:
```typescript
jest.mock('../db/conversations');
jest.mock('../db/codebases');
jest.mock('../db/sessions');
jest.mock('../handlers/command-handler');
jest.mock('../clients/factory');
jest.mock('fs/promises');
```

Test cases:
1. Slash command (non-invoke) - delegates to command handler, returns immediately
2. /command-invoke without codebase - sends error message
3. /command-invoke with invalid command name - sends "Command not found"
4. /command-invoke with file read error - sends error message
5. /command-invoke with valid command - reads file, substitutes variables
6. Issue context appending - appends issueContext after command text
7. Plan→Execute transition - creates new session, deactivates old
8. Resume existing session - reuses session
9. Stream mode - sends each chunk via platform.sendMessage
10. Batch mode - accumulates response, filters tool indicators
11. Session metadata tracking - updates lastCommand
12. Non-command message without codebase - sends error

---

### Phase 6: CI/CD Setup

---

### CREATE .github/workflows/test.yml

- **IMPLEMENT**: GitHub Actions workflow for automated testing
- **PATTERN**: Standard Node.js CI workflow
- **IMPORTS**: N/A (YAML config)
- **GOTCHA**: Use Node 20.x to match engines requirement
- **VALIDATE**: Push to branch and verify workflow runs

```yaml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20.x'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Type check
        run: npm run type-check

      - name: Lint
        run: npm run lint

      - name: Run tests with coverage
        run: npm run test:coverage

      - name: Upload coverage report
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: coverage/
          retention-days: 14
```

---

## TESTING STRATEGY

### Unit Tests

- **Framework**: Jest 29.7.0 with ts-jest
- **Location**: Co-located with source files (`*.test.ts`)
- **Scope**: All exported functions and classes
- **Mocking**: External dependencies (database, SDKs, file system)
- **Coverage Target**: 80% statements, 75% branches

### Integration Tests

- **Scope**: Future enhancement (not in this PRP)
- **Approach**: Use TestAdapter with real orchestrator
- **Database**: Would require test PostgreSQL container

### Edge Cases

- Empty/null/undefined inputs for all functions
- Database query failures (mock rejects)
- File system errors (command file not found)
- Invalid command names and arguments
- Streaming interruptions and errors
- Session state transitions (plan→execute)
- Concurrent conversation handling

---

## VALIDATION COMMANDS

Execute every command to ensure zero regressions and 100% feature correctness.

### Level 1: Syntax & Style

```bash
# TypeScript compilation
npm run type-check

# ESLint
npm run lint

# Prettier formatting
npm run format:check
```

### Level 2: Unit Tests

```bash
# Run all tests
npm test

# Run tests with coverage
npm run test:coverage

# Run specific test file
npm test -- --testPathPattern=orchestrator

# Run tests in watch mode (development)
npm run test:watch
```

### Level 3: Coverage Verification

```bash
# Verify coverage meets thresholds
npm run test:coverage

# View HTML report
open coverage/index.html
```

### Level 4: Manual Validation

```bash
# Start application and verify tests don't break runtime
npm run dev

# Test via test adapter endpoints
curl -X POST http://localhost:3000/test/message \
  -H "Content-Type: application/json" \
  -d '{"conversationId":"test-123","message":"/status"}'

curl http://localhost:3000/test/messages/test-123
```

---

## ACCEPTANCE CRITERIA

- [ ] All 7 existing test files continue to pass
- [ ] New test files created for: tool-formatter, conversations, codebases, sessions, test adapter, factory, orchestrator
- [ ] Overall statement coverage >= 60% (up from 15.98%)
- [ ] Overall branch coverage >= 40% (up from 6.3%)
- [ ] Coverage thresholds configured and enforced
- [ ] CI/CD pipeline runs tests on every PR
- [ ] All validation commands pass with zero errors
- [ ] No regressions in existing functionality

---

## COMPLETION CHECKLIST

- [ ] Phase 1: Test infrastructure setup complete
- [ ] Phase 2: tool-formatter tests complete (100% coverage)
- [ ] Phase 3: Database layer tests complete (90%+ coverage)
- [ ] Phase 4: Adapter and client tests complete
- [ ] Phase 5: Orchestrator tests complete (80%+ coverage)
- [ ] Phase 6: CI/CD pipeline configured
- [ ] All validation commands executed successfully
- [ ] Coverage thresholds met
- [ ] Manual testing confirms no regressions

---

## NOTES

### Design Decisions

1. **Co-located tests**: Tests remain next to source files (`*.test.ts`) rather than separate `__tests__` directory - matches existing pattern
2. **Shared mocks in src/test/**: Centralized mock utilities prevent duplication across test files
3. **Gradual coverage thresholds**: Starting at 30-40% to avoid blocking existing workflow, will increase as coverage improves
4. **No integration tests in this PRP**: Focus on unit tests first; integration tests can be added later using TestAdapter

### Trade-offs

1. **Mocking vs Real Database**: Unit tests use mocks for speed and isolation. Integration tests with real PostgreSQL deferred to future work.
2. **SDK Mocking Complexity**: Claude/Codex SDKs use ESM and complex async patterns. Tests focus on interface contracts rather than SDK internals.
3. **Coverage Thresholds**: Low initial thresholds (30-40%) allow incremental improvement without blocking CI immediately.

### Risks

1. **ESM Module Issues**: Some tests may need `transformIgnorePatterns` adjustments for ESM modules
2. **Async Generator Mocking**: Complex to mock correctly; may need iteration on patterns
3. **CI Time**: Full test suite with coverage may take 30-60 seconds; acceptable for this project size

### Future Improvements

1. Increase coverage thresholds to 70%+ after baseline established
2. Add integration tests using TestAdapter with real orchestrator
3. Add database integration tests with PostgreSQL test container
4. Add performance benchmarks for conversation lock

<!-- EOF -->
