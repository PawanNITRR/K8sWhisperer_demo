from pathlib import Path


def load_prompt(filename: str) -> str:
    return (Path(__file__).parent / "prompts" / filename).read_text(encoding="utf-8")
