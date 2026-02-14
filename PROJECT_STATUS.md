# Translation Cog - Project Status & Roadmap

## Project Overview

The Translation cog is a **redbot cog** that translates messages and provides multilingual support for Discord communities with intelligent automation and user privacy as core principles.

**Core Philosophy**:
- **Automatic & Unobtrusive**: Translations happen with minimal user interaction
- **Privacy-First**: All translations are ephemeral (visible only to the requester)
- **Cache-Aware**: Minimize API calls through intelligent caching
- **Modular Architecture**: Pure business logic separated from Discord interactions

---

## Phased Implementation Plan

**Status**: ✅ **Phase 1 COMPLETE** | Phase 2-6 Planned

### **Phase 1: Refactor for Separation of Concerns** ✅ COMPLETE
*Goal: Clean architecture that separates Discord interactions from translation logic*

**Status**: ✅ Implementation Complete

**Deliverables**:
- ✅ `translator.py` - Translation logic with no Discord imports
- ✅ `cache.py` - In-memory caching with LRU eviction and TTL
- ✅ `strings.py` - Centralized user-facing messages and embeds
- ✅ `main.py` - Discord commands and event handlers
- ✅ `__init__.py` - Cog setup and registration
- ✅ Architecture documentation and comprehensive docstrings

#### Module Structure

```
translate/
├── __init__.py          # Setup hook
├── main.py              # Discord interface (550 lines)
├── translator.py        # Translation logic (230 lines)
├── cache.py             # LRU cache with TTL (240 lines)
└── strings.py           # Messages & embeds (150 lines)
```

#### 1. `main.py` - Discord Interface Layer
**Responsibility**: Handle all Discord interactions

- Discord commands and event listeners
- Configuration management (redbot Config system)
- Command argument parsing and validation
- Response formatting and sending (ephemeral-first)
- Context menu support
- User preference management

**Commands Implemented**:
- `[p]translate [text]` - Translate to preferred language
- `[p]translate to <lang> [text]` - Translate to specific language
- `/translate <lang> <text>` - Slash command
- `/setmylanguage <lang>` - Set language preference
- Context menu: Right-click message → Apps → Translate

**Key Methods**:
- `translate_group()` - Text command group
- `translate_to()` - Translate to specific language
- `translate_slash()` - Slash command version
- `set_language()` - Hybrid command for preference
- `translate_context_menu()` - Context menu handler
- `_respond_ephemeral()` - Send responses (ephemeral when possible)
- `_do_translate()` - Translation with caching
- `_clean_text()` - Remove Discord emojis

**Design**: No direct API calls or business logic—delegates to `translator.py`

---

#### 2. `translator.py` - Pure Translation Logic
**Responsibility**: Translation operations (no Discord imports—reusable platform-agnostic logic)

- Language normalization and validation
- Google Translate API calls (async-safe)
- Language detection from text
- Error handling for API failures
- Timeout protection (10 seconds default)

**Key Classes**:
- `Translator` - Main API handler
- `TranslatorError` - Base exception
- `LanguageNotFoundError` - Invalid language
- `TranslationAPIError` - API failures

**Key Methods**:
- `async translate(text, target_language, source_language)` - Translate text
- `async detect_language(text)` - Detect language of text
- `normalize_language(language)` - Convert user input to ISO 639-1 code
- `get_available_languages()` - List all supported languages

**Design**:
- Async-first (all I/O is non-blocking)
- Uses `asyncio.to_thread()` for sync Google Translate API
- Full type hints throughout
- No Discord dependencies (mobile/web ready!)

---

#### 3. `cache.py` - Translation Cache
**Responsibility**: In-memory caching with automatic expiration and memory bounds

- Thread-safe async operations with locks
- LRU (Least Recently Used) eviction at capacity
- TTL (time-to-live) automatic expiration
- Cache statistics (hits, misses, evictions)
- SHA256 hash-based keys for efficiency

**Key Classes**:
- `TranslationCache` - Cache manager
- `CacheEntry` - Individual cached translation with metadata

**Key Methods**:
- `async get(text, target_language)` - Retrieve cached translation
- `async set(text, target_language, translated_text, source_language, ttl)` - Store
- `async clear()` - Clear all entries
- `async cleanup_expired()` - Remove expired entries periodically
- `get_stats()` - Get cache performance metrics

**Cache Configuration**:
- **Max Size**: 5,000 entries (prevents unbounded growth)
- **Default TTL**: 7 days (604,800 seconds)
- **Key Format**: `"{target_lang}:{sha256_hash}"`
- **Eviction Policy**: LRU when capacity exceeded

