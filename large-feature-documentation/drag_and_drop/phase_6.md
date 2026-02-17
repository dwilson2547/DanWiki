# Phase 6: Styling (Day 3)

## Overview

**Priority: MEDIUM - Polish and consistency**

This phase focuses on refining the visual design of all drag-and-drop components to ensure a consistent, professional appearance that matches the rest of the wiki application. Includes styling for drag states, drop zones, modal, and responsive design.

## Goals

- Create cohesive visual design language
- Ensure consistency with existing wiki theme
- Add smooth animations and transitions
- Implement responsive design for mobile
- Support dark mode
- Add accessibility indicators
- Polish micro-interactions
- Ensure cross-browser compatibility

## Timeline

**Duration:** 0.5 days (Day 3 late afternoon)

### Day 3 Late Afternoon: Styling Polish
- Refine all component styles
- Test responsive layouts
- Verify dark mode
- Cross-browser testing

## Technical Implementation

### Design Tokens

```css
/* frontend/src/styles/dragAndDrop.css */

:root {
  /* Colors */
  --dnd-primary: #3b82f6;
  --dnd-primary-hover: #2563eb;
  --dnd-primary-light: rgba(59, 130, 246, 0.1);
  --dnd-primary-lighter: rgba(59, 130, 246, 0.05);
  
  --dnd-success: #10b981;
  --dnd-warning: #f59e0b;
  --dnd-error: #ef4444;
  
  --dnd-border: #e5e7eb;
  --dnd-border-light: #f3f4f6;
  --dnd-border-hover: #d1d5db;
  
  --dnd-text-primary: #111827;
  --dnd-text-secondary: #6b7280;
  --dnd-text-muted: #9ca3af;
  
  --dnd-bg-card: #ffffff;
  --dnd-bg-hover: rgba(0, 0, 0, 0.04);
  --dnd-bg-active: rgba(0, 0, 0, 0.08);
  
  --dnd-shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --dnd-shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07);
  --dnd-shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
  --dnd-shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.15);
  
  /* Spacing */
  --dnd-spacing-xs: 4px;
  --dnd-spacing-sm: 8px;
  --dnd-spacing-md: 12px;
  --dnd-spacing-lg: 16px;
  --dnd-spacing-xl: 24px;
  
  /* Border radius */
  --dnd-radius-sm: 4px;
  --dnd-radius-md: 6px;
  --dnd-radius-lg: 8px;
  --dnd-radius-xl: 12px;
  
  /* Transitions */
  --dnd-transition-fast: 150ms ease;
  --dnd-transition-base: 200ms ease;
  --dnd-transition-slow: 300ms ease;
  
  /* Z-index */
  --dnd-z-drag: 1000;
  --dnd-z-modal: 2000;
  --dnd-z-modal-backdrop: 1999;
}

/* Dark mode tokens */
@media (prefers-color-scheme: dark) {
  :root {
    --dnd-primary: #60a5fa;
    --dnd-primary-hover: #3b82f6;
    --dnd-primary-light: rgba(96, 165, 250, 0.15);
    --dnd-primary-lighter: rgba(96, 165, 250, 0.08);
    
    --dnd-border: #374151;
    --dnd-border-light: #1f2937;
    --dnd-border-hover: #4b5563;
    
    --dnd-text-primary: #f9fafb;
    --dnd-text-secondary: #d1d5db;
    --dnd-text-muted: #9ca3af;
    
    --dnd-bg-card: #1f2937;
    --dnd-bg-hover: rgba(255, 255, 255, 0.05);
    --dnd-bg-active: rgba(255, 255, 255, 0.1);
    
    --dnd-shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
    --dnd-shadow-md: 0 4px 6px rgba(0, 0, 0, 0.4);
    --dnd-shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.5);
    --dnd-shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.6);
  }
}
```

### Page Tree Refined Styles

