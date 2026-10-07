from dataclasses import dataclass
import math


@dataclass(frozen=True)
class ScoreReport:
    scorer: str
    components: tuple[tuple[str, float], ...]
    denominator: int
    coverage: float = 1.0
    valid: bool = True
    units: str = "exploratory bits per input symbol"
    direction: str = "minimize"
    diagnostics: tuple[str, ...] = ()

    def __post_init__(self):
        if self.denominator < 1 or not 0 <= self.coverage <= 1:
            raise ValueError("invalid score denominator/coverage")
        if self.direction != "minimize":
            raise NotImplementedError("initial runner minimizes cost")
        if any(not math.isfinite(v) for _, v in self.components):
            raise ValueError("nonfinite scores must be represented as invalid results")
        if len({k for k, _ in self.components}) != len(self.components):
            raise ValueError("duplicate score components")

    @property
    def loss(self):
        return sum(v for _, v in self.components) / self.denominator if self.valid else None
