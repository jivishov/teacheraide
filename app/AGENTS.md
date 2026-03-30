# AGENTS.md

## Scope
This file applies to the `app/` subtree and defines general guidance for maintaining Reflex applications in this project.

## Next Session Resume Protocol (No Full Repo Scan)
When a new session starts, do not rescan the full codebase. Use this focused sequence:
1. Read `../2026-02-17_implementation_checklist.md`.
2. Open only the in-flight files first:
   - `utils/llm_handlers.py`
   - `utils/local_storage.py`
   - `utils/question_upload.py`
   - `utils/docx_converter.py`
   - `pages/text_questions_page.py`
   - `pages/image_questions_page.py`
   - `components/reading_material_components.py`
   - `components/review_components.py`
   - `pages/review_page.py`
   - `states/text_questions_state.py`
   - `states/image_questions_state.py`
   - `states/reading_material_state.py`
   - `states/review_state.py`
   - `states/settings_state.py`
   - `../tests/test_docx_converter.py`
   - `../tests/test_settings_state.py`
   - `../tests/test_quality_gate_xml.py`
   - `../tests/test_review_state.py`
3. Verify current baseline before further edits:
   - `py -m py_compile app/utils/llm_handlers.py app/utils/local_storage.py app/utils/question_upload.py`
   - `py -m unittest discover -s tests -p "test_*.py" -v`
   - `py -m reflex run`
4. Proceed directly to unresolved checklist verification items instead of reopening unrelated modules.

## Post-Run Maintenance Rule
- At the end of every run/session, update both instruction files:
  - `../AGENTS.md`
  - `AGENTS.md` (this file)
- Record compact handoff notes:
  - newly discovered pitfalls and their fixes
  - environment/runtime quirks (for example interpreter/tooling behavior)
  - exact current implementation stage and immediate next tasks
- Write entries to reduce repeated debugging and speed up next-session continuation.

## Reflex Runtime
- Run the app with: `py -m reflex run`
- For this repository, this command is the canonical runtime path and uses Python 3.13.
- If debugging interpreter-specific issues, verify interpreter first with:
  - `py -c "import sys; print(sys.version)"`

## Reflex Development Workflow
1. Update state/events first (if needed), then UI wiring.
2. Keep event handlers in state classes (`@rx.event`) and keep UI declarative.
3. Reuse shared components before introducing new UI primitives.
4. Run syntax checks after edits:
   - `py -m py_compile <touched files>`
5. Validate app startup:
   - `py -m reflex run`

## State Management Rules
- Prefer existing state fields and handlers (`active_model`, `generation_stage`, `preflight_*`, etc.) over creating duplicates.
- Keep side effects centralized in state events.
- For persisted settings, call `SettingsState` setter methods (these save to disk).

## UI Rules
- Follow existing style conventions (`rx.el.*`, explicit text colors, existing Tailwind classes).
- Co-locate action buttons with relevant status/error messages.
- Add UI feedback for long-running operations (progress/stage labels, retry affordances).

## UI Delegation to Claude
- For UI-focused refinement tasks, delegate design/refinement suggestions to Claude Opus 4.6:
  - `claude --model claude-opus-4-6 -p "<prompt>"`
- Before running any `claude` delegation command, ask the user for explicit confirmation.
- If the user confirms, run the delegation command and apply/evaluate results.
- If the user does not confirm, continue without Claude delegation and proceed with local implementation.
- Keep delegation prompts narrow (single page/component at a time) to avoid long-running/stalled responses.

## Safety Constraints
- Do not modify YAML/QTI/XML formatting behavior unless explicitly requested.
- Avoid changing converter/template semantics while doing UI/state refinements.

## Quick Checks for Common Tasks
- Full page import/syntax sanity:
  - `py -m py_compile app/pages/*.py app/components/*.py app/states/*.py`
- Local tests:
  - `py -m unittest discover -s tests -p "test_*.py" -v`

## Session Notes (2026-02-18)
- Completed focused verification pass for the in-flight files listed in `../2026-02-17_implementation_checklist.md`.
- `py -m py_compile app/utils/llm_handlers.py app/utils/local_storage.py app/utils/question_upload.py` passed.
- `py -m unittest discover -s tests -p "test_*.py" -v` passed (7 tests).
- Runtime fix applied: `rxconfig.py` now excludes `nul` from hot-reload paths on Windows when that entry exists; `py -m reflex run` no longer throws watchfiles `FileNotFoundError`.
- Runtime hygiene note: repeated non-interactive startup checks can leave multiple `python -m reflex run` processes active and increment backend ports.
- Settings follow-up fix: `set_thinking_budget` now accepts `str|float|int` so numeric input `on_change` events no longer emit the type-mismatch warning; covered by `tests/test_settings_state.py`.
- UI clarity update: `Stage:` labels now show `Active model:` on text/image/reading generation UIs, reflecting active selection with default fallback.
- Quality-gate fix: for FIB questions, prompt text can exist in `itemBody` without a `<prompt>` element; quality checks now accept that structure (covered by `tests/test_quality_gate_xml.py`).
- Review-state fix: `_parse_xml` and `_quality_gate_for_export` now accept FIB prompt text from `itemBody`; prevents false `No prompt found` and export-blocked errors (covered by `tests/test_review_state.py`).
- DOCX parity fix: `utils/docx_converter.py` now falls back from `<prompt>` to `itemBody` text so FIB prompts without `<prompt>` are exported correctly in quiz papers.
- Review UI safeguard: `components/review_components.py` now suppresses the generic prompt line for FIB when `prompt_with_blanks` exists, preventing duplicate/misleading prompt output.
- Added tests: `../tests/test_docx_converter.py` covers prompt extraction for prompt-tag, itemBody fallback, and empty-prompt cases.
- Validation update: full `py -m unittest discover -s tests -p "test_*.py" -v` run now passes with 20 tests.
- Continuation validation: `py -m py_compile app/utils/yaml_converter.py app/utils/llm_handlers.py app/utils/question_upload.py app/utils/docx_converter.py` passed.
- Runtime continuation note: `py -m reflex run` still starts; backend can auto-move to port `8001` if `8000` is occupied.
- Git baseline is now present (`f3452e2`), enabling normal diff-guard verification from `HEAD`.
- Windows safeguard: `.gitignore` includes `nul` to avoid invalid-path errors while staging/committing.
- Checklist alignment update: remaining unified-plan gaps are tracked in `../2026-02-17_implementation_checklist.md` backlog section for prioritized follow-up.
- Cross-project export utility added at `../tools/convert_mole_tycoon_topics.py` to convert Mole Tycoon topic questions into this app's YAML shape and QTI packages (output under `../generated_questions/mole_tycoon_exports/`).
- Cross-project prompt refinement utility added at `../tools/refine_mole_tycoon_exports.py` to improve prompt clarity only, validate banks, and generate final QTI packages in `../generated_questions/mole_tycoon_exports/refined/`.
- Next action in app scope: keep using `git diff --name-only HEAD -- <protected paths>` before and after each phase.
- Added upload workflow-intent routing in `states/material_state.py` with explicit redirect events for text generation, image generation, and PDF question conversion.
- Added a third Upload page CTA in `pages/upload_material_page.py`: `Convert Uploaded Questions to Test`.
- Added conversion prompt function in `prompts/qti_prompts.py`: `create_pdf_question_conversion_prompt(...)`.
- Added Text Questions workflow mode support in `states/text_questions_state.py`:
  - mode resolution from upload intent (`generate` / `convert_pdf_questions`)
  - conversion mode skips manual question-count gating
  - conversion warning summary for partially skipped items (YAML count vs converted XML count).
- Added conversion-mode UI logic in `pages/text_questions_page.py`:
  - conversion banner
  - conversion action label
  - question-count section replaced with mode note
  - warning banner for skipped/unsupported items.
- Review empty-state hint now mentions PDF conversion path (`pages/review_page.py`).
- Added tests:
  - `../tests/test_text_questions_state.py`
  - `../tests/test_qti_prompts.py`
- Validation:
  - `py -m py_compile app/states/material_state.py app/states/text_questions_state.py app/pages/upload_material_page.py app/pages/text_questions_page.py app/pages/review_page.py app/prompts/qti_prompts.py tests/test_text_questions_state.py tests/test_qti_prompts.py`
  - `py -m unittest discover -s tests -p "test_*.py" -v` passed with 25 tests
  - `py -m reflex run` reached `App Running` (auto-port fallback to 8002 after 8000/8001 were occupied).