```css
/* frontend/src/components/PageTree.css */

@import '../styles/dragAndDrop.css';

/* Page Tree Container */
.page-tree {
  list-style: none;
  padding: 0;
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* Page Tree Item */
.page-tree-item {
  position: relative;
  padding: var(--dnd-spacing-sm) var(--dnd-spacing-md);
  margin: var(--dnd-spacing-xs) 0;
  border-radius: var(--dnd-radius-md);
  transition: all var(--dnd-transition-base);
  cursor: grab;
  user-select: none;
  background: transparent;
}

.page-tree-item:hover:not(.dragging) {
  background: var(--dnd-bg-hover);
}

.page-tree-item:active {
  cursor: grabbing;
}

/* Dragging state */
.page-tree-item.dragging {
  opacity: 0.5;
  transform: scale(0.98);
  background: var(--dnd-bg-active);
  box-shadow: var(--dnd-shadow-md);
}

/* Drag over state */
.page-tree-item.drag-over {
  background: var(--dnd-primary-lighter);
  border-left: 3px solid var(--dnd-primary);
  padding-left: calc(var(--dnd-spacing-md) + 3px - 3px); /* Compensate for border */
  box-shadow: var(--dnd-shadow-sm);
}

.page-tree-item.drag-over::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: var(--dnd-radius-md);
  border: 2px dashed var(--dnd-primary);
  opacity: 0.4;
  pointer-events: none;
}

/* Page item content */
.page-item-content {
  display: flex;
  align-items: center;
  gap: var(--dnd-spacing-sm);
  padding: var(--dnd-spacing-xs);
  position: relative;
  z-index: 1;
}

.page-icon {
  font-size: 16px;
  flex-shrink: 0;
  width: 20px;
  text-align: center;
  transition: transform var(--dnd-transition-fast);
}

.page-tree-item:hover .page-icon {
  transform: scale(1.1);
}

.page-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--dnd-text-primary);
  font-size: 14px;
  font-weight: 500;
  transition: color var(--dnd-transition-fast);
}

/* Nested children */
.page-tree-children {
  list-style: none;
  padding-left: 20px;
  margin: var(--dnd-spacing-xs) 0 0 0;
  position: relative;
}

.page-tree-children::before {
  content: '';
  position: absolute;
  left: 8px;
  top: 0;
  bottom: 0;
  width: 1px;
  background: var(--dnd-border-light);
}

/* Loading state */
.page-tree-item[draggable="false"] {
  cursor: not-allowed;
  opacity: 0.6;
  pointer-events: none;
}

/* Focus state (accessibility) */
.page-tree-item:focus-visible {
  outline: 2px solid var(--dnd-primary);
  outline-offset: 2px;
  border-radius: var(--dnd-radius-md);
}

/* Root Drop Zone */
.drop-zone {
  min-height: 60px;
  border: 2px dashed var(--dnd-border);
  border-radius: var(--dnd-radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--dnd-text-secondary);
  margin: var(--dnd-spacing-md) 0;
  padding: var(--dnd-spacing-lg);
  transition: all var(--dnd-transition-base);
  font-size: 14px;
  font-weight: 500;
  background: var(--dnd-bg-card);
}

.drop-zone.drag-over {
  border-color: var(--dnd-primary);
  border-width: 3px;
  background: var(--dnd-primary-lighter);
  color: var(--dnd-primary);
  transform: scale(1.02);
  box-shadow: var(--dnd-shadow-md);
}

.drop-zone::before {
  content: '📁';
  font-size: 24px;
  margin-right: var(--dnd-spacing-sm);
  transition: transform var(--dnd-transition-base);
}

.drop-zone.drag-over::before {
  transform: scale(1.2) rotate(5deg);
}

/* Custom drag image */
.drag-image {
  position: absolute;
  top: -9999px;
  left: -9999px;
  padding: var(--dnd-spacing-sm) var(--dnd-spacing-md);
  background: var(--dnd-primary);
  color: white;
  border-radius: var(--dnd-radius-md);
  font-size: 14px;
  font-weight: 500;
  max-width: 250px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  box-shadow: var(--dnd-shadow-xl);
  pointer-events: none;
  z-index: var(--dnd-z-drag);
}

/* Responsive - Mobile */
@media (max-width: 768px) {
  .page-tree-item {
    padding: var(--dnd-spacing-md);
    touch-action: none;
  }
  
  .page-item-content {
    gap: var(--dnd-spacing-md);
  }
  
  .page-icon {
    font-size: 18px;
    width: 24px;
  }
  
  .page-title {
    font-size: 15px;
  }
  
  .drop-zone {
    min-height: 80px;
    font-size: 15px;
  }
}

/* Tablet adjustments */
@media (min-width: 769px) and (max-width: 1024px) {
  .page-tree-item {
    padding: var(--dnd-spacing-md);
  }
}

/* High contrast mode */
@media (prefers-contrast: high) {
  .page-tree-item.drag-over {
    border-left-width: 5px;
    background: var(--dnd-primary-light);
  }
  
  .drop-zone {
    border-width: 3px;
  }
  
  .drop-zone.drag-over {
    border-width: 4px;
  }
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .page-tree-item,
  .page-icon,
  .page-title,
  .drop-zone {
    transition: none;
  }
}

/* Print styles */
@media print {
  .page-tree-item {
    cursor: default;
  }
  
  .drop-zone {
    display: none;
  }
}
```

