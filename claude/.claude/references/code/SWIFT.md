# SWIFT — language standard

Scope: Swift — iOS/macOS apps, Swift packages. Strength vocabulary per
`CODE-STANDARD.md`.

## Naming & casing

| Kind                                   | Casing                                    | Example                              |
| -------------------------------------- | ----------------------------------------- | ------------------------------------ |
| variables / functions / properties     | `camelCase`                               | `resolveUserSession`                 |
| constants (`let` at type/global scope) | `camelCase`                               | `let maxRetryCount = 3`              |
| types (class/struct/enum/protocol)     | `PascalCase`                              | `SessionManager`                     |
| protocols                              | `PascalCase`, often `-able`/`-ing` suffix | `Cacheable`, `Persisting`            |
| enum cases                             | `camelCase`                               | `case loading`, `case failed(Error)` |
| files                                  | `PascalCase.swift`, matching primary type | `SessionManager.swift`               |

- No Hungarian/type prefixes (`strName`, `bIsActive`) — Swift's type system
  makes them noise, not information.
- Acronyms follow the prevailing Swift API-guideline convention: capitalize
  consistently as a unit (`userID`, `htmlParser`, not `userId`/`hTMLParser`).

## Rules

- MUST use `let` by default; `var` only when reassignment genuinely happens.
  Prefer immutability the same way `const`-by-default applies in TypeScript.
- `guard` for early-exit/precondition checks over nested `if`; keeps the
  happy path unindented and the failure case explicit at the top of a
  function (matches this repo's universal "validate at boundaries" rule).
- Optionals: force-unwrap (`!`) is AVOID outside test code and genuinely
  provable invariants (each one needs a why-comment justifying the
  invariant). Prefer `if let`/`guard let` binding, `??` for defaults, or
  optional chaining (`?.`).
- MUST NOT use implicitly-unwrapped optionals (`var x: T!`) except the two
  conventional exceptions: `@IBOutlet` properties and dependency-injected
  properties set immediately after init in a two-phase-init pattern —
  both require a comment stating which exception applies.
- Value types (`struct`/`enum`) are the default; `class` is reserved for
  genuine reference semantics (shared mutable state, identity matters,
  inheritance needed, or a framework requires it — e.g. `UIViewController`).
- `final` MUST be the default on classes not designed for subclassing —
  opt into inheritance deliberately, not by omission.
- Error handling: `throws`/`try`/`catch` for recoverable errors conforming to
  `Error`; `Result<Success, Failure>` for async contexts predating
  structured concurrency or where the caller needs to hold a
  not-yet-handled outcome as a value. `fatalError`/`precondition` only for
  truly unrecoverable programmer-error states (never for expected runtime
  failure like a network error).
- Access control: MUST be as restrictive as correctness allows — `private`
  default, widen to `fileprivate`/`internal`/`public` only when a real
  caller outside that scope needs it. No implicit "everything is internal
  and nobody thought about it" default.
- Concurrency: prefer structured concurrency (`async`/`await`, `Task`,
  `TaskGroup`) over completion-handler closures in new code. Shared mutable
  state crossing concurrency domains MUST be protected — an `actor`, not a
  manually-locked class, unless a specific documented reason rules it out.
- MUST NOT retain-cycle a closure capturing `self` in a long-lived context
  (stored closure, `Task`, `Timer`, `NotificationCenter` observer) without
  `[weak self]`/`[unowned self]` — a short-lived, synchronously-executed
  closure (`map`, `sorted(by:)`) does not need it.

## File layout (SHOULD — top to bottom)

1. `import` statements — Foundation/system frameworks first, then third-party,
   then local modules, blank line between groups
2. Type declaration, with protocol conformances listed and each conformance's
   required members grouped under a `// MARK: - ProtocolName` comment when a
   type conforms to more than one
3. Stored properties (grouped: `let` constants, then `var` state)
4. Initializers
5. Public/internal methods — newspaper order, high-level first
6. Private helpers, below the methods that call them
7. Extensions for protocol conformance SHOULD live in a separate `extension`
   block per protocol (not crammed into the primary type body) — keeps each
   conformance's members grep-able and lets `// MARK:` label them cleanly.

## Directory structure (canonical minimum)

Ecosystem-standard shape (Xcode project or Swift Package Manager). An
existing project's layout always wins over this.

```
<AppName>/
├── <AppName>.xcodeproj/ or Package.swift
├── Sources/<AppName>/
│   ├── App/                # entry point, app-level config
│   ├── Models/              # value types, no UI/framework imports
│   ├── Views/                # SwiftUI views or UIKit view controllers
│   ├── ViewModels/           # or equivalent presentation layer
│   └── Services/             # networking, persistence, external APIs
└── Tests/<AppName>Tests/     # XCTest, mirrors Sources/ structure
```

- Minimum viable (SPM library): `Package.swift` + `Sources/<Target>/` +
  `Tests/<Target>Tests/`.
- Pure logic (`Models`, business rules) MUST stay importable with no
  `UIKit`/`SwiftUI` import — same UI/logic separation rule as every other
  language file in this directory.

## Testing

- XCTest (or swift-testing on newer toolchains) — tests colocated per target
  convention above; red-green per `/tdd`.
- View/UI logic SHOULD be tested via the ViewModel/presentation layer, not
  by driving the UI directly, wherever the architecture separates them —
  UI tests (XCUITest) are reserved for genuine end-to-end flows, since
  they're slow and brittle relative to unit tests.

## Tooling

- `swift-format` is the authoritative formatter where configured (or
  `swiftformat`, the third-party tool, if that's what the project uses —
  match the project's existing choice, don't introduce a second one).
- SwiftLint is the authoritative linter where a `.swiftlint.yml` exists —
  treat its findings as MUST-fix, not suggestions.
- `swift build`/`xcodebuild build` is the cheap verify gate; run before
  claiming done.
