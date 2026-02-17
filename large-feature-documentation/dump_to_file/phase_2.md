# Phase 2: Frontend Integration (Week 1-2)

## Overview

**Priority: HIGH - User-facing functionality**

This phase creates the user interface for the export feature, making it accessible and intuitive for users to back up their wikis. The focus is on seamless integration with the existing WikiSettings page and providing clear feedback during the export process.

## Goals

- Add export section to WikiSettings page
- Create format selector (ZIP/TAR.GZ)
- Implement export button with loading states
- Add progress indicator for export operations
- Implement file download handling
- Display success notifications
- Provide detailed error messages
- Ensure responsive design for mobile devices

## Timeline

**Duration:** 2 days (Days 6-7 of implementation)

### Day 6: Settings UI
- Add export section to WikiSettings
- Create format selector
- Add export button
- Implement file download

### Day 7: Progress & Error Handling
- Add progress indicator
- Implement error display
- Add success notifications

## Technical Implementation

### File Structure

```
frontend/
├── src/
│   ├── pages/
│   │   └── WikiSettings.jsx       # Updated with export section
│   ├── components/
│   │   └── ExportProgress.jsx     # Progress indicator component
│   └── services/
│       └── api.js                 # Export API methods
```

### WikiSettings Component Updates

```jsx
// frontend/src/pages/WikiSettings.jsx

function WikiSettings() {
  // Existing state...
  
  // Export state
  const [exportFormat, setExportFormat] = useState('zip');
  const [includeAttachments, setIncludeAttachments] = useState(true);
  const [exportProgress, setExportProgress] = useState(null);
  const [exportError, setExportError] = useState(null);
  
  const handleExport = async () => {
    try {
      setExportProgress({ status: 'preparing', message: 'Preparing export...' });
      setExportError(null);
      
      const response = await wikisAPI.exportWiki(wikiId, {
        format: exportFormat,
        include_attachments: includeAttachments
      });
      
      // Download file
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
      const filename = `${wikiSlug}_backup_${timestamp}.${exportFormat}`;
      downloadFile(response, filename);
      
      setExportProgress({ 
        status: 'completed', 
        message: 'Export completed successfully!' 
      });
      
      // Clear success message after 3 seconds
      setTimeout(() => setExportProgress(null), 3000);
      
    } catch (error) {
      setExportError(error.response?.data?.error || error.message);
      setExportProgress(null);
    }
  };
  
  return (
    <div className="wiki-settings">
      {/* ... existing settings sections ... */}
      
      <section className="export-section">
        <h2>Export & Backup</h2>
        <p className="section-description">
          Download a complete backup of your wiki including all pages and attachments.
        </p>
        
        <div className="export-options">
          <div className="form-group">
            <label htmlFor="export-format">Export Format</label>
            <select 
              id="export-format"
              value={exportFormat} 
              onChange={e => setExportFormat(e.target.value)}
              disabled={exportProgress?.status === 'preparing'}
            >
              <option value="zip">ZIP Archive (.zip)</option>
              <option value="tar.gz">Compressed TAR (.tar.gz)</option>
            </select>
            <p className="help-text">
              Both formats are compatible with the import feature
            </p>
          </div>
          
          <div className="form-group checkbox-group">
            <label>
              <input
                type="checkbox"
                checked={includeAttachments}
                onChange={e => setIncludeAttachments(e.target.checked)}
                disabled={exportProgress?.status === 'preparing'}
              />
              <span>Include Attachments</span>
            </label>
            <p className="help-text">
              Include all images, PDFs, and other files attached to pages
            </p>
          </div>
          
          <button 
            onClick={handleExport}
            disabled={exportProgress?.status === 'preparing'}
            className="btn-primary export-button"
          >
            {exportProgress?.status === 'preparing' ? (
              <>
                <span className="spinner"></span>
                Exporting...
              </>
            ) : (
              <>
                <DownloadIcon />
                Export Wiki
              </>
            )}
          </button>
          
          {exportProgress && exportProgress.status !== 'preparing' && (
            <div className="export-success">
              <CheckIcon />
              <span>{exportProgress.message}</span>
            </div>
          )}
          
          {exportError && (
            <div className="export-error">
              <ErrorIcon />
              <span>{exportError}</span>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
```

### ExportProgress Component

