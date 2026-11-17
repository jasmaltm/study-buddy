"""
AI Study Buddy Agent — Main Interactive Runner
Demonstrates the 7 Pillars in action:
1. Think -> Act -> Look Loop
2. 2-4 Clearly Described Tools
3. Self-healing / Error Recovery on tool failure
4. Memory across tasks
5. A plan before it acts
6. Safety: Asks you first, Step limit, Audit log
7. Fake LLM first, then Real LLM
"""

import sys
import os

from agent.core import StudyBuddyAgent
from agent.memory import AgentMemory
from agent.safety import SafetyGuard, AuditLogger
from agent.llm.fake_llm import FakeLLM
from agent.llm.real_llm import GeminiLLM, OpenAILLM, OllamaLLM
import config


def get_llm():
    if config.USE_FAKE_LLM:
        print("[LLM Engine] Using deterministic FakeLLM (Pillar 7: Fake LLM first).")
        return FakeLLM()
    
    if config.REAL_LLM_PROVIDER == "ollama":
        print("[LLM Engine] Using Local LLM: Ollama / Llama.")
        return OllamaLLM(model="llama3.2:3b")
    elif config.REAL_LLM_PROVIDER == "gemini":
        print("[LLM Engine] Using RealLLM: Google Gemini.")
        return GeminiLLM(api_key=config.GEMINI_API_KEY)
    else:
        print("[LLM Engine] Using RealLLM: OpenAI.")
        return OpenAILLM(api_key=config.OPENAI_API_KEY)


def main():
    print("=" * 65)
    print("        AI STUDY BUDDY — AUTONOMOUS 7-PILLAR AGENT")
    print("=" * 65)
    print("Pillars active:")
    print("  1. Loop: Think -> Act -> Look (ReAct)")
    print("  2. Tools: search_knowledge_base, calculate_math, quiz, save_notes")
    print("  3. Self-Healing: Error recovery on tool failure")
    print("  4. Memory: Persistent state across tasks (storage/memory.json)")
    print("  5. Planning: Structured step plan before acting")
    print("  6. Safety: Human-in-the-Loop approval, step limit, audit log")
    if config.USE_FAKE_LLM:
        print("  7. LLM Mode: FakeLLM (Test Mode)")
    else:
        print(f"  7. LLM Mode: Real LLM ({config.REAL_LLM_PROVIDER})")
    print("=" * 65)

    llm = get_llm()
    memory = AgentMemory(storage_path=config.MEMORY_FILE_PATH)
    logger = AuditLogger(log_file=config.LOG_FILE_PATH)
    safety = SafetyGuard(max_steps=config.MAX_STEPS, logger=logger)

    agent = StudyBuddyAgent(
        llm=llm,
        memory=memory,
        safety=safety,
        logger=logger,
        max_steps=config.MAX_STEPS
    )

    import argparse
    parser = argparse.ArgumentParser(description="AI Study Buddy Runner")
    parser.add_argument("--scenario", "-s", type=str, default="", help="Scenario choice: 1, 2, or custom text")
    args, unknown = parser.parse_known_args()

    default_tasks = [
        "Explain photosynthesis simply and give me a practice quiz",
        "Calculate the falling distance of an object under gravity after 5 seconds using (9.8 * 5^2) / 2"
    ]

    if args.scenario:
        choice = args.scenario.strip()
    else:
        print("\nSelect a task to run or type your own:")
        print("  1. Explain photosynthesis and generate a practice quiz")
        print("  2. Solve falling distance formula (Demonstrates Pillar 3 error self-correction)")
        print("  3. Custom prompt")
        
        try:
            choice = input("\nEnter choice (1, 2, or 3) [Default: 1]: ").strip()
        except (EOFError, KeyboardInterrupt):
            choice = "1"
            print("1")
    
    if choice == "2":
        task = default_tasks[1]
    elif choice == "3":
        try:
            task = input("\nEnter your study question/task: ").strip()
        except (EOFError, KeyboardInterrupt):
            task = default_tasks[0]
        if not task:
            task = default_tasks[0]
    else:
        task = default_tasks[0]

    print(f"\n[RUNNING AGENT] Task: '{task}'")
    print("-" * 65)

    result = agent.run(task)

    print("\n" + "=" * 65)
    print("                  FINAL AGENT RESULT")
    print("=" * 65)
    print(result["final_answer"])
    print("-" * 65)
    print(f"Total steps executed: {result['total_steps']}")
    print(f"Tools invoked: {result['tools_used']}")
    print(f"Audit log saved to: {config.LOG_FILE_PATH}")
    print(f"Memory saved to: {config.MEMORY_FILE_PATH}")
    print("=" * 65)


if __name__ == "__main__":
    main()

