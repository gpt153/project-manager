# Feature: Telegram Markdown Formatter

## Feature Description

Implement a platform-aware message formatting system that converts GitHub-flavored markdown (output from AI assistants like Claude/Codex) to Telegram's MarkdownV2 format. Currently, messages are sent as raw text, causing markdown syntax (`**bold**`, `## Header`) to display as literal characters instead of formatted text.

## User Story

As a **user interacting with the bot via Telegram**
I want to **see properly formatted messages with bold text, code blocks, and other formatting**
So that **AI responses are readable and visually structured instead of showing raw markdown syntax**

## Problem Statement

AI assistants (Claude, Codex) output responses in GitHub-flavored markdown format. When sent to Telegram without conversion:
- `## Header` displays as literal `## Header` instead of bold text
- `**bold**` shows as `**bold**` instead of **bold**
- Code blocks, lists, and links appear as raw text
- Messages are difficult to read and unprofessional

Telegram requires MarkdownV2 format which is **completely different** from GitHub markdown:
| Feature | GitHub Markdown | Telegram MarkdownV2 |
|---------|----------------|---------------------|
| Bold | `**text**` | `*text*` |
| Italic | `*text*` | `_text_` |
| Headers | `## Header` | Not supported (convert to bold) |
| Code block | ` ```js ` | ` ```js ` (with escaped chars) |
| Lists | `- item` | Must escape `-` |

## Solution Statement

Create a `telegram-markdown.ts` utility module that:
1. Converts GitHub-flavored markdown to Telegram MarkdownV2 using `telegramify-markdown` library
2. Handles escaping of special characters required by MarkdownV2
3. Provides fallback to plain text if conversion fails (API strictness)
4. Integrates with `TelegramAdapter.sendMessage()` to add `parse_mode: 'MarkdownV2'`

## Feature Metadata

**Feature Type**: Enhancement
**Estimated Complexity**: Medium
**Primary Systems Affected**: `src/adapters/telegram.ts`, `src/utils/`
**Dependencies**: `telegramify-markdown` npm package (v1.3.0+)

---

## CONTEXT REFERENCES

### Relevant Codebase Files

- `src/adapters/telegram.ts` (lines 28-55) - Current `sendMessage()` implementation that needs updating
- `src/types/index.ts` (lines 49-74) - `IPlatformAdapter` interface (no changes needed)
- `src/utils/tool-formatter.ts` - Pattern for utility module structure with JSDoc and exports
- `src/utils/variable-substitution.ts` - Pattern for pure function utility with comprehensive tests
- `src/adapters/github.ts` (lines 66-84) - Reference: GitHub adapter passes markdown through unchanged
- `src/adapters/test.ts` - Reference: Simple adapter implementation pattern

### New Files to Create

- `src/utils/telegram-markdown.ts` - Markdown conversion utility functions
- `src/utils/telegram-markdown.test.ts` - Unit tests for conversion functions

### Files to Update

- `src/adapters/telegram.ts` - Integrate markdown formatting in `sendMessage()`
- `package.json` - Add `telegramify-markdown` dependency

### Relevant Documentation

