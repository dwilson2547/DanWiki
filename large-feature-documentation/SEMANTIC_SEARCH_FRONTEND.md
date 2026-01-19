# Semantic Search Frontend - Quick Guide

## What Was Added

### 1. **Reusable SemanticSearch Component**
Location: `frontend/src/components/SemanticSearch.jsx`

A fully-featured, reusable AI search component with:
- **3 Search Modes**: Semantic (AI), Hybrid (AI + Keyword), and Keyword
- **Configurable Settings**: Adjust similarity threshold and AI/keyword balance
- **Real-time Results**: Displays similarity scores and chunk previews
- **Flexible Integration**: Can be embedded anywhere in your app

### 2. **Dedicated Search Page**
Location: `frontend/src/pages/SemanticSearchPage.jsx`
Route: `/search`

A standalone page for AI-powered search with:
- Full-featured search interface
- Search tips and usage instructions
- Feature highlights

### 3. **API Client Functions**
Location: `frontend/src/services/api.js`

Added to `searchAPI`:
```javascript
semanticSearch(query, wikiId, limit, offset, threshold)
hybridSearch(query, wikiId, limit, semanticWeight)
```

## How to Use

### Access the Search Page

1. **From Dashboard**: Click the "AI Search" button in the header
2. **Direct URL**: Navigate to `/search`

### Using the Search Component

The component supports three modes:

#### 1. **AI Search (Semantic)**
- Understands meaning and context
- Try: "how to configure authentication"
- Best for: Natural language questions

#### 2. **Hybrid Search**
- Combines AI understanding with keyword matching
- Adjustable weight slider (AI vs Keywords)
- Best for: When unsure which mode to use

#### 3. **Keyword Search**
- Traditional full-text search
- Best for: Exact phrase matching

### Embedding the Component

You can use the `SemanticSearch` component anywhere in your app:

```jsx
import SemanticSearch from '../components/SemanticSearch';

// Basic usage
<SemanticSearch />

// With options
<SemanticSearch 
  wikiId={5}                      // Limit to specific wiki
  placeholder="Ask anything..."    // Custom placeholder
  defaultMode="hybrid"            // Start in hybrid mode
  showModeToggle={true}           // Show mode switcher
  onResultClick={(result) => {    // Custom click handler
    console.log('Clicked:', result);
  }}
/>
```

### Component Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `wikiId` | number/null | null | Limit search to specific wiki |
| `placeholder` | string | "Search with AI..." | Input placeholder text |
| `defaultMode` | string | "semantic" | Starting mode: 'semantic', 'hybrid', or 'keyword' |
| `showModeToggle` | boolean | true | Show mode switcher buttons |
| `onResultClick` | function | null | Custom result click handler |
| `className` | string | "" | Additional CSS classes |

## Search Settings

### Semantic Mode Settings
- **Similarity Threshold** (0.3 - 0.9)
  - Higher = stricter matching, fewer results
  - Lower = broader matching, more results
  - Default: 0.5

### Hybrid Mode Settings
- **AI Weight** (0% - 100%)
  - 100% = Pure AI search
  - 0% = Pure keyword search
  - Default: 70% AI / 30% Keyword

## Result Display

Each result shows:
- **Page Title** with icon
- **Similarity Score** (visual bar + percentage)
- **Heading Path** (e.g., "Installation > Setup > Dependencies")
- **Content Preview** (relevant text chunk)
- **Wiki Name**
- **AI Match Badge** (in hybrid mode when AI contributed)

## Tips for Best Results

### Good Queries:
- ✅ "How do I set up authentication?"
- ✅ "Database connection configuration"
- ✅ "Error handling best practices"
- ✅ "Install React dependencies"

### Search Mode Selection:
- **Use Semantic**: When asking questions or describing concepts
- **Use Hybrid**: When unsure or want comprehensive results
- **Use Keyword**: When searching for specific terms or code

## Styling

The component uses CSS classes from `semantic-search.css`:
- `.semantic-search-container` - Main wrapper
- `.search-result-item` - Individual results
- `.result-score` - Similarity score display
- `.search-mode-toggle` - Mode switcher buttons

All styles respect your theme (light/dark mode).

## Navigation

Added "AI Search" button to Dashboard header for easy access.

## Next Steps

1. **Test it**: Create/edit pages to generate embeddings
2. **Search**: Try different modes and queries
3. **Customize**: Adjust settings to find what works best
4. **Integrate**: Embed the component in other pages as needed

---

The component is production-ready and fully functional once:
1. Backend embedding service is running
2. RQ worker is processing embedding tasks
3. Pages have embeddings generated
