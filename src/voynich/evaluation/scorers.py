"""Public-input-only evaluators. Truth metrics are a separate post-search step."""
from dataclasses import asdict, dataclass
from functools import lru_cache
from voynich.decipher_search.core import Config, LanguageModel, evaluate, inventory, edit_accuracy
from voynich.laboratory.fixtures import PublicInput
from voynich.laboratory.manifest import fingerprint
from .outcomes import ScoreReport


@lru_cache(maxsize=2)
def model(training, order):
    return LanguageModel(training, order)


@dataclass(frozen=True)
class Evaluation:
    score: ScoreReport
    payload: dict
    status: str = "valid"
    error: str | None = None

    @property
    def loss(self):
        return self.score.loss

    @property
    def denominator(self):
        return self.score.denominator


@dataclass(frozen=True)
class KeyEvaluator:
    public: PublicInput
    training: str
    config: Config

    def __post_init__(self):
        if not isinstance(self.public, PublicInput):
            raise TypeError("evaluator accepts public input, never a fixture")
        self.config.validate()
        if (self.config.spacing == "preserve") != (self.public.spacing == "preserve"):
            raise ValueError("evaluator/input spacing mismatch")

    def identity(self):
        return {"evaluator": "legacy-beam-cost-v1", "public": asdict(self.public),
                "training_hash": fingerprint(self.training), "config": asdict(self.config),
                "fidelity": {"beam": self.config.beam}, "deterministic": True}

    def __call__(self, candidate):
        lm = model(self.training, self.config.order)
        value = evaluate(self.public.ciphertext, candidate.data["key"], lm, self.config,
                         inventory(lm, self.config))
        denominator = max(1, len(self.public.ciphertext.replace(" ", "")))
        if not value["valid"]:
            return Evaluation(ScoreReport("legacy-beam-cost-v1", (), denominator, 0, False,
                diagnostics=("constraint failure or no surviving beam path",)), {}, "invalid")
        score = ScoreReport("legacy-beam-cost-v1", (
            ("language_bits", value["language_bits"]),
            ("encoding_choice_bits", value["encoding_choice_bits"]),
            ("weighted_key_bits", self.config.key_weight * value["key_bits"])), denominator)
        # This is bounded best-path decoding, not evidence of plaintext uniqueness.
        return Evaluation(score, {"plaintext": value["plaintext"], "path": value["path"],
            "decoding": {"coverage": 1, "uniqueness": "unresolved", "algorithm": "beam",
                         "beam": self.config.beam, "complete_enumeration": False}})


@dataclass(frozen=True)
class PageEvaluator:
    document: object
    tables: tuple
    method: object
    training: str
    order: int = 4
    additive: bool = True

    def identity(self):
        return {"evaluator": "page-language-v1", "document": asdict(self.document),
                "tables": [asdict(k) for k in self.tables], "method": asdict(self.method),
                "training_hash": fingerprint(self.training), "order": self.order,
                "additive": self.additive, "deterministic": True}

    def __call__(self, candidate):
        outcome = self.method.execute(self.document, self.tables,
            tuple(candidate.data["choices"]), decrypt=True)
        texts = [p.text for p in outcome.document.pages]
        lm = model(self.training, self.order)
        cost = sum(lm.nll(t) for t in texts) if self.additive else lm.nll(" ".join(texts))
        return Evaluation(ScoreReport("page-language-v1", (("language_bits", cost),),
            sum(len(p.text) for p in self.document.pages)), {"plaintexts": texts})


def independent_page_choices(evaluator: PageEvaluator):
    """Exact shortcut only for declared state independence and additive scoring."""
    from dataclasses import replace
    from voynich.ciphers.contracts import Document
    from voynich.search.strategies import Candidate
    if not evaluator.method.capabilities().independent_pages or not evaluator.additive:
        raise ValueError("pagewise optimization invalid with coupled state or cross-page scoring")
    choices = []
    for page in evaluator.document.pages:
        local = replace(evaluator, document=Document((page,)))
        ranked = [(local(Candidate.create("page-choice-v1", choices=[i])).loss, i)
                  for i in range(len(evaluator.tables))]
        choices.append(min(ranked)[1])
    return Candidate.create("page-choice-v1", choices=choices)


def recovery_metrics(prediction: str, truth: str):
    return {"edit_accuracy": edit_accuracy(prediction, truth),
            "nonspace_edit_accuracy": edit_accuracy(prediction.replace(" ", ""), truth.replace(" ", ""))}