- Sticky-intent fix: conversion routing intent is now one-time (`MaterialState._consume_workflow_intent_once`) and reset to `generate_text` after Text Questions page load.
- Generation safeguard: `TextQuestionsState.handle_generate` no longer re-reads global `workflow_intent`, preventing stale intent from hijacking normal generation flow.
- Added `../tests/test_material_state.py` to lock this behavior; full suite now passes with 27 tests.
- OPEN backlog item `P2.2` addressed in `utils/llm_handlers.py`:
  - `GeminiAdapter.generate_text_questions` now processes PDF-backed text generation via `_gemini_generate` and returns unified completed stream event.
  - Removed unsupported-PDF runtime mismatch between Gemini capability flags and adapter behavior.
- Updated tests in `../tests/test_llm_handlers.py`:
  - asserts adapter no longer contains unsupported-PDF guard text
  - verifies Gemini text adapter uses decoded PDF bytes and emits final event shape.
- Validation update:
  - `py -m py_compile app/utils/llm_handlers.py tests/test_llm_handlers.py`
  - `py -m unittest discover -s tests -p "test_*.py" -v` passed with 29 tests
  - `py -m reflex run` reached `App Running` (backend auto-port fallback to 8006).
- OPEN backlog item `P2.6` addressed in `utils/combined_questions.py`:
  - added `sanitize_media_filename(...)` and enforced basename-only media path handling in package assembly.
  - unsafe/invalid media names are now rejected; duplicate names after sanitization are skipped with warnings.
- Added test coverage in `../tests/test_combined_questions.py`:
  - basename extraction
  - invalid filename rejection
  - ZIP packaging behavior for unsafe + duplicate media names.
- Validation update:
  - `py -m py_compile app/utils/combined_questions.py tests/test_combined_questions.py`
  - `py -m unittest discover -s tests -p "test_*.py" -v` passed with 32 tests
  - `py -m reflex run` reached `App Running` (auto-port fallback to 8007).
- OPEN backlog item `P2.7` addressed via new shared limits module `utils/input_limits.py`.
- Enforced upload limits with clear user errors:
  - PDF 25MB: `states/material_state.py`, `states/reading_material_state.py`
  - Image 3MB each: `states/image_questions_state.py`, `states/reading_material_state.py`
- Enforced long-text 10,000 char limit with clear user errors:
  - `states/text_questions_state.py` (`set_special_instructions`)
  - `states/image_questions_state.py` (`_set_prompt_at_index`)
  - `states/reading_material_state.py` (`set_topic`, `set_objectives`, `set_user_prompt`)
- Added tests in `../tests/test_input_limits.py`.
- Validation update:
  - `py -m py_compile app/utils/input_limits.py app/states/material_state.py app/states/text_questions_state.py app/states/image_questions_state.py app/states/reading_material_state.py tests/test_input_limits.py`
  - `py -m unittest discover -s tests -p "test_*.py" -v` passed with 38 tests
  - `py -m reflex run` reached `App Running` (auto-port fallback to 8008).
- OPEN backlog item `P2.10` addressed:
  - removed YAML token-count progress from streaming generation in `utils/llm_handlers.py`
  - normalized generation stage labels to `Validating -> Preparing -> Generating -> Parsing -> Packaging -> Ready`
  - replaced `Uploading/Preparing` with `Preparing` in text/image/reading flows.
- Added shared milestone helper `utils/generation_progress.py` and wired it into:
  - `states/text_questions_state.py`
  - `states/image_questions_state.py` (including explicit `Packaging` stage before summary/package-ready).
- Added regression coverage:
  - `../tests/test_generation_progress.py`
  - `../tests/test_llm_handlers.py` source assertion preventing reintroduction of `"- type:"` token-count progress.
- Validation update:
  - `py -m py_compile app/utils/generation_progress.py app/states/text_questions_state.py app/states/image_questions_state.py app/states/reading_material_state.py app/utils/llm_handlers.py tests/test_llm_handlers.py tests/test_generation_progress.py`
  - `py -m unittest discover -s tests -p "test_*.py" -v` passed with 41 tests
  - `py -m reflex run` reached `App Running` (auto-port fallback to 8009).
- OPEN backlog item `P2.11` addressed:
  - `utils/yaml_converter.py`: added `convert_with_warnings(...)` and retained `convert(...)` compatibility.
  - `utils/combined_questions.py`: added `create_package_with_warnings(...)` and retained `create_package(...)` compatibility wrapper.
  - `utils/question_upload.py`: added `parse_qti_package_with_report(...)` + `process_uploaded_questions_with_report(...)`.
- UI/state wiring:
  - `states/text_questions_state.py`: consumes YAML-converter warnings; surfaces warning count/message.
  - `states/image_questions_state.py` + `pages/image_questions_page.py`: consumes YAML-converter warnings and displays warning banner.
  - `states/review_state.py` + `components/review_components.py`: upload warning counts/details shown in modal.
  - `pages/review_page.py`: action-status banner now supports amber warning styling via `action_status_type`.
- Packaging warning surfacing:
  - text/image/review QTI download paths now use `create_package_with_warnings(...)` and surface warning counts to user-facing status fields.
- Added/updated tests:
  - `../tests/test_yaml_converter_warnings.py`
  - `../tests/test_combined_questions.py`
  - `../tests/test_question_upload.py`
- Validation update:
  - `py -m py_compile app/utils/yaml_converter.py app/utils/combined_questions.py app/utils/question_upload.py app/states/text_questions_state.py app/states/image_questions_state.py app/states/review_state.py app/components/review_components.py app/pages/review_page.py app/pages/image_questions_page.py tests/test_combined_questions.py tests/test_question_upload.py tests/test_yaml_converter_warnings.py`
  - `py -m unittest discover -s tests -p "test_*.py" -v` passed with 44 tests
  - `py -m reflex run` reached `App Running` (auto-port fallback to 8010).
- OPEN backlog item `P3.10` addressed:
  - `utils/local_storage.py`: replaced weak session token construction (`Date.now()+Math.random`) with crypto-backed generation:
    - primary: `window.crypto.randomUUID()`
    - fallback: `window.crypto.getRandomValues()` over 16 bytes.
  - Session token output remains underscore-free (`session-...`) for SharedState token constraints.
- Added test coverage:
  - `../tests/test_local_storage.py` now asserts crypto token APIs are present and weak random/time APIs are absent.
- Validation update:
  - `py -m py_compile app/utils/local_storage.py tests/test_local_storage.py`
  - `py -m unittest discover -s tests -p "test_*.py" -v` passed with 45 tests
  - `py -m reflex run` reached `App Running` (auto-port fallback to 8011).
- OPEN backlog item `P4.6` addressed:
  - added secure key-storage helper `utils/secure_storage.py` (OS keyring-backed).
  - `states/settings_state.py` now excludes API keys from JSON serialization and loads/saves keys via secure storage helpers.
  - implemented legacy migration path:
    - loads plaintext API keys from old settings files
    - migrates to secure storage when available
    - scrubs plaintext key fields from settings file afterward.
  - when secure storage is unavailable, keys remain session-only and settings status message communicates that state.
- Added tests:
  - `../tests/test_secure_storage.py`
  - extended `../tests/test_settings_state.py` to verify plaintext key exclusion/ignore behavior.
- Validation update:
  - `py -m py_compile app/utils/secure_storage.py app/states/settings_state.py tests/test_secure_storage.py tests/test_settings_state.py`
  - `py -m unittest discover -s tests -p "test_*.py" -v` passed with 49 tests
  - `py -m reflex run` reached `App Running` (auto-port fallback to 8012).
- Next app-scope task: backlog OPEN items are complete; continue with user-prioritized features/fixes.

## Session Notes (2026-02-21 - Reflex Warning Cleanup)
- Removed repeated sitemap startup warnings by explicitly disabling `reflex.plugins.sitemap.SitemapPlugin` in `../rxconfig.py`.
- Removed auto-setter deprecation warnings by defining explicit event setters used by current page bindings:
  - `states/material_state.py`: `set_page_selection`, `set_custom_pages`
  - `states/text_questions_state.py`: `set_selected_subject`, `set_assessment_title`, `set_content_type`
  - `states/image_questions_state.py`: `set_selected_subject`, `set_assessment_type`, `set_assessment_title`
  - `states/review_state.py`: `set_title`
- Validation:
  - `py -m py_compile rxconfig.py app/states/material_state.py app/states/text_questions_state.py app/states/image_questions_state.py app/states/review_state.py`
  - `py -m unittest discover -s tests -p "test_*.py" -v` (49 tests pass)
  - `py -m reflex run` reaches `App Running` with warning cleanup confirmed.
- Safeguard: when adding new `on_change=State.set_*` handlers, always implement a matching explicit state event to avoid Reflex 0.9 breakage.
- Current stage: runtime warning cleanup done; no app-scope backlog blocker introduced.
- Next app step: proceed with user-prioritized feature work; optional UI smoke check on touched bindings.