```jsx
// frontend/src/components/ExportProgress.jsx

export function ExportProgress({ progress }) {
  if (!progress) return null;
  
  return (
    <div className={`export-progress ${progress.status}`}>
      {progress.status === 'preparing' && (
        <div className="progress-preparing">
          <div className="spinner-large"></div>
          <p>{progress.message || 'Preparing export...'}</p>
        </div>
      )}
      
      {progress.status === 'completed' && (
        <div className="progress-success">
          <CheckCircleIcon size={48} />
          <p>{progress.message || 'Export completed!'}</p>
        </div>
      )}
      
      {progress.status === 'failed' && (
        <div className="progress-error">
          <ErrorCircleIcon size={48} />
          <p>{progress.message || 'Export failed'}</p>
          {progress.details && (
            <pre className="error-details">{progress.details}</pre>
          )}
        </div>
      )}
    </div>
  );
}
```

### API Service Methods

```javascript
// frontend/src/services/api.js

export const wikisAPI = {
  // ... existing methods ...
  
  /**
   * Export wiki to archive file
   * @param {number} wikiId - Wiki ID to export
   * @param {object} options - Export options
   * @param {string} options.format - 'zip' or 'tar.gz'
   * @param {boolean} options.include_attachments - Include attachments
   * @returns {Promise<Blob>} - Archive file blob
   */
  exportWiki: async (wikiId, options = {}) => {
    const response = await apiClient.post(
      `/wikis/${wikiId}/export`,
      options,
      {
        responseType: 'blob',
        timeout: 300000, // 5 minutes
        headers: {
          'Accept': options.format === 'zip' 
            ? 'application/zip' 
            : 'application/gzip'
        }
      }
    );
    return response.data;
  }
};

/**
 * Download blob as file
 * @param {Blob} blob - File data
 * @param {string} filename - Suggested filename
 */
export function downloadFile(blob, filename) {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}
```

### Styling

```css
/* frontend/src/styles/WikiSettings.css */

.export-section {
  margin-top: 2rem;
  padding: 1.5rem;
  background: var(--background-secondary);
  border-radius: 8px;
}

.export-section h2 {
  margin-bottom: 0.5rem;
  color: var(--text-primary);
}

.section-description {
  color: var(--text-secondary);
  margin-bottom: 1.5rem;
}

.export-options {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: 500;
  color: var(--text-primary);
}

.form-group select {
  padding: 0.5rem;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: var(--background-primary);
  color: var(--text-primary);
  font-size: 1rem;
}

.help-text {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin: 0;
}

.checkbox-group label {
  flex-direction: row;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.checkbox-group input[type="checkbox"] {
  width: 1.25rem;
  height: 1.25rem;
  cursor: pointer;
}

.export-button {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  font-weight: 500;
  align-self: flex-start;
}

.export-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.spinner {
  display: inline-block;
  width: 1rem;
  height: 1rem;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.export-success {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  background: var(--success-bg);
  color: var(--success-text);
  border-radius: 4px;
  animation: slideIn 0.3s ease-out;
}

.export-error {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  background: var(--error-bg);
  color: var(--error-text);
  border-radius: 4px;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Mobile responsive */
@media (max-width: 768px) {
  .export-section {
    padding: 1rem;
  }
  
  .export-button {
    width: 100%;
    justify-content: center;
  }
}
```

## User Experience Flow

1. **Navigate to Settings**: User opens wiki settings page
2. **Locate Export Section**: Clearly labeled "Export & Backup" section
3. **Select Options**: 
   - Choose format (ZIP or TAR.GZ)
   - Toggle attachment inclusion
4. **Initiate Export**: Click "Export Wiki" button
5. **View Progress**: Button shows loading state with spinner
6. **Download File**: Browser downloads file automatically
7. **Confirmation**: Success message appears briefly
8. **Error Handling**: Clear error message if export fails

## Error Messages

### User-Friendly Error Messages

```javascript
const ERROR_MESSAGES = {
  403: 'You don\'t have permission to export this wiki.',
  404: 'Wiki not found.',
  408: 'Export timed out. The wiki may be too large. Please try again or contact support.',
  413: 'Wiki is too large to export (maximum 2GB).',
  429: 'Too many export requests. Please wait a moment and try again.',
  500: 'Server error occurred during export. Please try again later.',
  network: 'Network error. Please check your connection and try again.',
  default: 'An unexpected error occurred. Please try again.'
};

function getErrorMessage(error) {
  if (!error.response) {
    return ERROR_MESSAGES.network;
  }
  return ERROR_MESSAGES[error.response.status] || ERROR_MESSAGES.default;
}
```

## Testing Requirements

