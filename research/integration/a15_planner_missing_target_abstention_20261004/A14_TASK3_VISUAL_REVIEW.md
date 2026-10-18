# Post-run visual review (not part of the frozen machine gate)

I inspected all five pinned 1280×800 screenshots after the model calls. This is a post-run qualitative check and does not change the predeclared schema/lifecycle decision rule in `PLAN.md`.

| Task | Screenshot | Model field point / submit point / crop | Visible target review |
|---:|---|---|---|
| 2 | `029.png` | `(280,401)` / `(376,401)` / `[120,394,331,408]` | The left-aligned Value field and Save button are visible; the field point/crop and button point appear to land on them. |
| 3 | `054.png` | `(250,401)` / `(376,401)` / `[121,394,331,409]` | The captured page body is blank; no Value field or Save button is visible. The model still returned the task-2-like left-layout coordinates. Grounding fails by direct visual inspection. |
| 4 | `079.png` | `(700,559)` / `(689,634)` / `[499,543,800,575]` | A centered Value field and Save button are visible; the point/crop appear to land on them. |
| 5 | `105.png` | `(700,558)` / `(689,634)` / `[498,544,800,573]` | A centered Value field and Save button are visible; the point/crop appear to land on them. |
| 6 | `134.png` | `(700,560)` / `(689,634)` / `[500,544,800,574]` | A centered Value field and Save button are visible; the point/crop appear to land on them. |

The machine audit's 5/5 result is strictly schema, predicate lifecycle, bounds, and candidate-compiler acceptance. It must not be read as 5/5 valid visual grounding. Task 3 is a concrete counterexample to that broader reading: a syntactically and lifecycle-valid contract can be emitted when the retained screenshot shows no target. No runtime was executed, so this review does not establish whether the live observer's fresh `target_valid` branch would safely yield on that blank frame.