## Session Notes (2026-02-21 - Vendor Model List Management)
- Implemented provider model-list management on Settings page:
  - add/remove model IDs for OpenAI, Anthropic, and Gemini directly in the Model Selection cards.
- Updated `states/settings_state.py`:
  - added `new_openai_model_input`, `new_anthropic_model_input`, `new_gemini_model_input`
  - added `add_*_model` and `remove_*_model` handlers per vendor
  - selected model setters now enforce provider-list membership
  - settings serialization now persists provider model arrays
  - payload application now normalizes/deduplicates provider/custom arrays and clears invalid assignments.
- Updated `pages/settings_page.py`:
  - provider model cards now include inline add input/button and per-model remove action.
- Updated tests in `../tests/test_settings_state.py` for:
  - provider list persistence
  - payload normalization + invalid model cleanup
  - provider add/remove behavior.
- Validation:
  - `py -m py_compile app/states/settings_state.py app/pages/settings_page.py tests/test_settings_state.py`
  - `py -m unittest discover -s tests -p "test_*.py" -v` passed with 51 tests
  - `py -m reflex run` reaches `App Running` (only environmental WSL/port warnings observed).

## Session Notes (2026-03-16 - Text Questions Header Pill Grouping)
- Updated `pages/text_questions_page.py` advanced mode so `Quick Presets` and `Content Type` render as two distinct pill groups inside one responsive header strip.
- Replaced the active page's content-type radio list with three pills:
  - `rm_q` -> `From Material`
  - `siml_q` -> `Paraphrase`
  - `diffr_q` -> `New Topic`
- Native `title` hints are attached to the content-type pills; no state or prompt contract changed.
- Mobile safeguard: pill rows wrap below `md`; desktop keeps the grouped one-line strip with a vertical divider.
- Conversion-mode safeguard: content-type pills stay hidden and a compact locked note is shown in the header instead.
- Validation:
  - `py -m py_compile app/pages/text_questions_page.py`
  - `py -m unittest discover -s tests -p "test_*.py" -v` (73 tests passed)
  - `py -m reflex run` reached `App Running`
- Visual verification: checked with Playwright at desktop and mobile widths after the final wrap refinement.
- Follow-up refinement: content-type pills now use custom hover/focus hint cards instead of native browser tooltips.
- Tooling note: if Playwright reports `Opening in existing browser session`, clear the conflicting Chrome session before attempting hover-state verification again.
- Follow-up simplification: the inline content-type helper now renders only the explanation sentence; the `Selected Behavior` badge was removed to keep the header compact.
- Hot-reload note: Playwright may need a fresh navigation after page-only changes before snapshots reflect the updated helper markup.
- Follow-up layout change: `Cognitive Distribution` was moved from below the question-type steppers to directly under the `Quick Presets` pills so it aligns with the content-type helper block.
- Runtime note: if `py -m reflex run` exposes only the backend listener and the frontend port is unreachable, redo startup before using Playwright as a verification source.
- Follow-up density change: the cognitive color-key legend now lives in the title row beside `Cognitive Distribution`; the lower legend row was removed to save vertical space.
- Follow-up spacing change: the cognitive bar is thinner and both advanced-header helper cards use tighter vertical padding so their bottoms align more closely.
- Safeguard: removing a model now clears any function assignment using that exact model ID to prevent stale references.
- Current stage: settings vendor model management complete and test-covered.
- Next app step: optional manual smoke-check of add/remove flows and assignment dropdown updates in browser.

## Session Notes (2026-02-22 - UX Planning Artifact)
- Added root planning doc `../2026-02-22_teacher_fast_flow_ux_plan.md` defining fast-flow UX improvements for teacher efficiency.
- Plan keeps manual generate behavior and sets review default to fast-pass (`Needs Attention`) to reduce review time.
- Safeguard: no YAML/QTI/XML conversion/output formatting changes are included in the plan.
- Current stage: planning complete, code implementation pending.
- Next app step: implement phased changes behind `UX_QUICK_FLOW_V1` and validate with targeted tests.

## Session Notes (2026-02-25 - Text Questions V2 Functional Wiring)
- Wired `pages/text_questions_page_v2.py` to production `states/text_questions_state.py` and `states/settings_state.py`; v2 now executes real preflight/generation/conversion/package flows.
- Added v2-focused state controls in `states/text_questions_state.py`:
  - fields: `v2_ui_mode`, `v2_active_preset`
  - events: `set_v2_ui_mode`, `apply_v2_preset`, `set_v2_assessment_type`, `set_v2_content_type`, `increment_question_count`, `decrement_question_count`
  - computed vars: `is_v2_quick_mode`, `v2_estimated_output_label`, `v2_active_model_display`.
- `pages/text_questions_page_v2.py` now includes:
  - delete modal, conversion banner, quick/advanced form controls, sidebar preflight + generate/convert CTA, progress/stage, retry/error YAML debug view, warning banner, package-ready summary/actions.
  - `quick_model_switcher(...)` wired to existing model persistence/reset events.
- Route bootstrap update in `app.py`: `/text-questions-v2` now uses `on_load=TextQuestionsState.initialize_model_selection`.
- Added tests in `../tests/test_text_questions_state.py` for v2 preset mapping + count clamping + content/assessment v2 handlers.
- Validation:
  - `py -m py_compile app/app.py app/states/text_questions_state.py app/pages/text_questions_page_v2.py tests/test_text_questions_state.py`
  - `py -m unittest discover -s tests -p "test_*.py" -v` (55 pass)
  - `py -m reflex run` reached `App Running` (port fallback to `8001`).
- Safeguard: `pages/text_questions_page.py` (v1 reference) was not modified; keep v2-only changes isolated to v2 route/state helpers.

## Session Notes (2026-02-25 - Text V2 Progress UI Stall Fix)
- Addressed a perceived stall on `/text-questions-v2` where UI remained at `Stage: Validating` (`10%`) during generation.
- Cause: `handle_generate` stage/progress fields were updated but not yielded immediately, delaying frontend refresh until a later async yield.
- Fix: inserted explicit `yield` calls immediately after stage transitions (`Preparing`, `Generating`, `Parsing`, `Packaging`) in `states/text_questions_state.py`.
- Validation:
  - `py -m py_compile app/states/text_questions_state.py`
  - `py -m unittest discover -s tests -p "test_text_questions_state.py" -v`
  - `py -m unittest discover -s tests -p "test_*.py" -v` (55 pass)
  - `py -m reflex run` reached `App Running` (port fallback to `8002`).
- Safeguard: whenever long async events update user-facing stage text, emit an immediate `yield` after the stage assignment.

## Session Notes (2026-02-25 - Image Questions V2 Functional Wiring)
- Wired `pages/image_questions_page_v2.py` to production `states/image_questions_state.py` and `states/settings_state.py`; v2 now executes real preflight/generation/package flows.
- Route bootstrap update in `../app.py`: `/image-questions-v2` now uses `on_load=ImageQuestionsState.initialize_model_selection`.
- Replaced mock UI behavior in `pages/image_questions_page_v2.py` with:
  - quick/advanced toggle
  - working generate CTA + progress/stage/status sidebar
  - warning banner, package-ready actions, and delete modal wiring
  - top-level batch upload plus per-row image replace upload.
- Added v2-focused state controls in `states/image_questions_state.py`:
  - fields: `v2_ui_mode`, `v2_expanded_slot`, `v2_batch_question_type`, `v2_special_instructions`
  - events: `set_v2_ui_mode`, `toggle_v2_slot`, `add_v2_slot`, `remove_v2_slot`, `set_v2_batch_question_type`, `set_v2_special_instructions`, `handle_v2_batch_upload`
  - computed vars: `v2_is_quick_mode`, `v2_total_slots`, `v2_images_ready_count`, `v2_can_generate`, `v2_active_model_display`.
- Stage-refresh parity fix: inserted explicit `yield` calls after generation stage transitions in `handle_generate` to avoid UI appearing stuck at early progress.
- Prompt behavior update: v2 global special instructions are appended to each per-image prompt before template generation.
- Added tests in `../tests/test_image_questions_state_v2.py` for v2 mode controls, slot math, batch type propagation, and instruction-limit enforcement.
- Validation:
  - `py -m py_compile app/app.py app/states/image_questions_state.py app/pages/image_questions_page_v2.py tests/test_image_questions_state_v2.py`
  - `py -m unittest discover -s tests -p "test_image_questions_state_v2.py" -v` (5 pass)
  - `py -m unittest discover -s tests -p "test_*.py" -v` (60 pass)
  - `py -m reflex run` reached `App Running` (port fallback to `8003`).
