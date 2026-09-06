# Style questions — Heart on a Sleeve

Visual calls found during the 2026-09-06 UX pass that need a human to look at rendered
options rather than be guessed at. Fixable inconsistencies live in ISSUES.md instead.

- Merch tiles (`.merch-btn`) use a `1.5px` border while every other button (`.btn`, `.btn-primary`, `.btn-secondary`, `.btn-danger`, `.design-card`) uses `1px`; `1.5px` is otherwise the input/select convention (`#place-search`, `.save-input`, `.brand-select`, login's `.field input`). Should the merch tiles drop to `1px` like the other buttons, keep `1.5px` as a deliberate "selectable tile" weight, or should all selectable tiles and inputs move to `2px`?
- The collapsed mobile bottom sheet peeks by a different amount per view: `#panel` shows `100px`, `#svg-side` and `#panel3d` show `80px`. Should they all match, and at which height?
- Text inputs use four different paddings across the app: `.brand-select` `6px 7px`, `.save-input` `7px 9px`, `#place-search` `8px 10px`, login's `.field input` `9px 11px`. Should these collapse to one input padding, or is the size meant to track the control's importance?
