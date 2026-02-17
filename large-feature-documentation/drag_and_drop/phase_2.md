# Phase 2: Frontend API Integration (Day 1)

## Overview

**Priority: HIGH - Connect frontend to backend**

This phase establishes the frontend connection to the newly created backend API endpoints. It includes adding API service methods, setting up error handling, and preparing the foundation for the drag-and-drop UI implementation.

## Goals

- Add API method for changing page parent
- Verify auth API handles settings updates
- Implement proper error handling and response parsing
- Set up loading states and user feedback
- Test API integration with backend

## Timeline

**Duration:** Half day (Afternoon of Day 1)

### Tasks
- Add changeParent API method
- Verify settings API compatibility
- Implement error handling
- Test API calls

## Technical Implementation

### API Service Updates

```javascript
// frontend/src/services/api.js

// Add to pagesAPI object
export const pagesAPI = {
  // ... existing methods ...
  
  /**
   * Change the parent of a page
   * @param {number} wikiId - Wiki ID
   * @param {number} pageId - Page ID to move
   * @param {number|null} newParentId - New parent ID (null for root)
   * @returns {Promise<{success: boolean, page: object}>}
   */
  changeParent: async (wikiId, pageId, newParentId) => {
    try {
      const response = await apiClient.post(
        `/wikis/${wikiId}/pages/${pageId}/change-parent`,
        { new_parent_id: newParentId }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to change page parent:', error);
      throw error;
    }
  }
};
```

### Auth API Verification

```javascript
// frontend/src/services/api.js

// Verify existing authAPI.updateMe() method
export const authAPI = {
  // ... existing methods ...
  
  /**
   * Update current user's profile and settings
   * @param {object} updates - Fields to update (username, email, settings, etc.)
   * @returns {Promise<{success: boolean, user: object}>}
   */
  updateMe: async (updates) => {
    try {
      const response = await apiClient.patch('/auth/me', updates);
      return response.data;
    } catch (error) {
      console.error('Failed to update user:', error);
      throw error;
    }
  },
  
  /**
   * Update user settings specifically
   * @param {object} settings - Settings object to merge
   * @returns {Promise<{success: boolean, user: object}>}
   */
  updateSettings: async (settings) => {
    return authAPI.updateMe({ settings });
  }
};
```

### Error Handler Utility

```javascript
// frontend/src/utils/errorHandler.js

/**
 * Extract user-friendly error message from API error
 * @param {Error} error - API error object
 * @returns {string} User-friendly error message
 */
export const getErrorMessage = (error) => {
  if (error.response) {
    // Server responded with error status
    const { status, data } = error.response;
    
    if (data && data.error) {
      return data.error;
    }
    
    // Default messages for status codes
    switch (status) {
      case 400:
        return 'Invalid request. Please check your input.';
      case 403:
        return 'You do not have permission to perform this action.';
      case 404:
        return 'The requested resource was not found.';
      case 500:
        return 'Server error occurred. Please try again later.';
      default:
        return `Error: ${status}`;
    }
  } else if (error.request) {
    // Request made but no response
    return 'Network error. Please check your connection.';
  } else {
    // Error setting up request
    return error.message || 'An unexpected error occurred.';
  }
};

/**
 * Handle API error with user feedback
 * @param {Error} error - API error object
 * @param {Function} setError - State setter for error message
 */
export const handleApiError = (error, setError) => {
  const message = getErrorMessage(error);
  console.error('API Error:', error);
  if (setError) {
    setError(message);
  }
  return message;
};
```

### API Response Types

```typescript
// frontend/src/types/api.ts (if using TypeScript)

export interface ChangeParentRequest {
  new_parent_id: number | null;
}

export interface ChangeParentResponse {
  success: boolean;
  page: Page;
}

export interface ApiError {
  error: string;
}

export interface UpdateSettingsRequest {
  settings: {
    disable_move_confirmation?: boolean;
    [key: string]: any;
  };
}
```

### Custom Hook for Page Operations

```javascript
// frontend/src/hooks/usePageOperations.js

import { useState } from 'react';
import { pagesAPI } from '../services/api';
import { handleApiError } from '../utils/errorHandler';

export const usePageOperations = (wikiId, onSuccess) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const changeParent = async (pageId, newParentId) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await pagesAPI.changeParent(wikiId, pageId, newParentId);
      
      if (response.success) {
        if (onSuccess) {
          onSuccess(response.page);
        }
        return response.page;
      }
    } catch (err) {
      const message = handleApiError(err, setError);
      throw new Error(message);
    } finally {
      setLoading(false);
    }
  };
  
  return {
    changeParent,
    loading,
    error,
    clearError: () => setError(null)
  };
};
```

### Toast Notification Helper