- Safeguard: keep `pages/image_questions_page.py` (v1 reference) untouched and isolate iteration work to v2-specific route/page/state events.

## Session Notes (2026-03-03 - Unit 2 HTML Formatting Pass)
- Updated `../html_questions/Unit 2.html` (content artifact) to restore required prompt tables, correct malformed reaction arrow characters, and convert embedded BMP data URIs to PNG.
- Verification used targeted Python checks:
  - prompt table blocks present in affected questions (`q2`, `q3`, `q5`, `q15`, `q17`, `q23`)
  - no remaining `data:image/bmp` URIs
  - no remaining private-use malformed reaction-arrow characters.
- Safeguard: if future exports collapse prompt tables into inline text, reapply table reconstruction before delivery.

## Session Notes (2026-03-03 - Unit 2 Diagram Choice Labeling Pass)
- Updated `../html_questions/Unit 2.html` (content artifact) for diagram-answer usability:
  - added explicit `A`-`D` labels directly above diagram images in `q7`, `q11`, `q13`, `q14`, `q16`, `q18`, `q24`
  - replaced trailing `[See diagram]` placeholders with explicit labeled-choice text.
- `q7` heading fix: added distinct `Before Displacement` and `After Displacement` headings.
- `q16` handling detail: kept figure 1 as the setup/reference image and labeled only figures 2-5 as answer options.
- `q12` follow-up: moved `Before`/`After` into a dedicated centered heading row above the reaction diagram (no tab-based stem spacing).
- `q22` follow-up: replaced collapsed diatomic-set prompt text with a structured reference table and corrected stem wording to `graph below`.
- `q22` choices follow-up: expanded choice labels from `(A)/(B)/(C)/(D)` to explicit set mappings in the choice text for faster scanning.
- `q26` follow-up: corrected stem wording from `represented above` to `represented below`.
- Sub/sup follow-up: converted plain hybridization text in prompts/choices from `sp2/sp3` to superscript notation (`sp<sup>2</sup>`, `sp<sup>3</sup>`) where applicable.
- Verification: targeted Python checks confirmed label alignment and zero remaining `[See diagram]` placeholders in `Unit 2.html`.
## Session Notes (2026-03-03 - Unit 5 HTML Formatting Cleanup)
- Applied targeted content-format cleanup in `../html_questions/Unit 5.html` to improve prompt readability and preserve chemistry notation fidelity.
- Introduced reusable `.prompt-table` styles and converted flattened prompt datasets into tabular HTML for affected references (Q4, Q7, Q9, Q10, Q30, Q31, Q33).
- Normalized invalid chemistry symbols and special glyphs to standards-compliant HTML entities, including reaction/equilibrium arrows and superscripts.
- Transcoded embedded BMP data URIs to PNG data URIs for browser compatibility (29 conversions).
- Safeguard: kept changes scoped to Unit 5 HTML only; no app state/pipeline code touched.
## Session Notes (2026-03-03 - Unit 4 HTML Formatting Cleanup)
- Updated `../html_questions/Unit 4.html` with prompt-format and chemistry-notation cleanup while keeping question content/answers unchanged.
- Added `.prompt-table` layout and converted collapsed reference data into proper tables for Q3, Q18, Q25, Q29, Q32, Q33, Q34, Q45, Q48, and Q50.
- Corrected malformed reaction/thermodynamic notation (`→`, `⇌`, `ΔH°`, `ΔS°`) and normalized visible temperature text to `°C`.
- Converted embedded image URIs from BMP to PNG for all inline figures in the file (`70` converted, `0` BMP remaining).
- Validation:
  - targeted Python checks for table insertion, image MIME conversion counts, and private-use glyph removal.
- Safeguard: text cleanup was applied on DOM text nodes only to avoid accidental mutation of base64 image data.
## Session Notes (2026-03-03 - Unit 4 Follow-up Formula + Table Corrections)
- Applied follow-up cleanup in `../html_questions/Unit 4.html` based on review feedback:
  - normalized additional subscript/superscript chemistry formatting across affected questions,
  - removed duplicate misplaced Q12 text in metadata,
  - converted Q44 run-on measurement line into a structured `.prompt-table`.
- Corrected ion charge rendering to superscript style where needed (e.g., `MnO4−`, `Mn2+`, `Ni2+`, `Zn2+`, `Cu2+`, `Ca2+`, `H+`, `OH−`, `CO3^2−`).
- Validation:
  - pattern checks confirm targeted malformed variants are removed,
  - Q44 now includes an in-stem table and no concatenated measurement line,
  - image MIME check remains stable (`data:image/bmp` absent).
- Safeguard: replacements were constrained to HTML/text tokens only to avoid accidental edits to embedded image payloads.
## Session Notes (2026-03-03 - Unit 5 Follow-up Chemistry Formatting Fixes)
- Updated `../html_questions/Unit 5.html` to resolve remaining notation and layout defects after initial cleanup.
- Fixed residual chemical formula misses:
  - `N<sub>2</sub>O5` -> `N<sub>2</sub>O<sub>5</sub>` in Q7 reference and choices.
  - `X<sub>2</sub>Z2` -> `X<sub>2</sub>Z<sub>2</sub>` in Q8 stem.
- Improved prompt/mechanism readability where text was still flattened:
  - Q17 mechanism comparison converted to a structured two-column `prompt-table` (`mechanism-table`).
  - Q21 mechanism prompt converted from tabbed inline text to aligned `.mechanism` rows with proper `&minus;` thermochemistry notation.
  - Q22 mechanism answer choices reformatted into aligned multi-line mechanism blocks.
- Removed residual tab/spacing artifacts in question prose (notably Q18, Q29, Q35).
- Validation:
  - pattern scans show no remaining `N<sub>2</sub>O5`, `X<sub>2</sub>Z2`, tab characters, or `data:image/bmp` entries.
  - quick structural counts: `prompt-table=8`, `mechanism blocks=13`, `png-uri=32`, `bmp-uri=0`.
- Safeguard: edits were applied to HTML text/markup only; embedded base64 image payloads were not modified.
## Session Notes (2026-03-03 - Unit 4 Q2 Diagram Label Fix)
- Applied targeted UI readability fix in `../html_questions/Unit 4.html` for Question 2:
  - inserted explicit in-flow diagram labels `A.`/`B.`/`C.`/`D.` above choice images 2-5.
- Added `.choice-image-label` styling to keep labels centered and visually distinct from stem text.
- Validation:
  - verified four labels are present in `q2`
  - verified style class is present
  - verified no BMP image URI regression.
## Session Notes (2026-03-03 - Unit 4 Font Legibility Update)
- Applied a readability-focused font update in `../html_questions/Unit 4.html`:
  - `body` now uses `'Segoe UI', 'Segoe UI Symbol', 'Arial', sans-serif`.
- Purpose: make Unicode chemistry sub/superscript characters easier to distinguish in-page.
- Validation:
  - confirmed the new font stack is active in the stylesheet.
## Session Notes (2026-03-04 - Unit HTML Chemistry Font Alignment)
- Updated main body font stack to 'Segoe UI', 'Segoe UI Symbol', 'Arial', sans-serif in html_questions/Unit 1.html, Unit 2.html, Unit 3.html, Unit 5.html, Unit 6.html, Unit 7.html, and Unit 8.html.
- Scope guard: changed only the primary body font-family line in each target file; no content/layout/equation/table/image-data edits.
- Validation: confirmed old serif stack (Georgia/Times New Roman) is absent from all seven targets and new font line is present in each file.
- Next concrete step: optional browser spot-check for glyph legibility consistency across all unit pages.

## Session Notes (2026-03-05 - Unit 5 Sub/Superscript Audit Pass)
- Reviewed all question blocks in `../html_questions/Unit 5.html` with targeted scans for plain formula digits/charges outside `<sub>/<sup>` markup.
- Fixed one chemistry-formatting defect in Q35 reference equation:
  - `Fe<sub>2</sub>O3` -> `Fe<sub>2</sub>O<sub>3</sub>`.
- Validation:
  - post-fix per-question scan reports no remaining plain formula-digit tokens in question text.
  - post-fix charge-pattern scan reports no remaining charge-format misses in question text.
- Safeguard: only text markup was edited; no table structure or embedded base64 image payloads were changed.

## Session Notes (2026-03-05 - Unit 5 Answer Key Completion)
- Backed up `../html_questions/Unit 5.html` to `../html_questions/Unit 5.backup_2026-03-05_101745.html` before edits.
- Marked correct answers for previously-unmarked questions:
  - Q2=C, Q4=B, Q5=C, Q9=B, Q10=C, Q20=D, Q21=C, Q29=D, Q30=D, Q32=D.
