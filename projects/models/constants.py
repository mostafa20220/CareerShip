from django.db import models

class PistonLanguages(models.TextChoices):
    PYTHON = 'python', 'Python'
    GO = 'go', 'Go'
    CPP = 'cpp', 'C++'
    JAVASCRIPT = 'javascript', 'JavaScript'
    JAVA = 'java', 'Java'
    C = 'c', 'C'
    RUST = 'rust', 'Rust'
    RUBY = 'ruby', 'Ruby'
    PHP = 'php', 'PHP'
    CSHARP = 'csharp', 'C#'

    @classmethod
    def get_file_extension(cls, language: str) -> str:
        """Returns the appropriate file extension for the given programming language."""
        extensions = {
            cls.PYTHON: 'py',
            cls.JAVASCRIPT: 'js',
            cls.JAVA: 'java',
            cls.CPP: 'cpp',
            cls.C: 'c',
            cls.GO: 'go',
            cls.RUST: 'rs',
            cls.RUBY: 'rb',
            cls.PHP: 'php',
            cls.CSHARP: 'cs'
        }
        return extensions.get(language, 'txt')
