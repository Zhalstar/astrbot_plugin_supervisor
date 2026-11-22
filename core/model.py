from enum import Enum


class SupervisorModel(Enum):
    """Available response models for supervised messages."""

    IMAGE = "image"
    LLM = "llm"
    POKE = "poke"

    def __str__(self) -> str:
        """Return the configuration-facing model name."""
        return self.value