- Validation: scan confirms all 38 questions in `Unit 5.html` now have exactly one `.choice.correct`.
## Session Notes (2026-03-05 - Unit 2 Charge Superscript Audit)
- Ran a full Unit 2 question text-format pass focused on chemistry sub/superscript correctness in `../html_questions/Unit 2.html`.
- Corrected ion charge rendering to superscript style in Q1 and Q23 (e.g., `Mg2+`, `Ca2+`, `O2−`, `Na+`, `F−`, `Cl−`, `Br−`).
- Validation:
  - targeted scan confirms legacy patterns such as `Mg<sub>2</sub>+` / `O<sub>2</sub>–` no longer appear
  - targeted scan confirms updated superscript tokens are present in those questions.
- Safeguard: modifications were limited to visible HTML question text; no base64 image payload content was edited.

## Session Notes (2026-03-05 - Unit 1 Chemistry Sub/Superscript Audit)
- Completed a full Unit 1 question text-format audit in `../html_questions/Unit 1.html` with focus on chemical formula/ion sub/superscripts.
- Corrected formatting in Q3, Q5, Q14, Q17, Q20, Q26, Q30, Q34, and Q37 (charge superscripts and missing formula subscripts).
- Validation:
  - targeted malformed-token scans return zero residual matches
  - post-fix structural checks return no remaining `subscript+charge` or `parenthesis-digit-without-subscript` chemistry defects.
- Safeguard: replacements were limited to visible text/markup tokens only; base64 image data was not edited.
- Next concrete step: optional browser render spot-check for Unit 1 chemistry notation legibility.

## Session Notes (2026-03-05 - Unit 1 Q8 Percent Formatting Fix)
- Applied a targeted formatting correction in `../html_questions/Unit 1.html` (Question 8 stem):
  - `40. percent` -> `40%`
  - `60. percent` -> `60%`
- Validation: targeted search confirms corrected percent text and no remaining old token variant.
- Safeguard: single-line text change only; no base64 image payload or layout structure edits.

## Session Notes (2026-03-05 - Percent Formatting Follow-up Scan)
- Ran a cross-unit check in `../html_questions/Unit *.html` for malformed percent notation (`\d+\. percent`).
- Result: no remaining matches; no additional HTML changes were needed.
- Validation: regex scan on per-question text extraction.

## Session Notes (2026-03-06 - Unit 1 Corrected Answer-Key Output)
- Generated `../html_questions/Unit 1_corrected.html` from `../html_questions/Unit 1.html` using a user-provided BeautifulSoup answer-key script.
- Safeguard: source `Unit 1.html` remained unchanged during this step; answer-key updates were written only to the corrected output file.
- Validation: a post-run scan confirmed 40/40 questions in `Unit 1_corrected.html` have exactly one marked correct choice.

## Session Notes (2026-03-05 - Number+Percent Notation Normalization)
- Executed a `number percent` -> `number%` normalization across affected `../html_questions/Unit *.html` question content.
- Updated files: Unit 1, Unit 2, Unit 4, Unit 5.
- Validation: zero remaining regex matches for `\d+(\.\d+)?\s+percent` in per-question text.
- Safeguard: edits were notation-only; no layout/image-data changes.

## Session Notes (2026-03-05 - Unit 1 Missing Answer Key Completion)
- Filled in missing marked-correct choices in `../html_questions/Unit 1.html` (Q3, Q4, Q5, Q24, Q26, Q31).
- Backup created before marking: `../html_questions/Unit 1.backup_2026-03-05_102231.html`.
- Validation: scripted scan confirms every question has exactly one `.choice.correct` + `correct-marker`.

## Session Notes (2026-03-05 - Unit 6 Missing Answer Key Completion)
- Filled in missing marked-correct choices in `../html_questions/Unit 6.html` (Q5, Q8, Q10, Q11, Q12, Q23, Q24, Q26, Q27, Q30, Q32, Q35).
- Backup created before marking: `../html_questions/Unit 6_backup_2026-03-05_101844.html`.
- Validation: scripted scan confirms every question has exactly one `.choice.correct` + `correct-marker`.

## Session Notes (2026-03-07 - Unit 7 BNK Reconciliation)
- `../html_questions/Unit 7.html` was reconciled against `../html_questions/CED Secure and Released Unit 7.bnk` using `bnk_viewer.py` and browser screenshots.
- Important extraction detail: Q1 answer choices live in EMF vector payloads, not plain text; rendered them to `../html_questions/q1_missing_answer_figures/q1_choice_*.png` and referenced those assets from the HTML.
- Follow-up fixes covered split stem/reference text, diagram labeling for image-based options, and the last residual Q39 choice mismatch.
- Validation path: `py __u7_validate.py`, `py __u7_final_audit.py`, and Playwright screenshots of `Unit 7.html#q1`.
- Next concrete step: if standalone self-contained HTML is required later, replace the external Q1 PNG references with a browser-supported inline representation after verifying the rendering path.

## Session Notes (2026-03-07 - Unit 2 Answer Key Correction)
- Re-solved all 29 questions in `../html_questions/Unit 2.html`, including image-based items checked in a rendered browser view, and updated the marked-correct choice in the HTML.
- Backup created before overwrite: `../html_questions/Unit 2.backup_2026-03-07_081410.html`.
- Final key applied: Q1 C, Q2 A, Q3 A, Q4 B, Q5 A, Q6 A, Q7 A, Q8 D, Q9 D, Q10 A, Q11 C, Q12 D, Q13 D, Q14 A, Q15 C, Q16 D, Q17 D, Q18 C, Q19 C, Q20 B, Q21 A, Q22 A, Q23 D, Q24 C, Q25 C, Q26 B, Q27 B, Q28 C, Q29 B.
- Validation: scripted scan confirmed every question has exactly one `.choice.correct` marker and that all 29 match the applied key.

## Session Notes (2026-03-11 - OpenAI Timeout + Files API Fix)
- `utils/llm_handlers.py` now uses the OpenAI Files API for PDF-backed Responses requests (`purpose="user_data"`) and caches file handles server-side so repeated runs reuse the same `file_id` instead of re-sending inline base64 PDF payloads.
- Timeout profile update: provider clients now use `30s` connect, `600s` read, and `120s` write timeouts to avoid premature failures on long reasoning-model first-token latency.
- Cleanup safeguard: PDF replacement/clear flows now release cached OpenAI file handles from `states/material_state.py` and `states/reading_material_state.py`.
- Added regression coverage in `../tests/test_llm_handlers.py` for cached upload reuse, file deletion on cleanup, adapter `input_file` ordering, and the longer timeout profile.
- Validation:
  - `py -m py_compile app/utils/llm_handlers.py app/states/material_state.py app/states/reading_material_state.py tests/test_llm_handlers.py`
  - `py -m unittest discover -s tests -p "test_*.py" -v` (64 passed)
  - `py -m reflex run` reached `App Running` on backend port `8001`; the spawned validation server tree was terminated afterward.

## Session Notes (2026-03-11 - Latest Model Catalog Refresh)
- Added `utils/model_catalog.py` to centralize default model lists, runtime capabilities, and provider-specific request hints.
- OpenAI updates:
  - default catalog now includes `gpt-5.4`
  - model-aware reasoning-effort normalization now prevents invalid effort values from reaching incompatible models
  - GPT-5 question-generation calls now request low verbosity; GPT-5 reading-material calls use medium verbosity.
- Anthropic updates:
  - default catalog now includes `claude-opus-4-6` and `claude-sonnet-4-6`
  - Claude 4.6 requests now use `thinking.type="adaptive"` via helper logic because the installed Anthropic SDK warns that `thinking.type="enabled"` is deprecated for newer Claude models.
- Fallback defaults in text/image/reading states now prefer `gpt-5.4` and `claude-sonnet-4-6` when no persisted selection exists.
- Added regression coverage in `../tests/test_llm_handlers.py` and `../tests/test_settings_state.py` for latest model presence, model-aware OpenAI effort handling, Claude 4.6 adaptive thinking, and new reasoning-effort options.
- Validation:
  - `py -m py_compile app/utils/model_catalog.py app/utils/llm_handlers.py app/states/settings_state.py app/states/text_questions_state.py app/states/image_questions_state.py app/states/reading_material_state.py app/states/v2_mock_state.py app/pages/settings_page.py app/pages/reading_material_page_v2.py tests/test_llm_handlers.py tests/test_settings_state.py`
  - `py -m unittest discover -s tests -p "test_*.py" -v` (69 passed)
  - `py -m reflex run` reached `App Running` on backend port `8001`; the spawned validation server tree was terminated afterward.

