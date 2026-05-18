---
name: firmware-linter
description: Lint and review embedded firmware code (C/C++) for best practices, safety, readability, and PR quality. Use when reviewing firmware PRs, checking embedded C or C++ code, auditing hardware abstraction layers, checking for magic numbers, reviewing ISR or HAL code, assessing function size and file organisation, or running a firmware code review. Trigger phrases: "lint my firmware", "review this firmware PR", "check my embedded code", "firmware code review", "check my C code for best practices", "review HAL changes", "check for magic numbers", "firmware PR review".
---

# Firmware Linter

Reviews embedded C/C++ firmware code for safety, readability, memory correctness, and PR quality.

## Workflow

When invoked with a file, diff, or PR:

1. **Read all changed or provided files** using Read/Glob tools
2. **Run each rule category** in order (Safety → Memory → Hardware → Naming → Readability)
3. **Report findings** grouped by severity: BLOCK | WARN | INFO
4. **Produce a PR verdict** at the end: ✅ APPROVE / ⚠️ NEEDS CHANGES / ❌ BLOCK

---

## Rule Categories

### 1. Safety & Undefined Behaviour (BLOCK on violation)

- **No implicit integer conversions** across signedness boundaries without explicit cast
- **Volatile correctness**: all hardware-mapped variables and ISR-shared variables must be `volatile`
- **No unbounded loops** without a timeout/counter escape path (especially in polling loops)
- **No use of `gets()`, `sprintf()` without bounds** — require `snprintf`, `fgets`
- **Out-of-bounds array access**: flag any index that is not bounds-checked before use
- **ISR functions must be short**: ISR bodies > 20 lines, or containing blocking calls, are a BLOCK
- **No `malloc`/`calloc`/`realloc`/`free`** inside ISR handlers or time-critical paths — flag as BLOCK

### 2. Memory Management (BLOCK on overflow risk, WARN on style)

- **Buffer writes**: every write to a fixed-size buffer must have a preceding or accompanying length check
- **Stack allocation of large objects**: arrays > 256 bytes on the stack inside a function are a WARN
- **Pointer arithmetic**: flag raw pointer arithmetic without bounds context
- **String operations**: `strcpy`, `strcat` without size guard are a BLOCK; `strlcpy`/`strncpy` with length are OK
- **No dynamic allocation in interrupt context** (BLOCK)

### 3. Hardware Abstraction (BLOCK on magic numbers)

- **No raw register magic numbers**: hex literals like `0x40021000`, `0x00000001` written directly to hardware registers outside of a dedicated driver/HAL file are a BLOCK
  - Exception: values inside `*_reg.h` or `*_hal.c/cpp` driver files are expected and allowed
- **No direct register access outside HAL layer**: peripheral register structs must not appear in application-layer files (`main.c`, task files, state machines)
- **Named constants for all pin/port assignments**: raw GPIO numbers without a `#define` or `constexpr` alias are a WARN
- **Clock and timer values must be derived from macros** (e.g. `SystemCoreClock / 1000`), not hardcoded

### 4. Naming & Style (WARN)

- **Header guards**: every `.h` file must have `#pragma once` or an `#ifndef` guard — missing guard is a WARN
- **File naming**: prefer `snake_case` for C files, consistent with the rest of the codebase
- **Type-aliased structs**: `typedef struct { ... } MyType_t;` style must be consistent within a file
- **Public API prefix**: functions in a module should share a common prefix matching the module name (e.g. `uart_init`, `uart_send` not `init_uart`, `UART_Send`)
- **No single-letter variables outside loop counters**: flag `int x`, `uint8_t d` etc. in non-loop scope

### 5. Code Readability (WARN on moderate, BLOCK on extreme)

- **Function comments**: every non-static function must have a comment above its signature (one-liner minimum). Missing = WARN.
- **Function length**:
  - > 200 lines: BLOCK — this is a god-function, must be split
  - 80–200 lines: WARN — suggest splitting
  - ≤ 80 lines: OK
- **File length**:
  - > 1000 lines: BLOCK — file does too much, split it
  - 500–1000 lines: WARN — consider splitting by responsibility
  - ≤ 500 lines: OK
- **One logical concern per file**: flag if a single `.c` file mixes unrelated subsystems (e.g. UART driver + business logic in the same file)
- **No commented-out code blocks**: dead code left in PRs is a WARN — it should be deleted or tracked in an issue

---

## PR Review Checklist

Run this when reviewing a PR (not just individual files):

### Required (BLOCK if missing)
- [ ] PR description includes a **change summary**: what changed, why, and any risk areas

### Strongly Expected (WARN if missing)
- [ ] Any ISR or HAL changes are **explicitly called out** in the PR description with justification
- [ ] No magic register hex values introduced outside driver files
- [ ] No new god-functions or monolith files added

### Good Practice (INFO)
- [ ] New functionality has test evidence (log output, unit test result, or hardware test note)
- [ ] All new public functions have a comment above the signature
- [ ] No commented-out code left in the diff

---

## Output Format

Structure your report like this:

```
## Firmware Lint Report

### BLOCK — Must fix before merge
- [file.c:42] Magic number 0x40021000 written directly to register outside HAL layer
- [isr_handler.c:88] ISR body is 34 lines and calls blocking function `HAL_Delay()`

### WARN — Should fix, reviewer discretion
- [sensors.c:210] Function `sensors_process_all()` is 150 lines — consider splitting
- [main.c:17] GPIO pin 5 used without named constant

### INFO — Nice to have
- [uart.c:33] New public function `uart_flush()` has no doc comment

### PR Verdict
❌ BLOCK — 2 blocking issues must be resolved before merge.
```

---

## Examples

### Magic number (BLOCK)
```c
// BAD — magic hex in application code
GPIOA->ODR = 0x00000010;

// GOOD — named constant in HAL layer
#define LED_PIN_MASK (1U << 4)
GPIOA->ODR = LED_PIN_MASK;
```

### Missing bounds check (BLOCK)
```c
// BAD
memcpy(dest, src, len);  // len unchecked

// GOOD
if (len <= sizeof(dest)) {
    memcpy(dest, src, len);
}
```

### Function without comment (WARN)
```c
// BAD
uint8_t calculate_checksum(uint8_t *buf, size_t len) { ... }

// GOOD
/* Returns CRC-8 checksum over buf[0..len-1]. */
uint8_t calculate_checksum(uint8_t *buf, size_t len) { ... }
```

### Volatile missing on ISR-shared variable (BLOCK)
```c
// BAD
bool data_ready = false;  // set in ISR, read in main loop

// GOOD
volatile bool data_ready = false;
```

---

## Notes for the Reviewer

- Apply rules strictly to new code in the diff; don't penalise pre-existing violations unless they're directly adjacent to the change
- If a file is legacy and untouched by this PR, note it as INFO only
- When in doubt about intent (e.g. a magic number that might be intentional), ask the author rather than auto-blocking