```javascript
// frontend/src/utils/toast.js

/**
 * Show success toast notification
 * @param {string} message - Success message
 */
export const showSuccess = (message) => {
  // Implement based on your toast library
  // Example with react-toastify:
  // toast.success(message);
  console.log('SUCCESS:', message);
};

/**
 * Show error toast notification
 * @param {string} message - Error message
 */
export const showError = (message) => {
  // Implement based on your toast library
  // Example with react-toastify:
  // toast.error(message);
  console.error('ERROR:', message);
};

/**
 * Show info toast notification
 * @param {string} message - Info message
 */
export const showInfo = (message) => {
  // Implement based on your toast library
  console.log('INFO:', message);
};
```

## Testing Requirements

### Unit Tests

```javascript
// tests/services/api.test.js

import { pagesAPI, authAPI } from '../services/api';

describe('pagesAPI', () => {
  test('changeParent sends correct request', async () => {
    // Mock API client
    // Verify correct endpoint called
    // Verify correct payload sent
  });
  
  test('changeParent handles successful response', async () => {
    // Mock successful response
    // Verify response parsed correctly
  });
  
  test('changeParent handles error response', async () => {
    // Mock error response
    // Verify error thrown correctly
  });
});

describe('authAPI', () => {
  test('updateSettings merges settings', async () => {
    // Mock API call
    // Verify settings object sent correctly
  });
});
```

### Integration Tests

```javascript
// tests/integration/pageOperations.test.js

import { renderHook, act } from '@testing-library/react-hooks';
import { usePageOperations } from '../hooks/usePageOperations';

describe('usePageOperations', () => {
  test('changeParent updates loading state', async () => {
    const { result } = renderHook(() => usePageOperations(1, jest.fn()));
    
    expect(result.current.loading).toBe(false);
    
    act(() => {
      result.current.changeParent(5, 3);
    });
    
    expect(result.current.loading).toBe(true);
  });
  
  test('changeParent calls onSuccess callback', async () => {
    const onSuccess = jest.fn();
    const { result } = renderHook(() => usePageOperations(1, onSuccess));
    
    await act(async () => {
      await result.current.changeParent(5, 3);
    });
    
    expect(onSuccess).toHaveBeenCalled();
  });
});
```

### Manual Testing

```javascript
// Manual test in browser console

// Test change parent
import { pagesAPI } from './services/api';

// Move page 5 to parent 3 in wiki 1
pagesAPI.changeParent(1, 5, 3)
  .then(response => console.log('Success:', response))
  .catch(error => console.error('Error:', error));

// Move page 5 to root
pagesAPI.changeParent(1, 5, null)
  .then(response => console.log('Success:', response))
  .catch(error => console.error('Error:', error));

// Test settings update
import { authAPI } from './services/api';

authAPI.updateSettings({ disable_move_confirmation: true })
  .then(response => console.log('Settings updated:', response))
  .catch(error => console.error('Error:', error));
```

## Error Handling Scenarios

### Network Errors
```javascript
// No internet connection
// Timeout
// DNS failure
// Display: "Network error. Please check your connection."
```

### Permission Errors
```javascript
// 403 Forbidden
// Display: "You do not have permission to move this page."
```

### Not Found Errors
```javascript
// 404 Page not found
// 404 Parent not found
// Display: "The page or parent could not be found."
```

### Validation Errors
```javascript
// 400 Circular reference
// Display: "Cannot move page to its own descendant."
```

### Server Errors
```javascript
// 500 Internal server error
// Display: "Server error. Please try again later."
```

## Success Criteria

- ✓ changeParent API method successfully calls backend
- ✓ Settings API handles settings updates
- ✓ Error handling provides user-friendly messages
- ✓ Loading states work correctly
- ✓ Success callbacks trigger properly
- ✓ All HTTP status codes handled appropriately
- ✓ Manual testing in browser succeeds
- ✓ Unit tests pass

## Dependencies

- Axios or Fetch API: HTTP client
- React hooks: State management
- Toast library (optional): User notifications

## Next Phase

After Phase 2 completion, proceed to **Phase 3: Confirmation Modal Component** to create the user confirmation dialog.

---

## Progress Tracking

### Feature 1: Change Parent API Method
- [ ] Add changeParent function to pagesAPI
- [ ] Define function parameters (wikiId, pageId, newParentId)
- [ ] Implement POST request to /change-parent endpoint
- [ ] Format request body with new_parent_id
- [ ] Handle null parent for root moves
- [ ] Return response data
- [ ] Add JSDoc comments
- [ ] Export function

### Feature 2: API Error Handling
- [ ] Import API client
- [ ] Wrap API call in try-catch
- [ ] Log errors to console
- [ ] Re-throw errors for caller handling
- [ ] Test with invalid page ID
- [ ] Test with invalid parent ID
- [ ] Test with network disconnected

### Feature 3: Auth API Verification
- [ ] Locate existing updateMe method
- [ ] Verify it accepts arbitrary fields
- [ ] Test settings parameter
- [ ] Add updateSettings convenience method
- [ ] Verify settings merge (not replace)
- [ ] Test settings update
- [ ] Document settings structure

