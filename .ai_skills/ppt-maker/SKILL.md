---
name: ppt-maker
description: Use when creating, editing, improving, restyling, remapping, or replacing templates for PowerPoint PPTX decks from prompts, user-provided PPT templates, existing decks, or content materials; also for 生成PPT、制作PPT、编辑PPT、替换PPT模板、PPT美化.
---

# ppt-maker

## Core Boundary

`ppt-maker` orchestrates PPT workflows and uses `/Users/tristanzh/agent/.ai_skills/gorden-ppt-skill` as the lower-level template/text-editing engine.

Hard rules:

- Never modify the original user PPTX in place.
- Do not promise arbitrary beautification or one-click redesign for every PPT.
- Run `scripts/validate_ppt_request.py` before mode-specific analysis.
- Run `scripts/pptx_analyzer.py` after validation when a source PPTX exists.
- Put work products under the current project root at `work/ppt-maker/<timestamp>/`.
- Use `qa_mode: structural_only` when render dependencies are missing.

## Mode Routing

| Mode | Use when | Reference |
|---|---|---|
| `prompt_to_ppt` | The user wants a new deck from a prompt, topic, outline, or content brief. | `references/mode-prompt-to-ppt.md` |
| `template_preserving_edit` | The user provides a PPTX and wants content changed while preserving layout/style. | `references/mode-template-preserving-edit.md` |
| `template_replacement` | The user wants an existing deck/content moved into a different template, theme, or visual style. | `references/mode-template-replacement.md` |

If the request is ambiguous, ask one concise clarification. Do not silently treat "make it better" as arbitrary visual redesign.

## Required Script Order

1. Run `scripts/validate_ppt_request.py` for mode inputs, Gorden compatibility, and QA mode.
2. If a source PPTX exists, run `scripts/pptx_analyzer.py --mode inspect` when a human inventory helps.
3. If the workflow needs structured source content, run `scripts/pptx_analyzer.py --mode extract`.

## References

- Read `references/schemas.md` when creating or consuming `machine_extracted`, `ai_inferred`, or QA report JSON.
- Read `references/qa-checklist.md` before claiming the output is ready.
- Read `references/capability-boundaries.md` before describing limitations to the user.
