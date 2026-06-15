# Project Sentinel v3 Capturer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for every implementation task. This plan starts with Red tests only; business logic must remain unimplemented until the failing tests are reviewed.

**Goal:** Implement Automated Artifact Capturer as a deterministic, offline-testable media capture module that upgrades Agent07 from dummy thumbnails to real cached project artifacts without blocking Blind Scout.

**Architecture:** Capturer is a local TypeScript module behind injected boundaries: downloader, media processor, filesystem cleanup, clock, and scheduler. Tests must never call the public internet, `ffmpeg`, PDF renderers, ImageMagick, GraphicsMagick, or any other real native media toolchain.

**Tech Stack:** TypeScript, Node.js 22+, Vitest, local JSON files, injected mock I/O boundaries, existing Sentinel atomic JSON conventions.

---

## Source of Truth

- Capturer SDD: `/Users/tristanzh/agent/docs/superpowers/specs/2026-06-16-project-sentinel-v3-capturer-design.md`
- Work root: `/Users/tristanzh/agent/Git-Scout`
- Test target: `/Users/tristanzh/agent/Git-Scout/tests/sentinel/artifactCapturer.test.ts`
- Interface target: `/Users/tristanzh/agent/Git-Scout/src/sentinel/artifactCapturer.ts`

## File Map

```text
/Users/tristanzh/agent/Git-Scout/src/sentinel/artifactCapturer.ts
  Public Capturer types and Red-stage NotImplemented stubs.

/Users/tristanzh/agent/Git-Scout/tests/sentinel/artifactCapturer.test.ts
  Offline Red tests for concurrency, timeout, reject cleanup, and fallback mapping.
```

## Task 1: Red Tests and Interface Stub

- [ ] Create `src/sentinel/artifactCapturer.ts` with public contracts:
  - `captureArtifactsForLead(input)`
  - `cleanupArtifactsForRejectedRepo(input)`
  - injected `ArtifactDownloader`
  - injected `ArtifactMediaProcessor`
  - injected cleanup filesystem adapter

- [ ] Create `tests/sentinel/artifactCapturer.test.ts` with three failing tests:
  - concurrency limit plus 5000ms timeout allows queue progress after hung downloads abort
  - reject cleanup deletes the repo artifact sandbox directory through injected filesystem deletion
  - 404 image plus corrupt PDF maps `artifacts.local_thumb_path` to local fallback without uncaught exception

- [ ] Run:

```bash
cd /Users/tristanzh/agent/Git-Scout
npm run typecheck
npx vitest run tests/sentinel/artifactCapturer.test.ts
```

Expected:

```text
typecheck exits 0
artifactCapturer.test.ts fails only because captureArtifactsForLead and cleanupArtifactsForRejectedRepo are not implemented
```

- [ ] Commit:

```bash
cd /Users/tristanzh/agent
git add docs/superpowers/specs/2026-06-16-project-sentinel-v3-capturer-implementation-plan.md \
  Git-Scout/src/sentinel/artifactCapturer.ts \
  Git-Scout/tests/sentinel/artifactCapturer.test.ts
git commit -m "test(sentinel): 编写 Capturer 样张捕获器并发、清理与降级全量 TDD 单元测试"
```

## Task 2: Green Implementation Boundary

This task is intentionally not executed in this Red-stage commit.

Future Green implementation must:

- implement a bounded per-repo async scheduler;
- enforce `downloadTimeoutMs <= 5000`;
- write fallback paths before network work starts;
- update `scout_pipeline.json` through atomic JSON mutation;
- delete rejected repo artifact directories inside the sandbox only;
- keep tests offline by using injected mock dependencies.

## Red-Line Review Checklist

- No real network call in tests.
- No real `ffmpeg`, PDF renderer, ImageMagick, or GraphicsMagick invocation in tests.
- No business implementation in Red commit.
- Existing Sentinel tests must remain green when excluding the new Red test file.