### Confirmation Modal Refined Styles

```css
/* frontend/src/components/MoveConfirmationModal.css */

@import '../styles/dragAndDrop.css';

/* Modal backdrop */
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  z-index: var(--dnd-z-modal-backdrop);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--dnd-spacing-xl);
  animation: fadeIn var(--dnd-transition-base);
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

/* Modal container */
.confirmation-modal {
  background: var(--dnd-bg-card);
  border-radius: var(--dnd-radius-xl);
  box-shadow: var(--dnd-shadow-xl);
  max-width: 500px;
  width: 100%;
  padding: 0;
  position: relative;
  z-index: var(--dnd-z-modal);
  animation: slideUp var(--dnd-transition-slow);
  overflow: hidden;
}

@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

/* Modal header */
.modal-header {
  padding: var(--dnd-spacing-xl);
  border-bottom: 1px solid var(--dnd-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--dnd-text-primary);
  margin: 0;
  display: flex;
  align-items: center;
  gap: var(--dnd-spacing-sm);
}

.modal-title-icon {
  font-size: 24px;
}

.modal-close {
  background: transparent;
  border: none;
  font-size: 24px;
  color: var(--dnd-text-muted);
  cursor: pointer;
  padding: var(--dnd-spacing-xs);
  border-radius: var(--dnd-radius-sm);
  transition: all var(--dnd-transition-fast);
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-close:hover {
  background: var(--dnd-bg-hover);
  color: var(--dnd-text-primary);
}

.modal-close:active {
  transform: scale(0.95);
}

/* Modal body */
.modal-body {
  padding: var(--dnd-spacing-xl);
}

.modal-message {
  font-size: 15px;
  line-height: 1.6;
  color: var(--dnd-text-secondary);
  margin: 0 0 var(--dnd-spacing-lg) 0;
}

.modal-highlight {
  font-weight: 600;
  color: var(--dnd-primary);
}

.modal-warning {
  display: flex;
  align-items: flex-start;
  gap: var(--dnd-spacing-sm);
  padding: var(--dnd-spacing-md);
  background: rgba(251, 191, 36, 0.1);
  border: 1px solid rgba(251, 191, 36, 0.3);
  border-radius: var(--dnd-radius-md);
  margin-top: var(--dnd-spacing-lg);
}

.modal-warning-icon {
  font-size: 18px;
  flex-shrink: 0;
}

.modal-warning-text {
  font-size: 13px;
  color: var(--dnd-text-secondary);
  line-height: 1.5;
}

/* Mute section */
.mute-section {
  margin-top: var(--dnd-spacing-xl);
  padding-top: var(--dnd-spacing-lg);
  border-top: 1px solid var(--dnd-border);
}

.mute-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--dnd-text-primary);
  margin-bottom: var(--dnd-spacing-sm);
}

.mute-dropdown {
  width: 100%;
  padding: var(--dnd-spacing-sm) var(--dnd-spacing-md);
  border: 1px solid var(--dnd-border);
  border-radius: var(--dnd-radius-md);
  background: var(--dnd-bg-card);
  color: var(--dnd-text-primary);
  font-size: 14px;
  cursor: pointer;
  transition: all var(--dnd-transition-fast);
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%236b7280' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right var(--dnd-spacing-md) center;
  padding-right: calc(var(--dnd-spacing-md) * 3);
}

.mute-dropdown:hover {
  border-color: var(--dnd-border-hover);
}

.mute-dropdown:focus {
  outline: none;
  border-color: var(--dnd-primary);
  box-shadow: 0 0 0 3px var(--dnd-primary-lighter);
}

/* Modal footer */
.modal-footer {
  padding: var(--dnd-spacing-lg) var(--dnd-spacing-xl);
  border-top: 1px solid var(--dnd-border);
  display: flex;
  gap: var(--dnd-spacing-md);
  justify-content: flex-end;
  background: var(--dnd-bg-hover);
}

/* Buttons */
.modal-button {
  padding: var(--dnd-spacing-sm) var(--dnd-spacing-xl);
  border: none;
  border-radius: var(--dnd-radius-md);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--dnd-transition-fast);
  display: inline-flex;
  align-items: center;
  gap: var(--dnd-spacing-xs);
}

.modal-button:focus-visible {
  outline: 2px solid var(--dnd-primary);
  outline-offset: 2px;
}

.modal-button:active {
  transform: scale(0.98);
}

.modal-button-cancel {
  background: transparent;
  color: var(--dnd-text-secondary);
  border: 1px solid var(--dnd-border);
}

.modal-button-cancel:hover {
  background: var(--dnd-bg-hover);
  border-color: var(--dnd-border-hover);
  color: var(--dnd-text-primary);
}

.modal-button-confirm {
  background: var(--dnd-primary);
  color: white;
  box-shadow: var(--dnd-shadow-sm);
}

.modal-button-confirm:hover {
  background: var(--dnd-primary-hover);
  box-shadow: var(--dnd-shadow-md);
}

.modal-button-confirm:disabled,
.modal-button-cancel:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Responsive - Mobile */
@media (max-width: 768px) {
  .modal-backdrop {
    padding: var(--dnd-spacing-md);
  }
  
  .confirmation-modal {
    max-width: 100%;
  }
  
  .modal-header,
  .modal-body,
  .modal-footer {
    padding: var(--dnd-spacing-lg);
  }
  
  .modal-title {
    font-size: 18px;
  }
  
  .modal-footer {
    flex-direction: column-reverse;
  }
  
  .modal-button {
    width: 100%;
    justify-content: center;
  }
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .modal-backdrop,
  .confirmation-modal {
    animation: none;
  }
  
  .modal-button,
  .modal-close,
  .mute-dropdown {
    transition: none;
  }
}

/* Dark mode specific adjustments */
@media (prefers-color-scheme: dark) {
  .modal-backdrop {
    background: rgba(0, 0, 0, 0.7);
  }
  
  .modal-warning {
    background: rgba(251, 191, 36, 0.15);
    border-color: rgba(251, 191, 36, 0.4);
  }
  
  .mute-dropdown {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23d1d5db' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
  }
}
```

