"""
Base LLM interface for the AI Study Buddy Agent.
"""

from abc import ABC, abstractmethod


class BaseLLM(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """
        Generate text response given a prompt.
        Must return formatted thought/action or final answer.
        """
        pass

