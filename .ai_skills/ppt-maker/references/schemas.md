# Schemas

## ppt-maker-machine-extracted/v1

Machine-only fields: source path, slide count, slide size, texts, charts, images, and tables.

Unsupported chart format:

```json
{"chart_type": "UNSUPPORTED", "supported": false, "raw_tag": "...pie3DChart", "error": "unsupported plot type ..."}
```

## ppt-maker-ai-inferred/v1

AI-only fields: deck title, audience, purpose, style intent, slide role, semantic summary, priority, and media policy.

## QA report

`structural_only`:

```json
{"qa_mode": "structural_only", "rendered_visual_verification": false}
```

`rendered_visual`:

```json
{"qa_mode": "rendered_visual", "rendered_visual_verification": true}
```