### Loading Spinner Component

```css
/* frontend/src/components/LoadingSpinner.css */

.loading-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.modal-button-confirm .loading-spinner {
  margin-left: var(--dnd-spacing-xs);
}
```

## Browser Compatibility

### Tested Browsers
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile Safari iOS 14+
- Chrome Android 90+

### Fallbacks

```css
/* CSS Grid fallback for older browsers */
@supports not (display: grid) {
  .modal-footer {
    display: flex;
  }
}

/* Backdrop filter fallback */
@supports not (backdrop-filter: blur(4px)) {
  .modal-backdrop {
    background: rgba(0, 0, 0, 0.7);
  }
}

/* Custom properties fallback */
@supports not (--css: variables) {
  .page-tree-item {
    padding: 8px 12px;
    border-radius: 6px;
  }
}
```

## Testing Requirements

### Visual Regression Tests

```javascript
// tests/visual/dragAndDrop.visual.test.js

describe('Drag and Drop Visual Tests', () => {
  test('page tree renders correctly', async () => {
    await page.goto('/wiki/1');
    await page.waitForSelector('.page-tree');
    const screenshot = await page.screenshot();
    expect(screenshot).toMatchImageSnapshot();
  });
  
  test('drag over state', async () => {
    // Simulate drag
    await page.hover('.page-tree-item:first-child');
    await page.mouse.down();
    await page.hover('.page-tree-item:nth-child(2)');
    const screenshot = await page.screenshot();
    expect(screenshot).toMatchImageSnapshot();
  });
  
  test('confirmation modal', async () => {
    // Open modal
    await openConfirmationModal();
    const screenshot = await page.screenshot();
    expect(screenshot).toMatchImageSnapshot();
  });
});
```