### Feature 4: Error Handler Utility
- [ ] Create errorHandler.js file
- [ ] Implement getErrorMessage function
- [ ] Handle error.response case
- [ ] Handle error.request case
- [ ] Handle error.message case
- [ ] Map status codes to messages
- [ ] Extract server error message
- [ ] Implement handleApiError function
- [ ] Test with various error types

### Feature 5: API Response Types
- [ ] Create types/api.ts file (if using TypeScript)
- [ ] Define ChangeParentRequest interface
- [ ] Define ChangeParentResponse interface
- [ ] Define ApiError interface
- [ ] Define UpdateSettingsRequest interface
- [ ] Export all types
- [ ] Add types to API methods

### Feature 6: usePageOperations Hook
- [ ] Create hooks/usePageOperations.js file
- [ ] Import required dependencies
- [ ] Define hook parameters (wikiId, onSuccess)
- [ ] Add loading state
- [ ] Add error state
- [ ] Implement changeParent function
- [ ] Set loading true before API call
- [ ] Call pagesAPI.changeParent
- [ ] Handle success response
- [ ] Call onSuccess callback
- [ ] Handle errors with handleApiError
- [ ] Set loading false in finally block
- [ ] Add clearError function
- [ ] Return hook values
- [ ] Export hook

### Feature 7: Toast Notification Helper
- [ ] Create utils/toast.js file
- [ ] Implement showSuccess function
- [ ] Implement showError function
- [ ] Implement showInfo function
- [ ] Choose toast library (react-toastify, react-hot-toast)
- [ ] Install toast library
- [ ] Configure toast provider
- [ ] Style toast notifications
- [ ] Test success notification
- [ ] Test error notification

### Feature 8: API Client Configuration
- [ ] Verify API client base URL
- [ ] Verify authentication headers
- [ ] Verify timeout configuration
- [ ] Add request interceptor (if needed)
- [ ] Add response interceptor (if needed)
- [ ] Test with valid token
- [ ] Test with expired token
- [ ] Test with missing token

### Feature 9: Response Parsing
- [ ] Extract response.data from axios
- [ ] Validate response structure
- [ ] Handle missing fields gracefully
- [ ] Parse success field
- [ ] Parse page object
- [ ] Test with complete response
- [ ] Test with partial response

### Feature 10: Manual Testing - Browser Console
- [ ] Open browser dev tools
- [ ] Import pagesAPI in console
- [ ] Test changeParent with valid IDs
- [ ] Verify network request in Network tab
- [ ] Verify request payload
- [ ] Verify response data
- [ ] Test with null parent (move to root)
- [ ] Test with invalid page ID
- [ ] Test with invalid parent ID
- [ ] Import authAPI
- [ ] Test updateSettings
- [ ] Verify settings saved

### Feature 11: Unit Tests - API Methods
- [ ] Set up test environment
- [ ] Mock apiClient
- [ ] Write test: changeParent sends correct request
- [ ] Write test: changeParent with null parent
- [ ] Write test: changeParent handles success
- [ ] Write test: changeParent handles 404
- [ ] Write test: changeParent handles 403
- [ ] Write test: changeParent handles 400
- [ ] Write test: updateSettings merges settings
- [ ] Run all tests
- [ ] Verify test coverage

### Feature 12: Unit Tests - Error Handler
- [ ] Write test: getErrorMessage with response error
- [ ] Write test: getErrorMessage with network error
- [ ] Write test: getErrorMessage with generic error
- [ ] Write test: status code 400 message
- [ ] Write test: status code 403 message
- [ ] Write test: status code 404 message
- [ ] Write test: status code 500 message
- [ ] Write test: handleApiError calls setError
- [ ] Run error handler tests

### Feature 13: Integration Tests - usePageOperations
- [ ] Set up React Testing Library
- [ ] Write test: hook initializes correctly
- [ ] Write test: changeParent sets loading state
- [ ] Write test: changeParent calls API
- [ ] Write test: changeParent calls onSuccess
- [ ] Write test: changeParent handles errors
- [ ] Write test: clearError clears error state
- [ ] Mock API responses
- [ ] Run integration tests

### Feature 14: Documentation
- [ ] Document changeParent API method
- [ ] Document parameters and return value
- [ ] Document error handling
- [ ] Add usage examples
- [ ] Document usePageOperations hook
- [ ] Document error handler utility
- [ ] Document toast notifications
- [ ] Create API integration guide

### Feature 15: Edge Case Handling
- [ ] Handle undefined wikiId
- [ ] Handle undefined pageId
- [ ] Handle undefined newParentId
- [ ] Handle malformed response
- [ ] Handle timeout errors
- [ ] Handle CORS errors
- [ ] Test with slow network
- [ ] Document edge cases
