# template_preserving_edit

Use this when the user provides a PPTX and wants content edited while preserving layout and style.

Workflow:
1. Never modify the original user PPTX.
2. Run `validate_ppt_request.py`.
3. Run `pptx_analyzer.py --mode inspect` and `--mode extract`.
4. Build `machine_extracted`.
5. Infer slide roles into `ai_inferred`.
6. Write Gorden edits with explicit address fields.
7. Run Gorden `build_pptx.py SOURCE_PPTX edits.json output.pptx --strict`.
