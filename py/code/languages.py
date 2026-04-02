"""Supported programming languages for code execution."""
from typing import Dict, List, Set


class Languages:
    """Manages supported programming languages."""
    
    # Language definitions with metadata
    SUPPORTED_LANGUAGES: Dict[str, Dict[str, any]] = {
        "python": {
            "name": "Python",
            "extensions": [".py"],
            "e2b_name": "python",
            "标志性": True
        },
        "javascript": {
            "name": "JavaScript",
            "extensions": [".js"],
            "e2b_name": "javascript",
            "标志性": True
        },
        "typescript": {
            "name": "TypeScript",
            "extensions": [".ts"],
            "e2b_name": "typescript",
            "标志性": True
        },
        "r": {
            "name": "R",
            "extensions": [".r", ".R"],
            "e2b_name": "r",
            "标志性": True
        },
        "java": {
            "name": "Java",
            "extensions": [".java"],
            "e2b_name": "java",
            "标志性": True
        },
        "go": {
            "name": "Go",
            "extensions": [".go"],
            "e2b_name": "go",
            "标志性": True
        },
        "rust": {
            "name": "Rust",
            "extensions": [".rs"],
            "e2b_name": "rust",
            "标志性": True
        },
        "c": {
            "name": "C",
            "extensions": [".c"],
            "e2b_name": "c",
            "标志性": True
        },
        "cpp": {
            "name": "C++",
            "extensions": [".cpp", ".cc", ".cxx"],
            "e2b_name": "cpp",
            "标志性": True
        },
        "ruby": {
            "name": "Ruby",
            "extensions": [".rb"],
            "e2b_name": "ruby",
            "标志性": True
        },
        "php": {
            "name": "PHP",
            "extensions": [".php"],
            "e2b_name": "php",
            "标志性": True
        },
        "kotlin": {
            "name": "Kotlin",
            "extensions": [".kt", ".kts"],
            "e2b_name": "kotlin",
            "标志性": True
        },
        "scala": {
            "name": "Scala",
            "extensions": [".scala"],
            "e2b_name": "scala",
            "标志性": True
        },
        "julia": {
            "name": "Julia",
            "extensions": [".jl"],
            "e2b_name": "julia",
            "标志性": True
        },
    }
    
    # Languages supported by local sandbox (node_runner)
    LOCAL_SANDBOX_LANGUAGES: Set[str] = {
        "python", "javascript", "typescript", "r", "java",
        "bash", "go", "rust", "c", "cpp", "php", "ruby",
        "kotlin", "scala", "julia", "sql"
    }
    
    # Languages supported by E2B sandbox
    E2B_SANDBOX_LANGUAGES: Set[str] = {
        "python", "javascript", "typescript", "r", "java"
    }
    
    @classmethod
    def list_all(cls) -> List[str]:
        """Get list of all supported language identifiers."""
        return list(cls.SUPPORTED_LANGUAGES.keys())
    
    @classmethod
    def list_local_supported(cls) -> List[str]:
        """Get list of languages supported by local sandbox."""
        return sorted(cls.LOCAL_SANDBOX_LANGUAGES)
    
    @classmethod
    def list_e2b_supported(cls) -> List[str]:
        """Get list of languages supported by E2B sandbox."""
        return sorted(cls.E2B_SANDBOX_LANGUAGES)
    
    @classmethod
    def is_supported(cls, language: str) -> bool:
        """Check if a language is supported by any sandbox."""
        return language.lower() in cls.SUPPORTED_LANGUAGES
    
    @classmethod
    def is_local_supported(cls, language: str) -> bool:
        """Check if a language is supported by local sandbox."""
        return language.lower() in cls.LOCAL_SANDBOX_LANGUAGES
    
    @classmethod
    def is_e2b_supported(cls, language: str) -> bool:
        """Check if a language is supported by E2B sandbox."""
        return language.lower() in cls.E2B_SANDBOX_LANGUAGES
    
    @classmethod
    def get_metadata(cls, language: str) -> Dict[str, any]:
        """Get metadata for a language."""
        return cls.SUPPORTED_LANGUAGES.get(language.lower(), {})
    
    @classmethod
    def get_e2b_name(cls, language: str) -> str:
        """Get the E2B sandbox language name."""
        meta = cls.SUPPORTED_LANGUAGES.get(language.lower(), {})
        return meta.get("e2b_name", language.lower())
