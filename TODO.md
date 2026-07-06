# TODO

Backlog imported from the retired todo store, 2026-07-06.

## Low

- [ ] **Create a Helm chart for danwiki and deploy it** — Build out a Helm chart for danwiki and deploy it to the cluster just to get the project running again as a fun side deployment.

## Unprioritized (imported from workman drafts, 2026-07-06)

- [ ] **Drag-and-drop page re-parenting** — Allow users to drag a page onto a new parent in the sidebar tree. Confirmation dialog with mute option (1/5/30/60 min or permanent). Moving a page only changes that page's parent — children stay where they are.
- [ ] **Attachment relative path storage** — Store and serve attachments using a relative path from the uploads directory. Add a new DB column for the relative path; preserve the original absolute path. Makes attachments portable if the uploads directory moves.
- [ ] **Color customization and theming panel** — User settings page: custom color panel for UI theming and syntax highlighting. Support built-in themes and a custom CSS box.
- [ ] **Dark mode scrollbar polish** — Restyle scrollbars to match dark theme instead of using the browser default light-mode scrollbars.
- [ ] **@user and #page inline autocomplete** — While editing, typing @ autocompletes to wiki members; typing # autocompletes to existing pages within the wiki. Inserts correct links.
- [ ] **JSON canvas support** — Add support for rendering and editing JSON canvas files (Obsidian canvas format) as a page type or attachment view.
- [ ] **GitHub repo load and backup** — Import wiki content from a GitHub repo; export/backup wiki to a GitHub repo. Support optional sidebar generation and handle GitHub attachment/link standards.
- [ ] **Dump wiki to tar/zip archive** — Export a wiki as a tar or zip archive. File structure must be compatible with the existing bulk import format.
- [ ] **S3 bucket backup** — Optional backup of wiki content and uploads to an S3-compatible bucket (TrueNAS AIStor or external S3).