**Design**: Pure data structure—no Discord logic, fully testable

---

#### 4. `strings.py` - User-Facing Strings
**Responsibility**: Centralized strings for easy maintenance and future i18n

- Error messages with actionable advice
- Success messages and confirmations
- Embed builder functions for responses
- Command help text
- Template strings for embeds

**Key Functions**:
- `build_translation_embed()` - Format translation with metadata
- `build_error_embed()` - Format error messages
- `build_success_embed()` - Format success confirmations

**Message Categories**:
- `MISSING_INPUTS` - No text to translate
- `LANGUAGE_NOT_FOUND` - Invalid language
- `TRANSLATION_FAILED` - API errors
- `TRANSLATION_TIMEOUT` - Timeout errors
- `NO_LANGUAGE_PREFERENCE` - User hasn't set preference
- And more...

**Design**: Strings only—no logic, easily extractable for translation/localization

---

#### Phase 1 Features Implemented

| Feature | Status | Notes |
|---------|--------|-------|
| Modular architecture | ✅ | Four focused modules, no circular deps |
| Translation logic | ✅ | `translator.py` with full error handling |
| LRU+TTL caching | ✅ | 5000 entries, 7-day TTL, stats tracking |
| User preferences | ✅ | Per-user language via redbot Config |
| Ephemeral responses | ✅ | All responses user-specific and hidden |
| Text commands | ✅ | `[p]translate`, `[p]translate to` |
| Slash commands | ✅ | `/translate`, `/setmylanguage` |
| Context menu | ✅ | Right-click message to translate |
| Language autocomplete | ✅ | Smart suggestions in slash commands |
| Error handling | ✅ | Specific exceptions, graceful fallbacks |
| Type hints | ✅ | Full type annotations throughout |
| Docstrings | ✅ | Google-style docstrings on every function |
| GDPR compliance | ✅ | User data deletion on request |
| Async-first design | ✅ | Non-blocking I/O throughout |

---

#### Design Decisions in Phase 1

1. **Ephemeral-First Architecture**
   - All responses visible only to requester
   - Keeps channel clean and respects privacy
   - Fallback to DM if ephemeral unavailable

2. **Sync API → Async Interface**
   - Google Translate is synchronous
   - Use `asyncio.to_thread()` for non-blocking calls
   - 10-second timeout protection

3. **LRU + TTL Cache**
   - LRU eviction prevents memory bloat in large servers
   - TTL (7 days) removes stale translations
   - Configurable, stats available for monitoring

4. **SHA256 Cache Keys**
   - Avoid storing full text as keys
   - Deterministic and collision-resistant
   - Safe for any message length

5. **Config for Persistence**
   - Use redbot's `Config` system
   - Persistent across bot restarts
   - Per-user and per-guild support built-in

6. **Modular Separation**
   - `translator.py` has zero Discord imports → reusable for mobile/web
   - `cache.py` is pure data structure → easy to test
   - `strings.py` is templates only → easy to localize
   - `main.py` handles only Discord interactions

---

#### Architecture Flow

```
Discord User Input
       ↓
   main.py (parse command, get user prefs)
       ↓
   cache.py (check if cached)
       ↓
   translator.py (if not cached: call Google Translate)
       ↓
   cache.py (store result)
       ↓
   strings.py (format embed)
       ↓
   main.py (send ephemeral response)
       ↓
Discord User (only they see result)
```

---

#### Testing Phase 1

**Quick Manual Test**:
```
[p]load translate
[p]setmylanguage spanish
[p]translate Hello world
# Should immediately see Spanish translation in ephemeral message

# Test cache (repeat—should be instant):
[p]translate Hello world
```

**Commands to Test**:
- `[p]translate Hola` - Uses preferred language
- `[p]translate to french Hello` - Specific language
- `/translate language:german text:Hello world` - Slash command
- Right-click message → Apps → Translate - Context menu
- `/setmylanguage italian` - Change preference

**Cache Performance**:
```python
# From bot owner/admin
cog = bot.get_cog("Translation")
stats = cog.cache.get_stats()
print(f"Cache: {stats['hit_rate']:.1%} hit rate after heavy use")
```

---

## Code Quality Metrics (Phase 1)

### File Statistics

| File | Lines | Purpose | Complexity |
|------|-------|---------|-----------|
| `main.py` | ~450 | Discord commands & handlers | Medium |
| `translator.py` | ~230 | Translation logic | Low |
| `cache.py` | ~240 | LRU+TTL caching | Low |
| `strings.py` | ~150 | Messages & embeds | Very Low |
| `__init__.py` | ~35 | Setup & registration | Very Low |
| **Total** | **~1,105** | **Full cog** | **Low avg** |

