# Features and bugfixes

List of tasks to complete for the project

## Features

### UI

- [x] Update parent page selection dropdown to reflect page depth. it should be easy for users to see which page they are selecting as a parent. the dropdown should also be searchable using something like the select-2 package
- [x] Update wiki edit page so that the parent page selection, summary, and change summary are above the editor, but under the page title.
- [x] Update wiki edit page so that tags are on their own row rather than being part of the title row
- [x] add verification process where newly registered users enter a pending state until the server administrator approves their account. there shuld also be a page in the admin panel to manage requests to join
- [ ] I'd like to allow the user to change the parent of a document by dragging and dropping it on the new parent in the ui. there should be a confirmation dialog to prevent accidental mishaps as well as a checkbox to skip the confirmation dialog box for the next n minutes. a dropdown should be provided and allow the user to select 1, 5, 30, or 60 minutes to mute the confirmation dialog. there should also be a permanent disable for the confirmation dialog. when a parent page with children is moved, the children should remain under the existing parent page, only the parent page's parent should be modified.
- [ ] Update attachments to store and use relative file path from the uploads directory so if the uploads directory moves, they're still accessible. the original file path should still be persisted, an additional field should be added to handle the relative path file name
- [ ] add load from github repo and backup to github repo. include option for sidebar generation and should account for github's attachment and link standards.
- [ ] add dump wiki to tar or zip option, should maintain file structure that is expected for import
- [ ] add color customization panel in user settings that allows users to customize their own ui, including themes and syntax highlighting. Include a box for custom css
- [ ] allow for s3 bucket backup optionally
- [ ] refine dark mode scroll bars to be dark theme
- [ ] add a user and page tagging feature where after typing @, the text is autocompleted to users with access tot he wiki and after typing #, existing pages within the wiki are auto completed for easy link creation
- [ ] add suppport for json canvas

## Bugfixes