# ARDUINO / EMBEDDED C++ — language standard

Scope: microcontroller firmware (jack-o: PlatformIO, SAMD21 Feather M0). The ruling
constraint is the hardware: tens of KB of RAM, no OS, runs forever. Every rule below
follows from that. Strength vocabulary per `CODE-STANDARD.md`.

## Naming & casing

| Kind | Casing | Example |
|---|---|---|
| variables / functions | `camelCase` (Arduino ecosystem norm) | `readBatteryVoltage` |
| constants | `UPPER_SNAKE`, `constexpr` | `constexpr uint8_t LED_PIN = 13;` |
| classes / structs / enums | `PascalCase` | `PumpkinEyeDriver` |
| pin assignments | named constants at top — a bare pin number in logic is banned | `SERVO_PIN` |
| files | `snake_case.cpp/.h` | `eye_driver.cpp` |

## Memory MUSTs (the rules that brick boards)

- **No `String` class** — heap fragmentation kills long-running firmware. Fixed
  `char` buffers + `snprintf`.
- **No `new`/`malloc` after `setup()`** — all allocation static or setup-time;
  the heap on a 32KB device is a loan you can't repay.
- `constexpr`/`const` + the smallest sufficient type (`uint8_t`, not `int`).
- `PROGMEM`/`F()` for string literals on AVR targets; SAMD has more flash headroom
  but large lookup tables still SHOULD be `const` (flash) not RAM.
- Watch stack depth: no recursion, no large locals in `loop()`-called functions.

## Timing MUSTs

- **Non-blocking `loop()`**: no `delay()` outside `setup()`. State machine +
  `millis()` scheduling (the same pure-SM discipline as the Lua/Python standards —
  and it makes logic host-testable).
- `millis()` rollover (~49 days): always `(now - last) >= interval` with unsigned
  arithmetic — never compare absolute times.
- Variables shared with ISRs MUST be `volatile`; ISRs stay short — set a flag,
  handle in `loop()`. No `Serial` prints inside an ISR.

## Rules

- `#pragma once` in every header.
- Error handling without exceptions (disabled in embedded builds): return status
  enums / bools; a failed sensor read MUST degrade visibly (LED code, serial log),
  never silently (universal hygiene rule).
- `Serial` debug output SHOULD be behind a compile-time flag (`#ifdef DEBUG_LOG`).
- AVOID C++ features that hide allocation: `std::vector`, `std::string`,
  `std::function`. Fixed arrays, function pointers, templates are fine.

## File layout (SHOULD — top to bottom)

`main.cpp` / `.ino`:
1. Includes
2. Pin + config constants (`constexpr`)
3. Types (enums for states, structs)
4. Globals — module state, hardware driver instances (statically allocated)
5. Helper functions — newspaper order
6. ISRs
7. `setup()` then `loop()` at the very bottom — `loop()` reads as the top-level
   state machine dispatch, nothing else

## Directory structure (canonical minimum — PlatformIO)

Ecosystem-standard shape. An existing repo's layout always wins.

```
<project>/
├── platformio.ini          # board, framework, deps — the build truth
├── src/
│   └── main.cpp            # entry: setup()/loop() + wiring, logic in modules
├── include/                # project headers
├── lib/                    # project-private libraries (each own dir)
└── test/                   # PlatformIO unit tests (host-runnable pure logic)
```

- Minimum viable: `platformio.ini` + `src/main.cpp`.
- Pure logic (state machines, protocol parsing) in `lib/` modules with no
  `Arduino.h` dependency where possible → testable on host without a board.

## Tooling

- PlatformIO build is the verify gate: `pio run` (compile) + `pio test` where
  host tests exist. clang-format when configured; match the file until then.