- [Telegram Bot API Formatting Options](https://core.telegram.org/bots/api#formatting-options)
  - Section: MarkdownV2 style
  - Why: Official spec for escape characters and supported formatting
- [telegramify-markdown npm](https://www.npmjs.com/package/telegramify-markdown)
  - Section: Usage and options
  - Why: Library API for conversion function
- [Telegraf sendMessage API](https://telegraf.js.org/classes/Telegram.html#sendMessage)
  - Section: Extra options
  - Why: How to pass `parse_mode` parameter

### Patterns to Follow

**Utility Module Structure** (from `tool-formatter.ts`):
```typescript
/**
 * Module description
 */

/**
 * Function JSDoc with @param and @returns
 */
export function functionName(param: Type): ReturnType {
  // Implementation
}
```

**Error Handling Pattern** (logging without crashing):
```typescript
try {
  // Attempt operation
} catch (error) {
  console.warn('[Module] Operation failed, fallback:', error);
  // Use fallback behavior
}
```

**Naming Conventions**:
- Files: kebab-case (`telegram-markdown.ts`)
- Functions: camelCase (`convertToTelegramMarkdown`)
- Constants: UPPER_SNAKE_CASE (`MAX_LENGTH`)

**Test Pattern** (from `tool-formatter.test.ts`):
```typescript
describe('moduleName', () => {
  describe('functionName', () => {
    test('specific scenario', () => {
      const result = functionName(input);
      expect(result).toBe(expected);
    });
  });
});
```

---

## IMPLEMENTATION PLAN

### Phase 1: Foundation

Add the markdown conversion dependency and create the utility module.

**Tasks:**
- Install `telegramify-markdown` package
- Create `telegram-markdown.ts` utility module
- Implement conversion function with error handling

### Phase 2: Core Implementation

Implement the main conversion logic with proper escaping and fallback handling.

**Tasks:**
- Implement `convertToTelegramMarkdown()` function
- Handle edge cases (empty strings, already-escaped content)
- Add fallback for conversion failures

### Phase 3: Integration

Integrate the formatter into the Telegram adapter.

**Tasks:**
- Update `TelegramAdapter.sendMessage()` to use converter
- Add `parse_mode: 'MarkdownV2'` to sendMessage calls
- Implement fallback to plain text on API errors

### Phase 4: Testing & Validation

Comprehensive testing of conversion and integration.

**Tasks:**
- Unit tests for conversion function
- Edge case tests (headers, code blocks, special characters)
- Integration test with mock Telegram API

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute every task in order, top to bottom. Each task is atomic and independently testable.

### Task 1: ADD telegramify-markdown dependency

- **IMPLEMENT**: Add `telegramify-markdown` to package.json dependencies
- **PATTERN**: Match existing dependency format in package.json:32-39
- **COMMAND**: `npm install telegramify-markdown`
- **VALIDATE**: `npm ls telegramify-markdown` (should show version)
- **VALIDATE**: `npm run type-check` (no type errors)

### Task 2: CREATE src/utils/telegram-markdown.ts

- **IMPLEMENT**: Create utility module with conversion function
- **PATTERN**: Mirror structure from `src/utils/tool-formatter.ts`
- **IMPORTS**:
  ```typescript
  import telegramifyMarkdown from 'telegramify-markdown';
  ```
- **GOTCHA**: The library uses CommonJS default export - import as shown above
- **VALIDATE**: `npm run type-check`

**Implementation:**
```typescript
/**
 * Telegram Markdown Converter
 *
 * Converts GitHub-flavored markdown (from AI assistants) to Telegram MarkdownV2 format.
 * Uses telegramify-markdown library for robust conversion.
 */

import telegramifyMarkdown from 'telegramify-markdown';

/**
 * Convert GitHub-flavored markdown to Telegram MarkdownV2 format
 *
 * Transformations:
 * - Headers (##) → Bold (*text*)
 * - **bold** → *bold*
 * - *italic* → _italic_
 * - Lists (- item) → Escaped bullet points
 * - Special characters escaped for MarkdownV2
 *
 * @param markdown - GitHub-flavored markdown text
 * @returns Telegram MarkdownV2 formatted text
 */
export function convertToTelegramMarkdown(markdown: string): string {
  if (!markdown || markdown.trim() === '') {
    return markdown;
  }

  try {
    // 'escape' strategy: escape unsupported tags rather than remove them
    return telegramifyMarkdown(markdown, 'escape');
  } catch (error) {
    console.warn('[TelegramMarkdown] Conversion failed, returning original:', error);
    return escapeMarkdownV2(markdown);
  }
}

/**
 * Escape special characters for Telegram MarkdownV2
 * Used as fallback when conversion fails
 *
 * Characters that need escaping: _ * [ ] ( ) ~ ` > # + - = | { } . !
 *
 * @param text - Plain text to escape
 * @returns Text with special characters escaped
 */
export function escapeMarkdownV2(text: string): string {
  // Characters that must be escaped in MarkdownV2
  const specialChars = /([_*\[\]()~`>#+\-=|{}.!\\])/g;
  return text.replace(specialChars, '\\$1');
}

/**
 * Check if text appears to be already in MarkdownV2 format
 * (contains escaped characters)
 *
 * @param text - Text to check
 * @returns True if text appears already escaped
 */
export function isAlreadyEscaped(text: string): boolean {
  // Look for patterns like \* \_ \[ etc.
  return /\\[_*\[\]()~`>#+\-=|{}.!]/.test(text);
}
```

### Task 3: CREATE src/utils/telegram-markdown.test.ts

- **IMPLEMENT**: Comprehensive unit tests for conversion functions
- **PATTERN**: Mirror test structure from `src/utils/tool-formatter.test.ts`
- **IMPORTS**: Import functions from `./telegram-markdown`
- **VALIDATE**: `npm test -- src/utils/telegram-markdown.test.ts`

**Implementation:**
```typescript
import {
  convertToTelegramMarkdown,
  escapeMarkdownV2,
  isAlreadyEscaped
} from './telegram-markdown';

describe('telegram-markdown', () => {
  describe('convertToTelegramMarkdown', () => {
    describe('headers', () => {
      test('converts ## header to bold', () => {
        const result = convertToTelegramMarkdown('## Header Text');
        expect(result).toContain('*Header Text*');
      });

      test('converts # header to bold', () => {
        const result = convertToTelegramMarkdown('# Main Header');
        expect(result).toContain('*Main Header*');
      });
    });

    describe('bold and italic', () => {
      test('converts **bold** to *bold*', () => {
        const result = convertToTelegramMarkdown('This is **bold** text');
        expect(result).toContain('*bold*');
      });

      test('converts *italic* to _italic_', () => {
        const result = convertToTelegramMarkdown('This is *italic* text');
        expect(result).toContain('_italic_');
      });
    });

    describe('code blocks', () => {
      test('preserves inline code', () => {
        const result = convertToTelegramMarkdown('Use `npm install`');
        expect(result).toContain('`npm install`');
      });

      test('preserves code blocks', () => {
        const input = '```javascript\nconst x = 1;\n```';
        const result = convertToTelegramMarkdown(input);
        expect(result).toContain('```');
        expect(result).toContain('const x = 1');
      });
    });

    describe('lists', () => {
      test('converts bullet lists', () => {
        const input = '- Item 1\n- Item 2';
        const result = convertToTelegramMarkdown(input);
        // Library converts - to bullet point or escapes it
        expect(result).toBeDefined();
        expect(result.length).toBeGreaterThan(0);
      });
    });

    describe('links', () => {
      test('preserves markdown links', () => {
        const result = convertToTelegramMarkdown('[Click here](https://example.com)');
        expect(result).toContain('[Click here]');
        expect(result).toContain('https://example.com');
      });
    });

    describe('special characters', () => {
      test('escapes special characters', () => {
        const input = 'Price is $100. Use + or -';
        const result = convertToTelegramMarkdown(input);
        // Should have escaped . + -
        expect(result).toBeDefined();
      });
    });

    describe('edge cases', () => {
      test('handles empty string', () => {
        const result = convertToTelegramMarkdown('');
        expect(result).toBe('');
      });

      test('handles whitespace only', () => {
        const result = convertToTelegramMarkdown('   ');
        expect(result).toBe('   ');
      });

      test('handles plain text without markdown', () => {
        const result = convertToTelegramMarkdown('Hello world');
        expect(result).toContain('Hello world');
      });
    });
  });

  describe('escapeMarkdownV2', () => {
    test('escapes underscore', () => {
      expect(escapeMarkdownV2('snake_case')).toBe('snake\\_case');
    });

    test('escapes asterisk', () => {
      expect(escapeMarkdownV2('2*3=6')).toBe('2\\*3\\=6');
    });

    test('escapes brackets', () => {
      expect(escapeMarkdownV2('[text](url)')).toBe('\\[text\\]\\(url\\)');
    });

    test('escapes period', () => {
      expect(escapeMarkdownV2('Hello.')).toBe('Hello\\.');
    });

    test('escapes backslash', () => {
      expect(escapeMarkdownV2('path\\to\\file')).toBe('path\\\\to\\\\file');
    });

    test('handles empty string', () => {
      expect(escapeMarkdownV2('')).toBe('');
    });

    test('escapes multiple special chars', () => {
      const input = 'Use `code` and *bold* here!';
      const result = escapeMarkdownV2(input);
      expect(result).toBe('Use \\`code\\` and \\*bold\\* here\\!');
    });
  });

  describe('isAlreadyEscaped', () => {
    test('returns true for escaped underscore', () => {
      expect(isAlreadyEscaped('snake\\_case')).toBe(true);
    });

    test('returns true for escaped asterisk', () => {
      expect(isAlreadyEscaped('2\\*3')).toBe(true);
    });

    test('returns false for unescaped text', () => {
      expect(isAlreadyEscaped('Hello world')).toBe(false);
    });

    test('returns false for regular markdown', () => {
      expect(isAlreadyEscaped('**bold** text')).toBe(false);
    });

    test('returns false for empty string', () => {
      expect(isAlreadyEscaped('')).toBe(false);
    });
  });
});
```

### Task 4: UPDATE src/adapters/telegram.ts - Add import

- **IMPLEMENT**: Add import for telegram-markdown utility at top of file
- **PATTERN**: Follow existing import structure (lines 5-6)
- **IMPORTS**:
  ```typescript
  import { convertToTelegramMarkdown } from '../utils/telegram-markdown';
  ```
- **VALIDATE**: `npm run type-check`

### Task 5: UPDATE src/adapters/telegram.ts - Modify sendMessage for short messages

- **IMPLEMENT**: Update the short message path (line 32) to use markdown formatting
- **PATTERN**: Use try-catch for API calls with fallback
- **GOTCHA**: MarkdownV2 is strict - malformed markdown causes API errors. Must fallback to plain text.
- **VALIDATE**: `npm run type-check`

**Update line 31-32 to:**
```typescript
if (message.length <= MAX_LENGTH) {
  const formatted = convertToTelegramMarkdown(message);
  try {
    await this.bot.telegram.sendMessage(id, formatted, { parse_mode: 'MarkdownV2' });
  } catch (error) {
    // Fallback to plain text if MarkdownV2 fails (strict parsing)
    console.warn('[Telegram] MarkdownV2 failed, sending as plain text');
    await this.bot.telegram.sendMessage(id, message);
  }
}
```

### Task 6: UPDATE src/adapters/telegram.ts - Modify sendMessage for chunked messages

- **IMPLEMENT**: Update the chunked message sending (lines 33-54) to use markdown formatting
- **PATTERN**: Apply same conversion and fallback pattern to each chunk
- **GOTCHA**: Each chunk must be independently valid MarkdownV2 - conversion happens per chunk
- **VALIDATE**: `npm run type-check`

**Update the else block to:**
```typescript
} else {
  // Split long messages by lines to preserve formatting
  const lines = message.split('\n');
  let chunk = '';

  for (const line of lines) {
    // Reserve 100 chars for safety margin
    if (chunk.length + line.length + 1 > MAX_LENGTH - 100) {
      if (chunk) {
        const formatted = convertToTelegramMarkdown(chunk);
        try {
          await this.bot.telegram.sendMessage(id, formatted, { parse_mode: 'MarkdownV2' });
        } catch {
          await this.bot.telegram.sendMessage(id, chunk);
        }
      }
      chunk = line;
    } else {
      chunk += (chunk ? '\n' : '') + line;
    }
  }

  // Send remaining chunk
  if (chunk) {
    const formatted = convertToTelegramMarkdown(chunk);
    try {
      await this.bot.telegram.sendMessage(id, formatted, { parse_mode: 'MarkdownV2' });
    } catch {
      await this.bot.telegram.sendMessage(id, chunk);
    }
  }
}
```

### Task 7: UPDATE src/adapters/telegram.test.ts - Add formatting tests

- **IMPLEMENT**: Add tests verifying markdown formatting integration
- **PATTERN**: Follow existing test structure in file
- **IMPORTS**: May need to mock the telegram-markdown module
- **VALIDATE**: `npm test -- src/adapters/telegram.test.ts`

**Add test cases:**
```typescript
describe('message formatting', () => {
  test('formats markdown when sending messages', async () => {
    const adapter = new TelegramAdapter('fake-token-for-testing');
    // Verify convertToTelegramMarkdown is called
    // Mock telegram.sendMessage to verify parse_mode is passed
  });
});
```

### Task 8: RUN full validation suite

- **IMPLEMENT**: Run all validation commands to ensure no regressions
- **VALIDATE**: Execute all Level 1-4 validation commands (see section below)

---

## TESTING STRATEGY

### Unit Tests

**Scope**: `src/utils/telegram-markdown.test.ts`
- Test `convertToTelegramMarkdown()` with various markdown inputs
- Test `escapeMarkdownV2()` with all special characters
- Test `isAlreadyEscaped()` detection
- Test edge cases: empty strings, already-escaped content, plain text

**Coverage Requirements**: 90%+ for new utility module

### Integration Tests

**Scope**: `src/adapters/telegram.test.ts`
- Test that `sendMessage()` uses markdown formatting
- Test fallback behavior when MarkdownV2 fails
- Test chunked message formatting

### Edge Cases

- Empty message
- Message with only whitespace
- Message with no markdown (plain text)
- Message with malformed markdown
- Message with already-escaped characters
- Very long message requiring chunking
- Message with code blocks containing special characters
- Message with nested formatting (bold inside italic)
- Message with URLs containing special characters

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

# Run specific module tests
npm test -- src/utils/telegram-markdown.test.ts

# Run adapter tests
npm test -- src/adapters/telegram.test.ts

# Coverage check
npm run test:coverage
```

### Level 3: Integration Tests

```bash
# Full test suite with coverage
npm run test:ci
```

### Level 4: Manual Validation

**Using Test Adapter (no Telegram setup required):**

```bash
# 1. Start application
npm run dev

# 2. Send test message with markdown
curl -X POST http://localhost:3000/test/message \
  -H "Content-Type: application/json" \
  -d '{"conversationId":"md-test","message":"## Test Header\n\n**Bold** and *italic* text\n\n```js\nconst x = 1;\n```"}'

# 3. Check response formatting
curl http://localhost:3000/test/messages/md-test | jq

# 4. Verify markdown was processed (look for converted format)
```

**Using Telegram (requires bot token):**

1. Send message to bot: `## Test Header`
2. Verify it displays as bold "Test Header" (not literal ##)
3. Send: `**bold** and *italic*`
4. Verify bold and italic formatting applied
5. Send code block and verify syntax highlighting

---

## ACCEPTANCE CRITERIA

- [ ] `telegramify-markdown` package installed and typed correctly
- [ ] `convertToTelegramMarkdown()` function converts GitHub markdown to MarkdownV2
- [ ] `escapeMarkdownV2()` function escapes all 16 special characters
- [ ] `TelegramAdapter.sendMessage()` applies markdown formatting
- [ ] Messages sent with `parse_mode: 'MarkdownV2'`
- [ ] Fallback to plain text when MarkdownV2 parsing fails
- [ ] All unit tests pass with 90%+ coverage on new module
- [ ] All existing tests continue to pass (no regressions)
- [ ] `npm run type-check` passes with no errors
- [ ] `npm run lint` passes with no errors
- [ ] Manual testing confirms formatted messages in Telegram

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Each task validation passed immediately
- [ ] All validation commands executed successfully
- [ ] Full test suite passes (unit + integration)
- [ ] No linting or type checking errors
- [ ] Manual testing confirms feature works in Telegram
- [ ] Acceptance criteria all met
- [ ] Code reviewed for quality and maintainability

---

## NOTES

### Design Decisions

1. **Library Choice**: `telegramify-markdown` chosen over `telegram-format` because:
   - Specifically designed for LLM output conversion
   - Handles GitHub-flavored markdown to MarkdownV2 transformation
   - Active maintenance (v1.3.0, March 2025)
   - TypeScript types included

2. **Fallback Strategy**: Plain text fallback when MarkdownV2 fails because:
   - MarkdownV2 parsing is strict - malformed markdown causes API errors
   - User experience > formatting - message delivery is priority
   - Logged warning enables debugging without breaking flow

3. **Per-Chunk Conversion**: Apply conversion to each chunk separately because:
   - Each chunk must be independently valid MarkdownV2
   - Splitting mid-formatting-tag would cause parse errors
   - Consistent with current line-based splitting approach

### Known Limitations

1. **Headers**: Telegram doesn't support headers - converted to bold text
2. **Tables**: Telegram doesn't support tables - will be escaped or removed
3. **Nested Formatting**: Complex nesting may not convert perfectly
4. **Images**: Telegram requires separate API call for images - links converted to text

### Future Enhancements

1. Add HTML mode option as alternative to MarkdownV2
2. Add platform-specific `formatMessage()` to `IPlatformAdapter` interface
3. Create Slack mrkdwn converter for future Slack adapter
4. Consider message caching to avoid re-conversion

### Risk Mitigation

1. **Conversion Failures**: Fallback to plain text ensures message delivery
2. **API Changes**: Library abstraction allows swapping conversion logic
3. **Performance**: Conversion is O(n) - negligible impact on message latency

<!-- EOF -->