## Session Notes (2026-03-11 - Model Catalog Refinement)
- Review follow-up fixed a partial regression where the central catalog still pointed `gpt-5.4`/Claude 4.6 names at older models while tests and some UI paths expected the latest IDs directly.
- `utils/model_catalog.py` now:
  - keeps `gpt-5.4`, `claude-opus-4-6`, and `claude-sonnet-4-6` as first-class entries
  - canonicalizes stale Anthropic 4.5 aliases to 4.6
  - exposes runtime gating for `gpt-5.4-pro` so it cannot execute without an explicit future UI confirmation step
  - maps the shared reasoning setting onto Claude 4.6 adaptive-thinking effort values.
- `states/settings_state.py` now canonicalizes provider model IDs on add/select/load so persisted stale aliases do not leak back into dropdowns or assignments.
- `states/v2_mock_state.py` and `pages/reading_material_page_v2.py` now derive model pickers from catalog-backed lists instead of hardcoded strings.
- Validation:
  - `py -m py_compile app/utils/model_catalog.py app/utils/llm_handlers.py app/states/settings_state.py app/states/v2_mock_state.py app/pages/settings_page.py app/pages/reading_material_page_v2.py tests/test_llm_handlers.py tests/test_settings_state.py`
  - `py -m unittest discover -s tests -p "test_*.py" -v` (72 passed)
  - `py -m reflex run` reached `App Running` on backend port `8001`; existing Reflex invalid-icon warnings (`check_circle`, `loader_2`) remain and the spawned server tree was terminated afterward.

## Session Notes (2026-03-11 - Unit 3 Answer Key Correction)
- Housekeeping note for HTML bank maintenance: `../html_questions/Unit 3.html` was updated to the fully verified answer key after diagram-by-diagram review and comparison against rendered choices.
- Backup created before edit: `../html_questions/Unit 3.backup_2026-03-11_144356.html`.
- Verification shortcut for future sessions: run `py html_questions/__compare_unit3_answers.py` from repo root; expected result is `Mismatches: 0`.

## Session Notes (2026-03-11 - Unit 4 Backup Answer Key Correction)
- HTML-bank maintenance note: `../html_questions/Unit 4_backup_2026-03-05_101720.html` is now the visually verified Unit 4 source with all 50 answers marked.
- Backups created before backup-file edits:
  - `../html_questions/Unit 4_backup_2026-03-05_101720.pre_playwright_fix.html`
  - `../html_questions/Unit 4_backup_2026-03-05_101720.pre_answer_marking.html`
- Playwright verification was used against the backup file because `../html_questions/Unit 4.html` was reported as visually distorted; after HTML normalization the previously failing embedded diagrams rendered correctly.
- Verified unanswered-set key applied to the backup file:
  - `Q3 D`, `Q5 B`, `Q7 B`, `Q11 A`, `Q18 A`, `Q22 B`, `Q23 B`, `Q24 C`, `Q27 B`, `Q29 C`, `Q30 C`, `Q32 D`, `Q33 D`, `Q34 B`, `Q44 D`, `Q45 A`, `Q49 C`, `Q50 A`
- Quick validation shortcut: check `../html_questions/Unit 4_backup_2026-03-05_101720.html` for `50` occurrences each of `class="choice correct"` and `class="correct-marker"` after future maintenance.

## Session Notes (2026-03-16 - V2 Question Page Promotion)
- Promoted the V2 generation UIs into the base page modules:
  - `pages/text_questions_page.py` now contains the active V2 layout.
  - `pages/image_questions_page.py` now contains the active V2 layout.
- Preserved the previous live layouts as legacy V0 pages:
  - `pages/text_questions_page_v0.py`
  - `pages/image_questions_page_v0.py`
- Added compatibility wrappers:
  - `pages/text_questions_page_v2.py`
  - `pages/image_questions_page_v2.py`
  These re-export the active V2 pages so older imports do not break.
- Route wiring in `app.py` now maps:
  - `/text-questions` and `/image-questions` -> active V2 pages
  - `/text-questions-v0` and `/image-questions-v0` -> legacy pages
- Validation:
  - `py -m py_compile app/app.py app/pages/text_questions_page.py app/pages/text_questions_page_v0.py app/pages/text_questions_page_v2.py app/pages/image_questions_page.py app/pages/image_questions_page_v0.py app/pages/image_questions_page_v2.py`
  - `py -m unittest discover -s tests -p "test_*.py" -v` (`72` passed)
  - `py -m reflex run` reached `App Running`; unchanged Reflex icon warnings still appear for legacy invalid icon tags.
- Safeguard: when future work says “text questions page” or “image questions page,” assume the base filenames are the active V2 targets; use the `_v0` files only for regression comparison or deliberate legacy fixes.

## Session Notes (2026-03-16 - Settings Model List Refresh)
- Catalog defaults now drive the Settings page to show:
  - OpenAI: `gpt-5.4`, `gpt-5.2`, `gpt-5.1`, `gpt-5-mini`
  - Anthropic: `claude-opus-4-6`, `claude-sonnet-4-6`, `claude-haiku-4-5`
- `utils/model_catalog.py` now treats `claude-haiku-4-5` as the canonical Haiku model name; legacy `claude-3-5-haiku-latest` values canonicalize to it for backward compatibility.
- `states/settings_state.py` now persists `provider_model_catalog_revision` and rewrites saved provider lists to the current defaults on first load after a catalog refresh while preserving valid current selections.
- Validation:
  - `py -m py_compile app/utils/model_catalog.py app/states/settings_state.py tests/test_settings_state.py tests/test_llm_handlers.py`
  - `py -m unittest discover -s tests -p "test_*.py" -v` (`74` passed)
  - `py -m reflex run` reached `App Running` on backend port `8001`; unchanged invalid-icon warnings for `loader_2` / `check_circle` remain.
- Safeguard: if provider-managed default model lists are changed again, update the revision constant at the same time so persisted settings normalize once instead of drifting.

## Session Notes (2026-03-16 - Text Questions Advanced Header Refinement)
- `pages/text_questions_page.py` advanced mode now renders `Quick Presets` and `Assessment Type` in a single responsive header row.
- Preset chips use a non-wrapping horizontal list with overflow fallback so the control group stays visually on one line on desktop.
- Validation:
  - `py -m py_compile app/pages/text_questions_page.py`
  - `py -m reflex run` reached `App Running` on frontend `3001` / backend `8001`; unchanged invalid-icon warnings for `loader_2` / `check_circle` remain.
- Safeguard: future edits to the advanced header should preserve this single-row desktop layout and only stack on smaller screens.

## Session Notes (2026-03-16 - Text Questions Assessment Type Removal)
- Active text questions V2 UI no longer exposes `Assessment Type` as a visible control or sidebar summary.
- `states/text_questions_state.py` still keeps `assessment_type` internally for prompt construction, but the active profile is now derived only from preset selection.
- Removed unused V2-only assessment-type override event and trimmed tests accordingly; preset mapping coverage remains for `Quick Check -> Practice`.
- Validation:
  - `py -m py_compile app/pages/text_questions_page.py app/states/text_questions_state.py tests/test_text_questions_state.py`
  - `py -m unittest discover -s tests -p "test_text_questions_state.py" -v`
  - `py -m unittest discover -s tests -p "test_*.py" -v` (`73` passed)
  - `py -m reflex run` reached `App Running` on frontend `3001` / backend `8001`; unchanged invalid-icon warnings for `loader_2` / `check_circle` remain.
- Safeguard: if assessment-type control comes back later, it should not be a partial override that conflicts with preset-driven counts and cognitive mix.

## Session Notes (2026-03-17 - Separate Student App V1)
- Added shared platform code under `student_platform/` for:
  - SQLAlchemy persistence models
  - shared assessment render/publish services
  - submissions + autosave/final submit
  - evaluation jobs + manual essay scoring
  - analytics/mastery rollups
  - remediation plan generation
  - Google OIDC-ready auth helpers
  - server-side media storage.
- Reflex app integration:
  - new state `states/student_platform_state.py`
  - new page `pages/student_platform_page.py`
  - new route `/student-platform` in `app.py`
  - navigation entry in `components/layout_components.py`
  - Review page shortcut into student publishing.
- Shared-render safeguard:
  - Review parsing now uses the shared render service so teacher review and student publish read the same normalized item structure.
  - Numeric delivery items are classified separately from FIB using `responseDeclaration` base type instead of text-entry shape alone.
- Settings/runtime note:
  - `states/settings_state.py` now persists `student_remediation_model`
  - `student_platform/auth_service.py` keeps `Authlib` optional so the Reflex app still imports before OIDC setup is finished.
- Separate runtime note outside the `app/` subtree:
  - student-facing web app entrypoint is `../student_app/main.py`
  - async worker entrypoint is `../tools/run_student_platform_worker.py`
  - next productionization step is adding managed DB migrations and Fly process wiring for all three runtimes.
