"""
Text Chunking Service

Intelligently splits long technical documents into chunks suitable for embedding generation.
Preserves markdown structure and heading context for better semantic search.
"""

import re
import tiktoken
from typing import List, Dict, Tuple
from flask import current_app


class TextChunker:
    """
    Chunks text for embedding generation with markdown-aware splitting.
    
    Features:
    - Respects markdown heading hierarchy
    - Preserves code blocks
    - Maintains context with overlapping chunks
    - Tracks heading path for each chunk
    """
    
    def __init__(self, 
                 max_tokens: int = None,
                 overlap_tokens: int = None,
                 encoding_name: str = 'cl100k_base'):
        """
        Initialize the text chunker.
        
        Args:
            max_tokens: Maximum tokens per chunk (default from config)
            overlap_tokens: Overlap between chunks (default from config)
            encoding_name: Tiktoken encoding to use for token counting
        """
        self.max_tokens = max_tokens or current_app.config.get('MAX_CHUNK_TOKENS', 400)
        self.overlap_tokens = overlap_tokens or current_app.config.get('CHUNK_OVERLAP_TOKENS', 50)
        
        try:
            self.encoder = tiktoken.get_encoding(encoding_name)
        except Exception:
            # Fallback to simple word-based counting if tiktoken unavailable
            self.encoder = None
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if self.encoder:
            return len(self.encoder.encode(text))
        else:
            # Rough approximation: ~0.75 tokens per word
            return int(len(text.split()) * 0.75)
    
    def extract_headings(self, text: str) -> List[Tuple[int, str, int]]:
        """
        Extract markdown headings with their positions.
        
        Returns:
            List of (level, heading_text, char_position) tuples
        """
        headings = []
        pattern = r'^(#{1,6})\s+(.+)$'
        
        for match in re.finditer(pattern, text, re.MULTILINE):
            level = len(match.group(1))
            heading = match.group(2).strip()
            position = match.start()
            headings.append((level, heading, position))
        
        return headings
    
    def get_heading_path(self, headings: List[Tuple[int, str, int]], 
                        position: int) -> str:
        """
        Get the hierarchical heading path for a given position in the text.
        
        Args:
            headings: List of (level, heading, position) tuples
            position: Character position in text
        
        Returns:
            Heading path like "Introduction > Setup > Installation"
        """
        # Find all headings before this position
        relevant_headings = [(level, heading) for level, heading, pos in headings if pos < position]
        
        if not relevant_headings:
            return ""
        
        # Build hierarchical path
        path = []
        current_level = 0
        
        for level, heading in relevant_headings:
            if level <= current_level:
                # Pop back to appropriate level
                path = path[:level-1]
            path.append(heading)
            current_level = level
        
        return " > ".join(path)
    
    def split_by_paragraphs(self, text: str) -> List[str]:
        """Split text by paragraphs while preserving code blocks."""
        # Split on double newlines, but preserve code blocks
        code_block_pattern = r'```[\s\S]*?```'
        code_blocks = {}
        
        # Replace code blocks with placeholders
        for i, match in enumerate(re.finditer(code_block_pattern, text)):
            placeholder = f"__CODE_BLOCK_{i}__"
            code_blocks[placeholder] = match.group(0)
            text = text[:match.start()] + placeholder + text[match.end():]
        
        # Split into paragraphs
        paragraphs = re.split(r'\n\s*\n', text)
        
        # Restore code blocks
        restored_paragraphs = []
        for para in paragraphs:
            for placeholder, code in code_blocks.items():
                para = para.replace(placeholder, code)
            if para.strip():
                restored_paragraphs.append(para.strip())
        
        return restored_paragraphs
    
    def chunk_page(self, page_title: str, page_content: str) -> List[Dict[str, any]]:
        """
        Chunk a wiki page into embedding-ready segments.
        
        Args:
            page_title: Title of the page
            page_content: Markdown content of the page
        
        Returns:
            List of chunk dictionaries with:
            - chunk_index: Position in page
            - chunk_text: The text content
            - heading_path: Hierarchical heading context
            - token_count: Approximate token count
        """
        if not page_content or not page_content.strip():
            # Empty page - create single chunk with title only
            return [{
                'chunk_index': 0,
                'chunk_text': page_title,
                'heading_path': '',
                'token_count': self.count_tokens(page_title)
            }]
        
        # Extract heading structure
        headings = self.extract_headings(page_content)
        
        # Split into paragraphs
        paragraphs = self.split_by_paragraphs(page_content)
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        chunk_index = 0
        
        # Include title in first chunk
        title_prefix = f"# {page_title}\n\n"
        current_chunk.append(title_prefix)
        current_tokens = self.count_tokens(title_prefix)
        
        for para in paragraphs:
            para_tokens = self.count_tokens(para)
            
            # If single paragraph exceeds max, split it further
            if para_tokens > self.max_tokens:
                # Flush current chunk if any
                if len(current_chunk) > 1:  # More than just title
                    chunk_text = ''.join(current_chunk)
                    position = page_content.find(current_chunk[-1])
                    chunks.append({
                        'chunk_index': chunk_index,
                        'chunk_text': chunk_text,
                        'heading_path': self.get_heading_path(headings, position),
                        'token_count': current_tokens
                    })
                    chunk_index += 1
                    
                    # Start new chunk with overlap
                    current_chunk = [current_chunk[-1]]
                    current_tokens = self.count_tokens(current_chunk[0])
                
                # Split long paragraph by sentences
                sentences = re.split(r'([.!?]+\s+)', para)
                for sentence in sentences:
                    if not sentence.strip():
                        continue
                    
                    sentence_tokens = self.count_tokens(sentence)
                    
                    if current_tokens + sentence_tokens > self.max_tokens:
                        # Save current chunk
                        chunk_text = ''.join(current_chunk)
                        position = page_content.find(current_chunk[-1]) if current_chunk else 0
                        chunks.append({
                            'chunk_index': chunk_index,
                            'chunk_text': chunk_text,
                            'heading_path': self.get_heading_path(headings, position),
                            'token_count': current_tokens
                        })
                        chunk_index += 1
                        
                        # Start new chunk with overlap
                        overlap_text = sentence if sentence_tokens < self.overlap_tokens else ''
                        current_chunk = [overlap_text]
                        current_tokens = self.count_tokens(overlap_text)
                    else:
                        current_chunk.append(sentence)
                        current_tokens += sentence_tokens
            
            elif current_tokens + para_tokens > self.max_tokens:
                # Save current chunk
                chunk_text = ''.join(current_chunk)
                position = page_content.find(current_chunk[-1]) if current_chunk else 0
                chunks.append({
                    'chunk_index': chunk_index,
                    'chunk_text': chunk_text,
                    'heading_path': self.get_heading_path(headings, position),
                    'token_count': current_tokens
                })
                chunk_index += 1
                
                # Start new chunk with overlap from previous chunk
                overlap_size = 0
                overlap_parts = []
                for part in reversed(current_chunk):
                    part_tokens = self.count_tokens(part)
                    if overlap_size + part_tokens <= self.overlap_tokens:
                        overlap_parts.insert(0, part)
                        overlap_size += part_tokens
                    else:
                        break
                
                current_chunk = overlap_parts + [para]
                current_tokens = self.count_tokens(''.join(current_chunk))
            else:
                # Add paragraph to current chunk
                current_chunk.append('\n\n' + para)
                current_tokens += para_tokens + 2  # Account for newlines
        
        # Add final chunk if any
        if current_chunk and current_tokens > 0:
            chunk_text = ''.join(current_chunk)
            position = page_content.find(current_chunk[-1]) if len(current_chunk) > 1 else 0
            chunks.append({
                'chunk_index': chunk_index,
                'chunk_text': chunk_text,
                'heading_path': self.get_heading_path(headings, position),
                'token_count': current_tokens
            })
        
        return chunks if chunks else [{
            'chunk_index': 0,
            'chunk_text': page_title,
            'heading_path': '',
            'token_count': self.count_tokens(page_title)
        }]


def chunk_page_content(page_title: str, page_content: str,
                       max_tokens: int = None,
                       overlap_tokens: int = None) -> List[Dict[str, any]]:
    """
    Convenience function to chunk a page.
    
    Args:
        page_title: Page title
        page_content: Page markdown content
        max_tokens: Max tokens per chunk (optional)
        overlap_tokens: Overlap tokens (optional)
    
    Returns:
        List of chunk dictionaries
    """
    chunker = TextChunker(max_tokens=max_tokens, overlap_tokens=overlap_tokens)
    return chunker.chunk_page(page_title, page_content)