### Responsive Tests

```javascript
// tests/responsive/dragAndDrop.responsive.test.js

describe('Responsive Design Tests', () => {
  const viewports = [
    { name: 'mobile', width: 375, height: 667 },
    { name: 'tablet', width: 768, height: 1024 },
    { name: 'desktop', width: 1920, height: 1080 }
  ];
  
  viewports.forEach(viewport => {
    test(`renders correctly on ${viewport.name}`, async () => {
      await page.setViewport(viewport);
      await page.goto('/wiki/1');
      // Verify layout
    });
  });
});
```

### Dark Mode Tests

```javascript
// tests/darkMode/dragAndDrop.dark.test.js

describe('Dark Mode Tests', () => {
  beforeEach(async () => {
    await page.emulateMediaFeatures([
      { name: 'prefers-color-scheme', value: 'dark' }
    ]);
  });
  
  test('page tree in dark mode', async () => {
    await page.goto('/wiki/1');
    const backgroundColor = await page.$eval('.page-tree-item', 
      el => getComputedStyle(el).backgroundColor
    );
    expect(backgroundColor).toMatch(/rgba\(31, 41, 55/);
  });
});
```

### Accessibility Tests

```javascript
// tests/a11y/dragAndDrop.a11y.test.js

describe('Accessibility Tests', () => {
  test('passes axe accessibility checks', async () => {
    await page.goto('/wiki/1');
    const results = await new AxePuppeteer(page).analyze();
    expect(results.violations).toHaveLength(0);
  });
  
  test('focus indicators visible', async () => {
    await page.goto('/wiki/1');
    await page.keyboard.press('Tab');
    const outline = await page.$eval('.page-tree-item:focus', 
      el => getComputedStyle(el).outline
    );
    expect(outline).not.toBe('none');
  });
});
```

## Success Criteria

- ✓ Consistent design language across all components
- ✓ Smooth animations without jank
- ✓ Responsive on all screen sizes
- ✓ Dark mode fully supported
- ✓ Accessibility standards met (WCAG 2.1 AA)
- ✓ Cross-browser compatibility verified
- ✓ Performance optimized (60fps animations)
- ✓ Visual regression tests pass
- ✓ High contrast mode supported

