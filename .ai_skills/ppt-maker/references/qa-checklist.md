# QA Checklist

Structural checks:
- no original file mutation
- no empty selected editable slots
- no stale sample text
- Gorden build used `--strict`
- chart migration uses runtime inspection
- caution pages do not receive precise decorative data mappings

Visual checks:
- `qa_mode: rendered_visual` only after PNG render review
- `qa_mode: structural_only` when render dependencies are missing
- unknown image importance is listed under `needs_visual_confirmation`