- Validation:
  - `py -m py_compile app/student_platform/db.py app/student_platform/models.py app/student_platform/assessment_render_service.py app/student_platform/assessment_publish_service.py app/student_platform/submission_service.py app/student_platform/evaluation_service.py app/states/student_platform_state.py app/pages/student_platform_page.py`
  - `py -m unittest discover -s tests -p "test_*.py" -v` (`75` passed)
  - `py -m uvicorn student_app.main:app --port 8051` reached `Application startup complete`, then shut down cleanly
  - `py -m reflex run` reached `App Running`; existing invalid-icon warnings remained unchanged and unrelated to the student-platform additions.

## Session Notes (2026-03-17 - Student Platform Stabilization Pass)
- Cleared the remaining app-scope Reflex icon warnings by updating compiled page icon names:
  - `pages/text_questions_page.py`
  - `pages/text_questions_page_v0.py`
  - `pages/text_questions_mock.py`
  - `pages/reading_material_page_v2.py`
- Logging/test cleanup:
  - `utils/yaml_converter.py` now treats skipped-question conversion as a warning path instead of an error path
  - `../tests/test_combined_questions.py` and `../tests/test_yaml_converter_warnings.py` now capture expected warning logs so full-suite output stays clean.
- Validation:
  - `py -m py_compile app/pages/text_questions_page.py app/pages/text_questions_page_v0.py app/pages/text_questions_mock.py app/pages/reading_material_page_v2.py app/utils/yaml_converter.py tests/test_combined_questions.py tests/test_yaml_converter_warnings.py`
  - `py -m unittest discover -s tests -p "test_*.py" -v` (`75` passed)
  - `py -m reflex run --frontend-port 3005 --backend-port 8015` reached `App Running`
  - local HTTP smoke check returned `200` for `http://127.0.0.1:3005/student-platform`
- Windows validation safeguard:
  - repeated Reflex runs can leave `8000/8001` appearing busy even after the owning process disappears; when verifying app health, rerun on explicit clean ports before diagnosing a code regression.

## Session Notes (2026-03-17 - Student App Preview + UI Redesign)
- Student preview access is now intentional and test-covered from the shared app/runtime side:
  - `../student_app/main.py` enables a default read-only preview path when no live session exists
  - preview routes use structured sample dashboard/assignment/results payloads so the full student flow can be reviewed before auth rollout.
- UI/design follow-up outside the `app/` subtree:
  - rewrote `../student_app/templates/*.html` and `../student_app/static/student.css`
  - added `../student_app/static/favicon.svg` and `/favicon.ico` redirect handling.
- Validation:
  - `py -m py_compile student_app/main.py tests/test_student_app_preview.py`
  - `py -m unittest discover -s tests -p "test_student_app_preview.py" -v` (`4` passed)
  - `py -m unittest discover -s tests -p "test_*.py" -v` (`79` passed)
  - `py -m uvicorn student_app.main:app --port 8053` reached `Application startup complete`
  - local visual pass confirmed `/dashboard` and `/results/preview-bio-enzymes` render in preview mode without auth.

## Session Notes (2026-03-17 - Student App Cozy Layout Pass)
- Student-app UI follow-up outside the `app/` subtree:
  - `../student_app/static/student.css` now uses tighter widths, padding, radii, typography, and control sizing so the preview feels compact instead of oversized
  - copy in `../student_app/templates/login.html`, `../student_app/templates/dashboard.html`, and `../student_app/templates/results_detail.html` was shortened to match the denser layout.
- Regression safeguard:
  - `../tests/test_student_app_preview.py` now checks the revised dashboard hero text to keep preview-mode assertions aligned with the UI.
- Validation:
  - `py -m py_compile student_app/main.py`
  - `py -m unittest discover -s tests -p "test_student_app_preview.py" -v` (`4` passed)
  - `py -m unittest discover -s tests -p "test_*.py" -v` (`79` passed)
  - `py -m uvicorn student_app.main:app --port 8054` reached `Application startup complete`
  - local browser pass confirmed `/login`, `/dashboard`, `/assignments/preview-bio-energy`, and `/results/preview-bio-enzymes`.

## Session Notes (2026-03-17 - Student Assignment Review-Style Layout)
- Student assignment page follow-up outside the `app/` subtree:
  - `../student_app/templates/assignment.html` now mirrors the teacher review workspace structure with a compact header, question-card stack, and sticky sidebar
  - `../student_app/static/student.css` adds the review-style assignment/sidebar/question classes used by that layout.
- Shared runtime note:
  - `../student_app/main.py` now computes question-type summary rows and humanized assignment/result labels for the assignment template, and sets `hide_preview_banner=True` there so the page matches the teacher review feel more closely.
- Regression safeguard:
  - `../tests/test_student_app_preview.py` now checks the new assignment preview notice text instead of the removed global banner copy.
- Validation:
  - `py -m py_compile student_app/main.py`
  - `py -m unittest discover -s tests -p "test_student_app_preview.py" -v` (`4` passed)
  - `py -m unittest discover -s tests -p "test_*.py" -v` (`79` passed)
  - `py -m uvicorn student_app.main:app --port 8054` reached `Application startup complete`
  - local browser pass confirmed the updated `/assignments/preview-bio-energy` layout against the teacher `/review-download` reference.

## Session Notes (2026-03-30 - Fly Deploy Pycairo Fix)
- The Fly deploy image in `../Dockerfile` needed native Cairo build support because Reading Material PDF export imports `xhtml2pdf`, which pulls `pycairo` through `svglib` and `rlpycairo`.
- Added `build-essential`, `pkg-config`, and `libcairo2-dev` to the deploy image install step before `pip install -r requirements.txt`.
- Validation:
  - `fly deploy` from `../` progressed through the old failure point and completed `RUN pip install --no-cache-dir -r requirements.txt`, plus the later `COPY` and `reflex init` build steps.
  - the command was interrupted during image export, so deployment completion still needs a fresh `fly deploy` run.
- Safeguard: if Fly build errors mention `pycairo` again, check the deploy image package list before changing Python dependencies or removing `xhtml2pdf`.

## Session Notes (2026-03-30 - Teacher Route Sync + Release)
- Refreshed the deploy bundle so Fly now serves the same newer teacher UI/state code as the local app for:
  - `/upload-material`
  - `/text-questions`
  - `/image-questions`
  - `/reading-material`
- Synced from root app into deploy bundle:
  - `pages/upload_material_page.py`
  - `pages/text_questions_page.py`
  - `pages/image_questions_page.py`
  - `pages/reading_material_page.py`
  - `states/material_state.py`
  - `states/image_questions_state.py`
  - `states/reading_material_state.py`
- Deploy-specific safeguard preserved:
  - did not overwrite `app.py`, navigation, or review-state/review-parser files that intentionally remove Student Platform behavior from Fly.
- Validation:
  - `py -m py_compile app/pages/upload_material_page.py app/pages/text_questions_page.py app/pages/image_questions_page.py app/pages/reading_material_page.py app/states/material_state.py app/states/image_questions_state.py app/states/reading_material_state.py`
  - `py -m reflex run --env prod --backend-only --backend-host 127.0.0.1 --backend-port 8013` reached `Backend running`
  - `fly deploy` from `../` released image `teacheraide:deployment-01KMYNMN808VA2NMN7JWVF6KMM`
  - `fly machine status 7841ed5b430598 -a teacheraide` reached `Checks [2/2]`
  - `curl.exe` checks to `https://teacheraide.fly.dev/ping` and `https://teacheraide.fly.dev/` both returned `200`
- Next step: if additional teacher-route changes land in root `app/`, compare those route files against `deploy/app/` before the next Fly release instead of assuming the deploy mirror is current.

## Session Notes (2026-03-30 - Upload Material Replace/Delete Release)
- Synced the root upload-material fix into the deploy bundle for this route only:
  - `pages/upload_material_page.py`
  - `states/material_state.py`
- Deploy behavior now matches root app:
  - uploaded PDF chip includes a delete control
  - replacing an upload performs full cleanup of prior uploaded/extracted PDFs
  - upload state resets to `All Pages` with cleared custom range
  - browser upload selection is cleared after delete/replacement so stale selections do not stick.
- Deploy-only safeguard preserved:
  - no changes to deploy app entry, navigation, or review-state files that intentionally differ from root.
- Validation:
  - `py -m py_compile app/states/material_state.py app/pages/upload_material_page.py`
  - `fly deploy` from `../` released image `teacheraide:deployment-01KMYPYC42PS49W85JT1E5DKFB`
  - `fly machine status 7841ed5b430598 -a teacheraide` reached `Checks [2/2]`
  - `curl.exe --http1.1 -i --max-time 15 https://teacheraide.fly.dev/ping` returned `200`
  - `curl.exe -sS -D - -o NUL --max-time 20 https://teacheraide.fly.dev/` returned `200 OK`
