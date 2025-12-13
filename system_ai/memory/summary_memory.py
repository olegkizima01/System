from dataclasses import dataclass


@dataclass
class SummaryMemory:
    summary: str = ""

    def update(self, new_summary: str) -> None:
        self.summary = new_summary
