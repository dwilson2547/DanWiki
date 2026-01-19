# Features and bugfixes

List of tasks to complete for the project

## Features

### UI

- [x] Update parent page selection dropdown to reflect page depth. it should be easy for users to see which page they are selecting as a parent. the dropdown should also be searchable using something like the select-2 package
- [x] Update wiki edit page so that the parent page selection, summary, and change summary are above the editor, but under the page title.
- [x] Update wiki edit page so that tags are on their own row rather than being part of the title row
- [ ] I'd like to allow the user to change the parent of a document by dragging and dropping it on the new parent in the ui. there should be a confirmation dialog to prevent accidental mishaps as well as a checkbox to skip the confirmation dialog box for the next n minutes. a dropdown should be provided and allow the user to select 1, 5, 30, or 60 minutes to mute the confirmation dialog. there should also be a permanent disable for the confirmation dialog. when a parent page with children is moved, the children should remain under the existing parent page, only the parent page's parent should be modified.

## Bugfixes