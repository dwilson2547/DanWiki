"""
Prompt template registry and loader.
"""
import importlib.util
import os
from typing import Protocol


class PromptTemplate(Protocol):
    """Protocol for prompt template modules."""
    SYSTEM_PROMPT: str
    
    def format_prompt(
        self,
        title: str,
        content: str,
        existing_tags: list[str],
        breadcrumbs: list[str] | None = None
    ) -> str:
        """Format the user prompt."""
        ...


class PromptRegistry:
    """Registry for available prompt templates."""
    
    def __init__(self):
        self._templates: dict[str, PromptTemplate] = {}
        self._load_builtin_templates()
    
    def _load_builtin_templates(self):
        """Load built-in prompt templates."""
        from prompts import detailed, quick, technical, general
        
        self._templates = {
            "detailed": detailed,
            "quick": quick,
            "technical": technical,
            "general": general,
        }
    
    def get_template(self, name: str) -> PromptTemplate:
        """Get a prompt template by name."""
        if name not in self._templates:
            raise ValueError(
                f"Unknown prompt template: {name}. "
                f"Available: {', '.join(self.available_templates())}"
            )
        return self._templates[name]
    
    def available_templates(self) -> list[str]:
        """Get list of available template names."""
        return list(self._templates.keys())
    
    def register_template(self, name: str, template: PromptTemplate):
        """Register a custom prompt template."""
        self._templates[name] = template


# Global registry instance
registry = PromptRegistry()


def get_template(name: str = "detailed") -> PromptTemplate:
    """Get a prompt template by name."""
    return registry.get_template(name)


def list_templates() -> list[str]:
    """List available prompt templates."""
    return registry.available_templates()