### Component Tests

```javascript
// tests/components/WikiSettings.test.jsx

describe('WikiSettings Export Section', () => {
  test('renders export section', () => {
    // Verify section renders
  });
  
  test('format selector changes state', () => {
    // Test format selection
  });
  
  test('attachment checkbox toggles', () => {
    // Test checkbox interaction
  });
  
  test('export button triggers download', async () => {
    // Mock API call, verify download
  });
  
  test('shows loading state during export', async () => {
    // Verify button disabled, spinner shown
  });
  
  test('shows success message after export', async () => {
    // Verify success notification
  });
  
  test('shows error message on failure', async () => {
    // Verify error display
  });
  
  test('disables controls during export', () => {
    // Verify inputs disabled during operation
  });
});
```

### Integration Tests

```javascript
// tests/integration/export.test.jsx

describe('Export Integration', () => {
  test('complete export flow', async () => {
    // Full user journey: settings -> export -> download
  });
  
  test('export with different formats', async () => {
    // Test ZIP and TAR.GZ
  });
  
  test('export with/without attachments', async () => {
    // Test both options
  });
  
  test('handles network errors gracefully', async () => {
    // Simulate network failure
  });
  
  test('handles server errors gracefully', async () => {
    // Simulate 500 error
  });
});
```

### Manual Testing

- [ ] Export section visible on settings page
- [ ] Format selector works (ZIP/TAR.GZ)
- [ ] Attachment checkbox toggles correctly
- [ ] Export button clickable when idle
- [ ] Export button disabled during operation
- [ ] Loading spinner appears during export
- [ ] File downloads automatically in Chrome
- [ ] File downloads automatically in Firefox
- [ ] File downloads automatically in Safari
- [ ] Success message appears after download
- [ ] Success message disappears after 3 seconds
- [ ] Error messages appear on failure
- [ ] Error messages are user-friendly
- [ ] Mobile layout is responsive
- [ ] Touch interactions work on mobile
- [ ] Keyboard navigation works

## Accessibility

- Use semantic HTML (`<section>`, `<label>`, etc.)
- Ensure all form controls have labels
- Add ARIA labels where needed
- Maintain keyboard navigation
- Ensure color contrast meets WCAG AA
- Add focus indicators
- Support screen readers

```jsx
// Accessibility example
<button 
  onClick={handleExport}
  disabled={exportProgress?.status === 'preparing'}
  aria-label="Export wiki to archive file"
  aria-busy={exportProgress?.status === 'preparing'}
>
  Export Wiki
</button>
```

## Success Criteria

- ✓ Export section integrates seamlessly with WikiSettings
- ✓ All form controls work correctly
- ✓ File downloads automatically in all browsers
- ✓ Loading states provide clear feedback
- ✓ Success messages confirm completion
- ✓ Error messages are helpful and actionable
- ✓ Mobile responsive design works perfectly
- ✓ All component tests pass
- ✓ All integration tests pass
- ✓ Accessibility audit passes (WCAG AA)

## Dependencies

- React icons library (for DownloadIcon, CheckIcon, etc.)
- Axios or fetch for API calls
- CSS custom properties for theming

## Next Phase

After Phase 2 completion, proceed to **Phase 3: Profile System** to add extensible export profiles.

---

## Progress Tracking

### Feature 1: WikiSettings UI Structure
- [ ] Add export section to WikiSettings.jsx
- [ ] Create section heading and description
- [ ] Add section styling
- [ ] Ensure proper spacing with other sections
- [ ] Test section rendering
- [ ] Verify responsive layout

### Feature 2: Format Selector
- [ ] Add format state to component
- [ ] Create select dropdown for format
- [ ] Add ZIP option
- [ ] Add TAR.GZ option
- [ ] Add help text explaining formats
- [ ] Style select dropdown
- [ ] Handle format change events
- [ ] Test format selection

### Feature 3: Attachment Toggle
- [ ] Add includeAttachments state
- [ ] Create checkbox input
- [ ] Add checkbox label
- [ ] Add help text for checkbox
- [ ] Style checkbox group
- [ ] Handle checkbox change events
- [ ] Test checkbox toggle

### Feature 4: Export Button
- [ ] Create export button component
- [ ] Add download icon
- [ ] Add button text
- [ ] Style button (primary style)
- [ ] Add hover effects
- [ ] Add disabled state styling
- [ ] Handle button click event
- [ ] Test button interaction

