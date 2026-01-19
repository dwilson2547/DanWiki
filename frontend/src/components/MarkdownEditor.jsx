import { useRef, useEffect, useCallback, forwardRef, useImperativeHandle } from 'react';
import { Editor } from '@toast-ui/react-editor';
import '@toast-ui/editor/dist/toastui-editor.css';
import '@toast-ui/editor/dist/theme/toastui-editor-dark.css';
import { useTheme } from '../context/ThemeContext';
import codeSyntaxHighlight from '@toast-ui/editor-plugin-code-syntax-highlight';
import '@toast-ui/editor-plugin-code-syntax-highlight/dist/toastui-editor-plugin-code-syntax-highlight.css';
import Prism from 'prismjs';
import '../styles/prism-theme.css'; // Custom theme that supports dark mode

// Import base dependencies first
import 'prismjs/components/prism-clike';
import 'prismjs/components/prism-markup';
import 'prismjs/components/prism-markup-templating';

// Import commonly used languages
import 'prismjs/components/prism-javascript';
import 'prismjs/components/prism-typescript';
import 'prismjs/components/prism-jsx';
import 'prismjs/components/prism-tsx';
import 'prismjs/components/prism-python';
import 'prismjs/components/prism-java';
import 'prismjs/components/prism-c';
import 'prismjs/components/prism-cpp';
import 'prismjs/components/prism-csharp';
import 'prismjs/components/prism-go';
import 'prismjs/components/prism-rust';
import 'prismjs/components/prism-ruby';
import 'prismjs/components/prism-php';
import 'prismjs/components/prism-bash';
import 'prismjs/components/prism-sql';
import 'prismjs/components/prism-json';
import 'prismjs/components/prism-yaml';
import 'prismjs/components/prism-markdown';
import 'prismjs/components/prism-css';
import 'prismjs/components/prism-scss';
import 'prismjs/components/prism-docker';
import 'prismjs/components/prism-git';

import { attachmentsAPI } from '../services/api';

