# template_replacement

Use this when the user wants content moved into a new template, theme, or visual style.

Workflow:
1. Run `validate_ppt_request.py --mode template_replacement`.
2. Run `pptx_analyzer.py --mode inspect` and `--mode extract` on the source PPTX.
3. Build `machine_extracted` from the script output.
4. Create `ai_inferred` with deck purpose, style intent, slide roles, priorities, and media policy.
5. Select a target template: user-provided template first, Gorden built-in template second, simple original mode last.
6. Inspect target template roles, slots, capacities, cautions, and runtime-detected charts.
7. Map content into the target template using the priority order below.
8. Apply degradation rules and generate a new deck; never mutate the source deck.

Mapping priority:
1. role match
2. capacity match
3. semantic match

Chart-Heavy selection:
- Rank chart pages by chart type compatibility, runtime support, page semantic fit, text capacity, visual/content diversity, and user page-count target.
- Select the smallest set covering distinct chart intents.

Degradation:
- Too much text: shorten first, split second.
- Unsupported chart: text/table summary or alternate template.
- Unclear image importance without render: preserve and mark `needs_visual_confirmation`.
