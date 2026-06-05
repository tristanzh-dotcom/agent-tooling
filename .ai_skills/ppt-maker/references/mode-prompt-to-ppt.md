# prompt_to_ppt

Use this when the user wants a new PPT from a prompt or content brief.

Workflow:
1. Run `scripts/validate_ppt_request.py --mode prompt_to_ppt`.
2. Use Gorden Mode A by default.
3. Pick template candidates from Gorden `templates/INDEX.md`.
4. Generate an outline sized to target slide capacity.
5. Write Gorden `edits.json`.
6. Run Gorden `build_pptx.py ... --detail ... --strict`.
7. Produce QA report with `qa_mode`.

Fallback:
- Use Gorden Mode C only when templates are unsuitable or the user asks for simple original design.
