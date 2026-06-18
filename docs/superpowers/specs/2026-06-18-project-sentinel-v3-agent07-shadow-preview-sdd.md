# Project Sentinel v3 Agent07 Shadow Preview Safety SDD

## Scope

Agent07 runtime evidence sanitizes local artifact paths into the `shadow://` pseudo protocol to prevent leaking host filesystem topology. The UI currently treats any `.svg/.png/.jpg/.webp` suffix as previewable, so sanitized `shadow://...thumb.svg` values can be rendered as `<img src>`, producing browser broken-image text instead of decision evidence.

This fix is scoped to Agent07 preview eligibility and tests. It must not weaken path sanitization, expose local filesystem paths, or alter unrelated agents.

## Contract

- `shadow://` is a safe reference identifier, not a browser-loadable image URL.
- `agent07CanPreviewImage` and browser-side `canPreviewImage` must return `false` for `shadow://...` values even when the suffix is image-like.
- Runtime candidates with only `shadow://` artifact references must render in ledger-only evidence mode.
- The Artifacts Theater must not show a broken image icon or alt text for sanitized shadow references.
- Public app-local paths such as `/agent07-artifacts/...svg` and HTTP(S) image URLs may remain previewable.
- Repository-relative paths such as `assets/screenshots/demo.jpg` or `docs/playground.gif` are not browser-loadable from the Agent07 origin and must be treated as non-preview evidence references unless they are resolved into a public URL first.

## TDD Matrix

- Server-render test: a runtime lead with `shadow://...thumb.svg` must not render `<img src="shadow://...">`; it must render a ledger/placeholder state.
- Browser script test: selecting a runtime candidate whose `local_thumb_path` is `shadow://...thumb.svg` must keep the selected artifact image hidden and place the stage in `is-ledger-only`.
- Server and browser script tests: repository-relative image paths must not be rendered as `<img>` previews.
- Existing Agent07 service, DOM, telemetry, and runtime trigger tests must remain green.

## Git Guard

Commit only this SDD and Agent07 web QA files. Do not commit `Git-Scout/storage/` runtime outputs or unrelated dirty files.