- Next step: if upload-material changes again in root app, re-sync both the page and `MaterialState` together; the route now depends on shared state-side cleanup helpers, not just the sidebar markup.

## Session Notes (2026-03-30 - Upload Route Deploy Follow-up)
- Deploy-side route fix:
  - updated `../nginx.conf` so `/upload-material` no longer matches the backend `/upload` proxy rule on hard refresh.
  - backend-only route regex is now `^/(ping$|upload(?:/|$)|_upload(?:/|$))`.
- Deploy mirror update:
  - re-synced `pages/upload_material_page.py` from root after fixing the dropzone binding to `rx.upload_files(upload_id="pdf-upload")`.
- Release:
  - `fly deploy` from `../` released image `teacheraide:deployment-01KMYQGAEH9MKVJJWQ5B4GH80S`
  - `fly machine status 7841ed5b430598 -a teacheraide` reached `Checks [2/2]`
- Verification:
  - Playwright direct navigation to `https://teacheraide.fly.dev/upload-material` loaded the page successfully
  - live browser smoke check confirmed `file-a.pdf -> delete -> file-b.pdf` on the upload chip
- Safeguard: if a Fly-only route works through in-app navigation but fails on hard refresh, check `deploy/nginx.conf` first for an over-broad backend regex before changing Reflex route generation.

## Session Notes (2026-03-30 - Deploy Upload Size Ceiling)
- Added `client_max_body_size 25m;` to `../nginx.conf` so Fly accepts request bodies up to the same PDF limit enforced by the app.
- Release:
  - `fly deploy` from `../` released image `teacheraide:deployment-01KMYR40NS6X5SYA54A8HJYN1F`
  - `fly machine status 7841ed5b430598 -a teacheraide` reached `Checks [2/2]`
- Verification:
  - live Playwright upload of a synthetic `>2 MB` file (`large-over-1mb.pdf`) on `/upload-material` reached the backend and surfaced a parser error instead of failing at the proxy
- Safeguard: nginx’s default body-size limit is too small for this app’s PDF workflow; preserve the explicit `25m` setting on future deploy config edits.

## Session Notes (2026-03-30 - Deploy Reading Material Error Detail Fix)
- Synced the reading-material error-path fix into the deploy bundle:
  - `states/reading_material_state.py`
- Deploy behavior change:
  - unexpected exceptions during reading-material generation setup now populate the inline page error message instead of falling through to Reflex's generic administrator toast alone.
- Release:
  - `fly deploy` from `../` released image `teacheraide:deployment-01KMZK5NZ02VQWQYHNMXPAEFTQ`
  - `fly machine status 7841ed5b430598 -a teacheraide` reached `Checks [2/2]`
- Safeguard: keep deploy mirror updates for reading-material state in sync with root when changing exception handling; this route's useful diagnostics live in state, not only in page markup.

## Session Notes (2026-03-30 - Deploy Reflex Transport Fix)
- Deploy-side transport hardening for Fly:
  - `../fly.toml`
    - removed the legacy `[[services]]` section that conflicted with `[http_service]`
    - set `auto_stop_machines = 'off'`
    - set `min_machines_running = 1`
  - `../rxconfig.py`
    - added `APP_URL`
    - set both `api_url` and `deploy_url` to the Fly public URL.
- Root cause:
  - Fly was intermittently routing/probing the app as if it lived on port `8080`, while the actual stack is nginx on `80`
  - scale-to-zero behavior also made Reflex `/_event` websocket startup unreliable.
- Release:
  - `fly deploy` from `../` released image `teacheraide:deployment-01KMZP76SA32YK72M27S526J69`
  - `fly machine status 7841ed5b430598 -a teacheraide` reached `Checks [2/2]`
- Live verification:
  - `fly config show -a teacheraide` now shows only `[http_service]` for public routing
  - websocket handshake to `/_event/?token=...&EIO=4&transport=websocket` returned `101 Switching Protocols`
  - fresh Playwright screenshot on `/reading-material` rendered without the visible connection-error banner.
- Safeguard: keep deploy Fly config on a single public service definition and preserve one warm machine for Reflex websocket stability.

## Session Notes (2026-03-30 - Deploy Reading Material Background Event Fix)
- Mirrored the background-event mutation fix into `states/reading_material_state.py` under `deploy/app`.
- Release:
  - `fly deploy` from `../` released image `teacheraide:deployment-01KMZR7P2HDGSEPYWSN8D2FKFR`
  - `fly status -a teacheraide` reported the machine healthy again after rollout.
- Live result:
  - the generic Reflex administrator toast on Reading Material generation is gone
  - Fly now shows a specific inline app error for the same action, which confirms the deploy bundle is no longer failing at background-event startup.
- Safeguard: if a deploy-only Reflex page still shows only the generic administrator toast, audit background-event state mutations before assuming the problem is Fly transport or provider credentials.

## Session Notes (2026-03-30 - Deploy Gemini Stream Await Fix)
- Synced the Gemini illustrated-stream fix into `utils/llm_handlers.py` under `deploy/app`.
- Release:
  - `fly deploy` from `../` released image `teacheraide:deployment-01KMZSTQ6G536Q9XEHKTCD4PB3`
  - `fly status -a teacheraide` reported `2 total, 2 passing`
- Live result:
  - the previous Reading Material Gemini coroutine error (`'async for' requires an object with __aiter__ method, got coroutine`) is gone on Fly
  - the page now reports the normal Gemini invalid-key API error when tested with a fake key.
- Safeguard: for deploy-side Google GenAI streaming helpers, verify whether SDK async methods return an async iterator directly or a coroutine that yields one before using `async for`.

## Session Notes (2026-03-30 - Deploy Illustrated Slide Deck Parity)
- Synced the root illustrated slide-deck changes into the deploy bundle:
  - `utils/model_catalog.py`
  - `utils/llm_handlers.py`
  - `states/settings_state.py`
  - `states/reading_material_state.py`
- Deploy bundle behavior now matches root for Reading Material:
  - slide decks require a Gemini image-preview model with generated-image output support
  - Gemini inline images are merged into ordered slide placeholders before preview/download
  - slide-deck PDFs render as landscape slide pages with a dedicated illustration panel.
- Deploy bundle also includes the Anthropic 4.6 request-shape fix:
  - adaptive thinking effort is now sent in `output_config`, not nested under `thinking`.
- Validation in root before sync:
  - `py -m py_compile ...` across root + deploy reading-material/model files
  - `py -m unittest discover -s tests -p "test_*.py" -v` (`97` passed)
  - `py -m reflex run` reached `App Running`
- Safeguard: keep deploy reading-material state and llm-handler copies aligned with root when changing model capability gates or PDF rendering; this route now depends on both pieces together.

## Session Notes (2026-03-30 - Deploy Slide Deck Two-Pass Gemini Images)
- Synced the slide-deck reliability follow-up into `deploy/app/utils/llm_handlers.py`.
- Deploy bundle now matches root for illustrated slide decks:
  - slide markdown is generated first
  - per-slide illustrations are generated in separate Gemini image calls
  - injected image markdown is then used for preview/PDF.
- Validation before sync:
  - `py -m unittest discover -s tests -p "test_*.py" -v` (`99` passed)
- Safeguard: keep deploy slide-deck behavior on the same two-pass Gemini flow as root; the older single mixed text+image response path is too unreliable for classroom slide output.

## Session Notes (2026-03-30 - Deploy Slide Deck One-Run Gemini Response)
- Synced the final root refactor into `deploy/app/utils/llm_handlers.py`: deploy slide decks now use one Gemini image-preview `generate_content(...)` call with mixed `TEXT` + `IMAGE` output, not the temporary two-pass slide image flow.
- Deploy bundle behavior now matches root:
  - ordered response parts are parsed into ordered slide markdown plus embedded illustrations
  - missing images fall back to `_Illustration unavailable_`
  - extra images attach to the last illustrated slide.
- SDK safeguard: deploy copy uses `thinking_budget` and a raw `image_config` dict because this repo's installed `google-genai` package does not expose `types.ImageConfig` and rejects `thinking_level`.
- Validation source of truth:
  - `py -m py_compile app/utils/llm_handlers.py deploy/app/utils/llm_handlers.py app/states/reading_material_state.py tests/test_llm_handlers.py tests/test_slide_deck_pdf.py`
  - `py -m unittest discover -s tests -p "test_*.py" -v` (`98` passed)
  - `py -m reflex run` reached `App Running`