### Quality Indicators

✅ **Type Safety**: 100% type-annotated functions
✅ **Documentation**: Google-style docstrings on every function/class
✅ **Error Handling**: Custom exceptions for different failure modes
✅ **Async-First**: All I/O non-blocking with timeout protection
✅ **Testing Ready**: Pure modules in `translator.py` and `cache.py` easy to unit test
✅ **Logging**: Appropriate levels (DEBUG, WARNING, ERROR)
✅ **Privacy**: No user content logged, ephemeral responses only
✅ **Reusability**: `translator.py` has zero Discord dependencies

### Design Patterns Applied

- **Separation of Concerns** - Four focused modules
- **Async/Await** - Non-blocking I/O throughout
- **LRU Cache** - Memory-bounded performance optimization
- **TTL Expiration** - Automatic cleanup of stale data
- **Custom Exceptions** - Specific error types for different scenarios
- **Singleton Pattern** - Translator and Cache single instances per cog
- **Configuration Pattern** - redbot Config for persistence

---

## Known Limitations & Future Considerations

### Phase 1 Limitations
1. **No auto-translation yet** - Requires manual command invocation
2. **No rate limit awareness** - Future phases will handle Google API limits
3. **No language detection display** - Could show detected source language
4. **No per-guild controls** - Future phases for admin settings

### What's Planned for Phase 2+
- Reaction emoji triggers for auto-translation
- Per-guild admin settings
- Language detection feedback
- Rate limit handling
- Background cache cleanup tasks
- Unit and integration tests

---

## Upcoming Phases

**Note**: Phase 1 is complete and the cog is fully functional! The following phases are planned enhancements.

### **Phase 2: Intelligent Auto-Translation Trigger** (Automation)
*Goal: Detect when a user wants a translation without explicit commands*

**Tasks:**
- Add message context detection via reactions
  - User reacts to a message with flag emoji (🇬🇧, 🇪🇸, etc.) to trigger translation
  - Helper method: `_should_auto_translate(message, user)`
- Add Config options:
  - `user_settings.auto_translate` (enabled/disabled per user)
  - `user_settings.auto_source_language` (optional)
*Goal: Translations are invisible to everyone except the intended user*

**Tasks:**
- Refactor response methods to prefer ephemeral:
  - Slash commands → always ephemeral
  - Context menu → always ephemeral
  - Reaction-triggered →Reply to user's message with ephemeral embed (if possible) OR send as DM
  - Text commands → ephemeral if in server (delete after 30s), public in DMs
- Create response templates in `strings.py`:
  - Success embed (with language footer)
  - Error embed (with actionable advice)
  - Rate limit message (with retry suggestion)
- Add user-friendly footer with source→target language names

**Key decisions:**
- **DM fallback**: If ephemeral isn't available (older Discord versions), fall back to user DM
- **Timeout handling**: Translate requests timeout after 10 seconds → show error, don't hang
- **Embed color**: Use bot's theme color for consistency

**Deliverable:** Translations only visible to the user who requested them

---

### **Phase 4: User Preferences & Privacy** (Control)
*Goal: Users have fine-grained control over their translation experience*

**Tasks:**
- Expand Config schema:
  - `preferred_language` ✅ (already exists)
  - `auto_translate_enabled` (new)
  - `show_source_language` (new: show original text in footer?)
  - `preferred_translation_backend` (new: future flexibility for DeepL, etc.)
- Create preference subcommand group:
  - `[p]translate set language <lang>` → set preferred target language
  - `[p]translate set auto-translate <on/off>` → enable/disable auto-trigger
  - `[p]translate view-settings` → show current preferences
- Add per-guild admin settings (optional Phase 4B):
  - `guild_settings.auto_translate_allowed` (admins can disable auto-translate in channel)
  - `guild_settings.translation_log_enabled` (log translations for moderation, privacy-respecting)

