# ppt-maker Pressure Scenarios

## 1. prompt_to_ppt: one-sentence prompt

Input: "帮我做一份 10 页的新能源汽车智能座舱趋势 PPT。"

Expected behavior:
- Classify as `prompt_to_ppt`.
- Use Gorden built-in templates unless the user requests original simple design.
- Generate outline first, then map to template slots.

## 2. template_preserving_edit: preserve template

Input: existing PPTX plus new content, with "保留这个模板，只更新内容".

Expected behavior:
- Classify as `template_preserving_edit`.
- Never modify the original file.
- Use explicit `address` edits.

## 3. template_replacement: template replacement style change

Input: existing PPTX plus "改成蓝色商务风".

Expected behavior:
- Classify as `template_replacement`.
- Extract content, select a target template, remap content, and build a new deck.
- Do not claim arbitrary mutation of the original visual system.

## 4. chart-heavy source into no-chart target

Expected behavior:
- Detect chart-heavy source.
- If the selected target has no native chart migration route, degrade to text/table summary or suggest a chart-capable template.

## 5. overlong bullets

Expected behavior:
- Shorten or split content across slides.
- Text must be shortened or split, not font-shrunk to fit.

## 6. non-commercial template constraint

Expected behavior:
- If the user asks to use Gorden built-in templates commercially, surface the non-commercial template constraint.