const MarkdownEditor = forwardRef(function MarkdownEditor({ 
  wikiId, 
  pageId, 
  initialValue = '', 
  onChange,
  height = '500px',
  placeholder = 'Start writing...'
}, ref) {
  const editorRef = useRef(null);
  const { theme } = useTheme();

  // Handle image upload (drag-drop or button)
  const handleImageUpload = useCallback(async (blob, callback) => {
    if (!wikiId || !pageId) {
      console.error('Wiki ID and Page ID required for image upload');
      callback('', 'Upload failed');
      return;
    }

    try {
      const response = await attachmentsAPI.uploadImage(wikiId, pageId, blob);
      const { url } = response.data;
      callback(url, blob.name || 'uploaded image');
    } catch (error) {
      console.error('Image upload failed:', error);
      callback('', 'Upload failed');
    }
  }, [wikiId, pageId]);

  // Handle clipboard paste for images
  useEffect(() => {
    const editorInstance = editorRef.current?.getInstance();
    if (!editorInstance) return;

    const editorEl = editorInstance.getEditorElements().mdEditor;
    if (!editorEl) return;

    const handlePaste = async (event) => {
      const items = event.clipboardData?.items;
      if (!items) return;

      for (const item of items) {
        if (item.type.startsWith('image/')) {
          event.preventDefault();
          
          const file = item.getAsFile();
          if (!file) continue;

          if (!wikiId || !pageId) {
            console.error('Wiki ID and Page ID required for image paste');
            return;
          }

          try {
            // Show loading placeholder
            const placeholder = `![Uploading ${file.name}...]()`;
            editorInstance.insertText(placeholder);

            const response = await attachmentsAPI.uploadImage(wikiId, pageId, file);
            const { url } = response.data;

            // Replace placeholder with actual image
            const markdown = editorInstance.getMarkdown();
            const newMarkdown = markdown.replace(placeholder, `![${file.name}](${url})`);
            editorInstance.setMarkdown(newMarkdown);
          } catch (error) {
            console.error('Paste image upload failed:', error);
            // Remove the placeholder on error
            const markdown = editorInstance.getMarkdown();
            const newMarkdown = markdown.replace(`![Uploading ${file.name}...]()`, '');
            editorInstance.setMarkdown(newMarkdown);
          }
          
          return;
        }
      }
    };

    editorEl.addEventListener('paste', handlePaste);
    
    return () => {
      editorEl.removeEventListener('paste', handlePaste);
    };
  }, [wikiId, pageId]);

  // Handle content changes
  const handleChange = useCallback(() => {
    const editorInstance = editorRef.current?.getInstance();
    if (editorInstance && onChange) {
      const markdown = editorInstance.getMarkdown();
      onChange(markdown);
    }
  }, [onChange]);

  // Add auth tokens to attachment images in preview
  useEffect(() => {
    const addTokenToPreviewImages = () => {
      const editorInstance = editorRef.current?.getInstance();
      if (!editorInstance) return;

      const previewEl = editorInstance.getEditorElements()?.preview;
      if (!previewEl) return;

      const token = localStorage.getItem('access_token');
      if (token) {
        const images = previewEl.querySelectorAll('img[src*="/api/attachments/"]');
        images.forEach(img => {
          const src = img.getAttribute('src');
          if (src && !src.includes('token=')) {
            const separator = src.includes('?') ? '&' : '?';
            img.setAttribute('src', `${src}${separator}token=${encodeURIComponent(token)}`);
          }
        });
      }
    };

    // Set up a mutation observer to watch for changes in the preview pane
    const editorInstance = editorRef.current?.getInstance();
    if (editorInstance) {
      const previewEl = editorInstance.getEditorElements()?.preview;
      if (previewEl) {
        const observer = new MutationObserver(() => {
          addTokenToPreviewImages();
        });

        observer.observe(previewEl, {
          childList: true,
          subtree: true
        });

        // Initial processing
        addTokenToPreviewImages();

        return () => observer.disconnect();
      }
    }
  }, []);

  // Get markdown content
  const getMarkdown = useCallback(() => {
    const editorInstance = editorRef.current?.getInstance();
    return editorInstance ? editorInstance.getMarkdown() : '';
  }, []);

  // Set markdown content
  const setMarkdown = useCallback((markdown) => {
    const editorInstance = editorRef.current?.getInstance();
    if (editorInstance) {
      editorInstance.setMarkdown(markdown);
    }
  }, []);

  // Insert text at cursor position
  const insertText = useCallback((text) => {
    const editorInstance = editorRef.current?.getInstance();
    if (editorInstance) {
      editorInstance.insertText(text);
    }
  }, []);

  // Expose methods via imperative handle
  useImperativeHandle(ref, () => ({
    getMarkdown,
    setMarkdown,
    insertText
  }), [getMarkdown, setMarkdown, insertText]);

  return (
    <Editor
      key={theme}
      ref={editorRef}
      initialValue={initialValue}
      previewStyle="vertical"
      height={height}
      initialEditType="markdown"
      useCommandShortcut={true}
      usageStatistics={false}
      placeholder={placeholder}
      onChange={handleChange}
      theme={theme}
      autofocus={false}
      hooks={{
        addImageBlobHook: handleImageUpload
      }}
      plugins={[[codeSyntaxHighlight, { highlighter: Prism }]]}
      toolbarItems={[
        ['heading', 'bold', 'italic', 'strike'],
        ['hr', 'quote'],
        ['ul', 'ol', 'task', 'indent', 'outdent'],
        ['table', 'image', 'link'],
        ['code', 'codeblock'],
        ['scrollSync'],
      ]}
      customHTMLRenderer={{
        // Enable better markdown rendering
      }}
    />
  );
});

export default MarkdownEditor;
