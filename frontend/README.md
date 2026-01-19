# Wiki App Frontend

A React frontend for the Wiki application using Toast UI Editor.

## Features

- User authentication (login/register)
- Wiki management (create, edit, delete)
- Hierarchical page structure
- Rich markdown editing with Toast UI Editor
- **Clipboard paste support for images** (Ctrl+V)
- Drag-and-drop image uploads
- File attachments
- Page revision history
- Real-time search
- Member management with roles

## Tech Stack

- React 18
- React Router v6
- Toast UI Editor
- Axios for API calls
- Lucide React for icons
- Vite for bundling

## Getting Started

### Prerequisites

Make sure the backend server is running on port 5000.

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

The app will be available at `http://localhost:3000`.

Vite is configured to proxy `/api` requests to `http://localhost:5000`.

### Build for Production

```bash
npm run build
```

Built files will be in the `dist` directory.

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── MarkdownEditor.jsx  # Toast UI Editor with paste support
│   │   ├── Modal.jsx
│   │   ├── PageTree.jsx
│   │   └── Search.jsx
│   ├── context/
│   │   └── AuthContext.jsx     # Authentication state
│   ├── pages/
│   │   ├── Login.jsx
│   │   ├── Register.jsx
│   │   ├── Dashboard.jsx       # Wiki list
│   │   ├── WikiLayout.jsx      # Layout with sidebar
│   │   ├── WikiHome.jsx
│   │   ├── WikiSettings.jsx
│   │   ├── PageView.jsx
│   │   └── PageEdit.jsx
│   ├── services/
│   │   └── api.js              # API client
│   ├── styles/
│   │   └── index.css
│   ├── App.jsx
│   └── main.jsx
├── index.html
├── package.json
└── vite.config.js
```

## Image Upload Support

The editor supports multiple ways to add images:

1. **Toolbar button**: Click the image icon in the toolbar
2. **Drag and drop**: Drag an image file onto the editor
3. **Clipboard paste**: Copy an image and paste with Ctrl+V (or Cmd+V on Mac)

All images are automatically uploaded to the server and embedded as markdown.

## Keyboard Shortcuts

The Toast UI Editor supports standard markdown shortcuts:

- `Ctrl+B` - Bold
- `Ctrl+I` - Italic
- `Ctrl+K` - Link
- `Ctrl+V` - Paste (including images!)
- `Tab` - Indent list
- `Shift+Tab` - Outdent list

## API Integration

The frontend communicates with the Flask backend through:

- JWT authentication with automatic token refresh
- RESTful API endpoints
- File upload via FormData

See `src/services/api.js` for the complete API client implementation.
