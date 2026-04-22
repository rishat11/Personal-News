<!--
Sync Impact Report
- Version change: (template placeholders) → 0.1.0
- Modified principles: (placeholders) → Code Quality, Testing, UX Consistency, Performance, Simplicity
- Added sections: Quality Gates, Development Workflow & Definition of Done
- Removed sections: None
- Templates requiring updates:
  - ✅ c:\Users\Rishat\PycharmProjects\earn\earn\.specify\templates\plan-template.md (still uses Constitution Check gate placeholder; compatible)
  - ✅ c:\Users\Rishat\PycharmProjects\earn\earn\.specify\templates\spec-template.md (testing + measurable success already emphasized; compatible)
  - ✅ c:\Users\Rishat\PycharmProjects\earn\earn\.specify\templates\tasks-template.md (task organization supports DoD/testing gating; compatible)
- Follow-up TODOs:
  - None
-->

# earn Constitution

## Core Principles

### I. Code Quality (NON-NEGOTIABLE)
- Code MUST be readable, consistent, and maintainable over cleverness.
- Public interfaces (API surface, CLI, UI components, schemas) MUST be documented and stable.
- Complexity MUST be justified; prefer simpler designs that meet requirements.
- Changes MUST include appropriate error handling and clear, actionable failure modes.

### II. Testing Standards (NON-NEGOTIABLE)
- Every behavior change MUST include tests at the right level (unit, integration, contract/e2e).
- Bug fixes MUST include a regression test that fails before the fix and passes after.
- Tests MUST be deterministic and isolated (no reliance on real external services unless explicitly
  designated as e2e/smoke).
- CI MUST run the test suite and block merges on failures.

### III. UX Consistency & Accessibility
- User-facing behavior MUST be consistent across surfaces (copy, formatting, flows, error messages).
- UX changes MUST define acceptance scenarios that cover success, empty, loading, and error states.
- Accessibility MUST be treated as a functional requirement (keyboard navigation, semantics, contrast
  where applicable).

### IV. Performance Requirements
- Performance budgets MUST be defined for user-critical paths (e.g., p95 latency, render time,
  throughput) when relevant.
- Changes MUST avoid known performance regressions (unbounded queries, N+1, excessive allocations,
  blocking I/O on critical paths).
- Performance-sensitive work MUST be measurable (benchmarks, profiling notes, or before/after
  metrics) when claims are made.

### V. Dependency Hygiene & Simplicity
- Dependencies MUST be added only when they materially reduce risk or implementation cost.
- Prefer standard library / existing project patterns over introducing new abstractions.
- Deprecations and breaking changes MUST be explicit and planned (migration notes where applicable).

## Quality Gates

- Formatting/linting/type-checking (when applicable) MUST pass in CI.
- Code review is required for all non-trivial changes; reviewers MUST verify:
  - correctness and edge cases
  - tests cover intended behavior
  - UX consistency (if user-facing)
  - performance risks (if relevant)
- Logging/telemetry (where the project already uses it) MUST not leak secrets or PII.

## Development Workflow & Definition of Done

A change is "done" only when:
- Requirements and acceptance scenarios are updated and satisfied.
- Tests are added/updated and passing in CI.
- User-facing changes include UX consistency checks (copy, states, accessibility).
- Performance impact is considered and, when relevant, measured.
- Rollback/mitigation is feasible for production-impacting changes.

## Governance

- This constitution supersedes local conventions where they conflict.
- Amendments MUST:
  - state the motivation
  - update impacted templates/docs
  - include a migration plan when behavior or process changes
- Versioning follows SemVer:
  - MAJOR: incompatible governance/principle removals or redefinitions
  - MINOR: new principles/sections or materially expanded guidance
  - PATCH: clarifications and non-semantic edits

**Version**: 0.1.0 | **Ratified**: 2026-04-22 | **Last Amended**: 2026-04-22