### Feature 5: Loading States
- [ ] Add exportProgress state
- [ ] Create spinner component
- [ ] Show spinner during export
- [ ] Update button text during export
- [ ] Disable button during export
- [ ] Disable form controls during export
- [ ] Test loading state transitions

### Feature 6: API Integration
- [ ] Add exportWiki method to api.js
- [ ] Configure POST request to export endpoint
- [ ] Set responseType to 'blob'
- [ ] Set appropriate timeout (5 minutes)
- [ ] Set Accept header based on format
- [ ] Handle API response
- [ ] Test API call

### Feature 7: File Download Handling
- [ ] Implement downloadFile utility function
- [ ] Create blob URL from response
- [ ] Create temporary download link
- [ ] Trigger download
- [ ] Clean up blob URL
- [ ] Generate filename with timestamp
- [ ] Test download in Chrome
- [ ] Test download in Firefox
- [ ] Test download in Safari
- [ ] Test download in Edge

### Feature 8: Success Feedback
- [ ] Add success message state
- [ ] Create success message component
- [ ] Add success icon
- [ ] Style success message
- [ ] Show success message after download
- [ ] Auto-hide success message after 3 seconds
- [ ] Animate success message appearance
- [ ] Test success feedback

### Feature 9: Error Handling
- [ ] Add exportError state
- [ ] Create error message component
- [ ] Add error icon
- [ ] Style error message
- [ ] Map HTTP status codes to user messages
- [ ] Show error message on failure
- [ ] Allow manual dismissal of errors
- [ ] Test all error scenarios (403, 404, 408, 413, 429, 500)
- [ ] Test network error handling

### Feature 10: ExportProgress Component
- [ ] Create ExportProgress.jsx component
- [ ] Handle 'preparing' status
- [ ] Handle 'completed' status
- [ ] Handle 'failed' status
- [ ] Add appropriate icons for each status
- [ ] Style component for each status
- [ ] Add animations
- [ ] Export component

### Feature 11: Styling & Polish
- [ ] Create WikiSettings.css for export section
- [ ] Style export section container
- [ ] Style form groups
- [ ] Style select dropdown
- [ ] Style checkbox
- [ ] Style button
- [ ] Style success message
- [ ] Style error message
- [ ] Add animations
- [ ] Add hover/focus states
- [ ] Ensure consistent spacing
- [ ] Test dark mode compatibility

### Feature 12: Responsive Design
- [ ] Test on mobile (320px width)
- [ ] Test on tablet (768px width)
- [ ] Test on desktop (1920px width)
- [ ] Adjust button width on mobile
- [ ] Adjust form layout on mobile
- [ ] Test touch interactions
- [ ] Verify text readability on small screens
- [ ] Test landscape orientation

### Feature 13: Accessibility
- [ ] Add semantic HTML elements
- [ ] Ensure all inputs have labels
- [ ] Add ARIA labels where needed
- [ ] Test keyboard navigation
- [ ] Add focus indicators
- [ ] Test with screen reader (NVDA/JAWS)
- [ ] Verify color contrast (WCAG AA)
- [ ] Add aria-busy attribute
- [ ] Test with keyboard only

### Feature 14: Component Testing
- [ ] Write test: renders export section
- [ ] Write test: format selector changes state
- [ ] Write test: attachment checkbox toggles
- [ ] Write test: export button triggers download
- [ ] Write test: shows loading state during export
- [ ] Write test: shows success message after export
- [ ] Write test: shows error message on failure
- [ ] Write test: disables controls during export
- [ ] Run all component tests
- [ ] Verify test coverage (>80%)

### Feature 15: Integration Testing
- [ ] Write test: complete export flow
- [ ] Write test: export with different formats
- [ ] Write test: export with/without attachments
- [ ] Write test: handles network errors
- [ ] Write test: handles server errors
- [ ] Write test: handles timeout
- [ ] Run all integration tests
- [ ] Test with actual backend

### Feature 16: Manual QA
- [ ] Complete manual testing checklist
- [ ] Test in Chrome
- [ ] Test in Firefox
- [ ] Test in Safari
- [ ] Test in Edge
- [ ] Test on iOS Safari
- [ ] Test on Android Chrome
- [ ] Document any browser-specific issues
- [ ] Verify fixes for all issues

### Feature 17: Documentation
- [ ] Document export section in user guide
- [ ] Add screenshots of export UI
- [ ] Document error messages
- [ ] Create troubleshooting guide
- [ ] Update component documentation
- [ ] Add inline code comments