## Next Phase

After Phase 6 completion, proceed to **Phase 7: Testing & Polish** for comprehensive testing and final refinements.

---

## Progress Tracking

### Feature 1: Design Tokens
- [ ] Create frontend/src/styles/dragAndDrop.css
- [ ] Define color variables
- [ ] Define spacing variables
- [ ] Define border-radius variables
- [ ] Define shadow variables
- [ ] Define transition variables
- [ ] Define z-index variables
- [ ] Add dark mode overrides

### Feature 2: PageTree Styles - Base
- [ ] Update PageTree.css
- [ ] Import design tokens
- [ ] Style .page-tree container
- [ ] Style .page-tree-item base
- [ ] Add hover state
- [ ] Add active state (grabbing cursor)
- [ ] Add user-select: none

### Feature 3: PageTree Styles - Drag States
- [ ] Style .dragging class
- [ ] Add opacity and scale transform
- [ ] Style .drag-over class
- [ ] Add left border highlight
- [ ] Add dashed border overlay (::before)
- [ ] Add background color
- [ ] Test all drag states

### Feature 4: PageTree Styles - Content
- [ ] Style .page-item-content
- [ ] Use flexbox layout
- [ ] Style .page-icon
- [ ] Add icon hover animation
- [ ] Style .page-title
- [ ] Add text truncation
- [ ] Add color transitions

### Feature 5: PageTree Styles - Nesting
- [ ] Style .page-tree-children
- [ ] Add left padding for indentation
- [ ] Add ::before pseudo-element
- [ ] Create vertical line connector
- [ ] Test with deeply nested pages

### Feature 6: PageTree Styles - Drop Zone
- [ ] Style .drop-zone
- [ ] Add dashed border
- [ ] Center content with flexbox
- [ ] Add ::before icon
- [ ] Style .drag-over state
- [ ] Add scale transform
- [ ] Add icon animation
- [ ] Test drop zone appearance

### Feature 7: PageTree Styles - States
- [ ] Style loading state [draggable="false"]
- [ ] Add disabled opacity
- [ ] Style :focus-visible
- [ ] Add outline for accessibility
- [ ] Style .drag-image
- [ ] Position off-screen
- [ ] Add shadow

### Feature 8: Modal Styles - Backdrop
- [ ] Update MoveConfirmationModal.css
- [ ] Import design tokens
- [ ] Style .modal-backdrop
- [ ] Add blur backdrop-filter
- [ ] Position fixed fullscreen
- [ ] Center modal with flexbox
- [ ] Add fadeIn animation

### Feature 9: Modal Styles - Container
- [ ] Style .confirmation-modal
- [ ] Set max-width and padding
- [ ] Add border-radius
- [ ] Add box-shadow
- [ ] Add slideUp animation
- [ ] Set z-index

### Feature 10: Modal Styles - Header
- [ ] Style .modal-header
- [ ] Add border-bottom
- [ ] Style .modal-title
- [ ] Add icon styling
- [ ] Style .modal-close button
- [ ] Add hover effect
- [ ] Add active transform

### Feature 11: Modal Styles - Body
- [ ] Style .modal-body
- [ ] Style .modal-message
- [ ] Style .modal-highlight
- [ ] Style .modal-warning container
- [ ] Add warning background and border
- [ ] Style warning icon and text

### Feature 12: Modal Styles - Mute Section
- [ ] Style .mute-section
- [ ] Add top border
- [ ] Style .mute-label
- [ ] Style .mute-dropdown
- [ ] Add custom dropdown arrow
- [ ] Add hover state
- [ ] Add focus state with ring

### Feature 13: Modal Styles - Footer
- [ ] Style .modal-footer
- [ ] Add top border
- [ ] Use flexbox for button layout
- [ ] Style .modal-button base
- [ ] Style .modal-button-cancel
- [ ] Style .modal-button-confirm
- [ ] Add hover and active states
- [ ] Add disabled state