**Key decisions:**
- **Privacy-first**: Log *only* metadata (language pair, timestamp), never actual message content
- **Distributed defaults**: Use language detection (Google Translate's feature) as fallback
- **Opt-in auto-translate**: Default is OFF, users must explicitly enable

**Deliverable:** Users have full control; privacy respected

---

### **Phase 5: Caching, Performance & Observability** (Polish)
*Goal: Sub-second translations, minimal API calls, easy debugging*

**Tasks:**
- Implement cache statistics:
  - Hit/miss ratio
  - Cache size monitoring
  - TTL expiration tracking
- Add debug logging:
  - `logger.debug(f"Cache hit: {language}:{text_hash}")` (never log full message)
  - `logger.warning(f"Rate limited: {guild_id} - retry in {retry_after}s")`
  - `logger.error(f"Translation failed: {error}")` (with context)
- Add cache purging on unload (cleanup)
- Optional: Persistent cache via Config for very frequent phrases
- Add metrics:
  - Average lookup time
  - Cache effectiveness
  - API call frequency

**Key decisions:**
- **Don't log user messages** - only log language pairs and timestamps
- **Cache keying**: `f"{target_lang}:{hash(content)}"` (deterministic, collision-resistant)
- **Cleanup on unload**: Clear in-memory cache, close HTTP session

**Deliverable:** Fast, efficient, observable cog

---

### **Phase 6: Testing & Hardening** (Quality)
*Goal: Reliable translation cog that handles edge cases gracefully*

**Tasks:**
- Unit tests for `translator.py`:
  - Test translation accuracy
  - Test cache behavior (hits, misses, TTL expiration)
  - Test rate limit handling
  - Test error recovery
- Integration tests for Discord interactions:
  - Ephemeral message delivery
  - Reaction-triggered translation
  - Config persistence
  - Permission checks
- Edge case handling:
  - Messages with custom emojis (already strips these)
  - Messages with links/URLs
  - Very long messages (> 3990 chars for embeds)
  - Empty messages
  - Rapid successive requests from same user

**Deliverable:** Robust cog with test coverage

---

## Architecture Overview (Phase 1)

### Module Interaction Diagram

```
┌──────────────────────────────────────────┐
│          Discord Server User             │
└──────────────────▲───────────────────────┘
                   │
        ┌──────────┴──────────┐
        │  main.py            │ (Discord interface)
        │ ──────────────────  │
        │ Commands:           │
        │ • /translate        │
        │ • [p]translate      │
        │ • Context menu      │
        └──────────┬──────────┘
                   │
        ┌──────────┴──────────┐
        │ _do_translate()     │
        └──────────┬──────────┘
                   │
        ┌──────────┴─────────────┐
        │ translator.py          │ (Pure logic)
        │ ──────────────────────│
        │ • translate()          │
        │ • detect_language()    │
        │ • normalize_language() │
        └──────────┬─────────────┘
                   │
        ┌──────────┴──────────┐
        │ cache.py            │ (Check cache)
        │ ──────────────────  │
        │ Hit? → Return       │
        │ Miss? → API call    │
        └──────────┬──────────┘
                   │
        ┌──────────┴──────────────────────┐
        │ Google Translate API            │
        │ (googletrans library)           │
        └──────────┬──────────────────────┘
                   │
        ┌──────────└──────────┐
        │ cache.py            │ (Store result)
        └──────────┬──────────┘
                   │
        ┌──────────└──────────┐
        │ strings.py          │ (Format embed)
        └──────────┬──────────┘
                   │
        ┌──────────└──────────────────────┐
        │ Discord Ephemeral Message       │
        │ (Visible only to user)          │
        └─────────────────────────────────┘
```

### Key Characteristics

- **No Coupling**: Each module has single responsibility
- **Type-Safe**: Full type hints throughout
- **Documented**: Google-style docstrings on every function
- **Tested** Built-in error handling and logging
- **Async-Safe**: All I/O operations non-blocking
- **Privacy**: Ephemeral responses keep channel clean
- **Performant**: Cache prevents redundant API calls
- **Maintainable**: Clear separation enables independent testing

---

## Overall Progress Tracker

| Feature | Phase | Status | Complete |
|---------|-------|--------|----------|
| Separate translator.py | 1 | ✅ Done | Yes |
| In-memory caching (LRU+TTL) | 1 | ✅ Done | Yes |
| Translation logic module | 1 | ✅ Done | Yes |
| Ephemeral responses | 1 | ✅ Done | Yes |
| User language preferences | 1 | ✅ Done | Yes |
| Text/Slash/Context commands | 1 | ✅ Done | Yes |
| Language autocomplete | 1 | ✅ Done | Yes |
| Error handling & messages | 1 | ✅ Done | Yes |
| Reaction emoji trigger | 2 | ⏳ Planned | No |
| Auto-translate system | 2 | ⏳ Planned | No |
| Per-guild admin controls | 4 | ⏳ Planned | No |
| Rate limit handling | 5 | ⏳ Planned | No |
| Background cache cleanup | 5 | ⏳ Planned | No |
| Unit tests | 6 | ⏳ Planned | No |
| Integration tests | 6 | ⏳ Planned | No |

---