### Feature 14: Loading Spinner
- [ ] Create LoadingSpinner.css
- [ ] Style .loading-spinner
- [ ] Create spin animation
- [ ] Add to confirm button
- [ ] Test spinner visibility

### Feature 15: Responsive - Mobile
- [ ] Add mobile media query (<768px)
- [ ] Adjust PageTree padding
- [ ] Increase touch targets
- [ ] Adjust font sizes
- [ ] Make modal full-width
- [ ] Stack footer buttons vertically
- [ ] Test on actual devices

### Feature 16: Responsive - Tablet
- [ ] Add tablet media query (769px-1024px)
- [ ] Adjust spacing
- [ ] Test layout
- [ ] Verify readability

### Feature 17: Dark Mode - PageTree
- [ ] Add dark mode media query
- [ ] Update color variables
- [ ] Test page tree in dark mode
- [ ] Verify contrast ratios
- [ ] Test drag states visibility

### Feature 18: Dark Mode - Modal
- [ ] Update modal colors for dark mode
- [ ] Adjust backdrop opacity
- [ ] Update warning colors
- [ ] Update dropdown arrow color
- [ ] Test modal in dark mode

### Feature 19: Accessibility - High Contrast
- [ ] Add high contrast media query
- [ ] Increase border widths
- [ ] Enhance color contrast
- [ ] Test with high contrast mode

### Feature 20: Accessibility - Reduced Motion
- [ ] Add reduced motion media query
- [ ] Remove animations
- [ ] Keep instant transitions
- [ ] Test with reduced motion enabled

### Feature 21: Browser Compatibility - Fallbacks
- [ ] Add @supports checks
- [ ] Add grid fallback
- [ ] Add backdrop-filter fallback
- [ ] Add CSS variables fallback
- [ ] Test in older browsers

### Feature 22: Print Styles
- [ ] Add print media query
- [ ] Hide drop zone
- [ ] Remove drag cursor
- [ ] Test print preview

### Feature 23: Visual Regression Tests
- [ ] Set up visual testing tool
- [ ] Create baseline screenshots
- [ ] Write test: page tree
- [ ] Write test: drag states
- [ ] Write test: modal
- [ ] Run visual tests
- [ ] Review differences

### Feature 24: Responsive Tests
- [ ] Define viewport sizes
- [ ] Write mobile tests
- [ ] Write tablet tests
- [ ] Write desktop tests
- [ ] Test orientation changes
- [ ] Verify layouts

### Feature 25: Dark Mode Tests
- [ ] Set up dark mode emulation
- [ ] Write color tests
- [ ] Write contrast tests
- [ ] Verify all components
- [ ] Compare with light mode

### Feature 26: Accessibility Tests
- [ ] Set up axe-core
- [ ] Run automated a11y tests
- [ ] Test keyboard navigation
- [ ] Test focus indicators
- [ ] Test screen reader
- [ ] Fix any violations

### Feature 27: Performance Tests
- [ ] Measure animation FPS
- [ ] Profile paint operations
- [ ] Check for layout thrashing
- [ ] Optimize if needed
- [ ] Verify 60fps on low-end devices

### Feature 28: Cross-Browser Testing
- [ ] Test in Chrome
- [ ] Test in Firefox
- [ ] Test in Safari
- [ ] Test in Edge
- [ ] Test in Mobile Safari
- [ ] Test in Chrome Android
- [ ] Document any issues

### Feature 29: Polish - Animations
- [ ] Review all animations
- [ ] Ensure smooth transitions
- [ ] Check for jank
- [ ] Add easing functions
- [ ] Test on different hardware

### Feature 30: Documentation
- [ ] Document CSS variables
- [ ] Create style guide
- [ ] Document responsive breakpoints
- [ ] Document dark mode approach
- [ ] Add usage examples
- [ ] Document browser support
