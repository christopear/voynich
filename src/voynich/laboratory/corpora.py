"""Pinned research corpora and explicitly lossy orthographic preparation."""
from dataclasses import dataclass
from pathlib import Path
import unicodedata
import xml.etree.ElementTree as ET
from voynich.decipher_search.core import normalize, digest
from voynich.paths import ROOT

# One-to-one storage alphabet for normalized Greek letters, not a historical
# transliteration claim. Diacritics/final sigma are normalized before this map.
# Explicit entries avoid relying on visual similarity between Greek/Latin glyphs.
GREEK = {"α":"a","β":"b","γ":"g","δ":"d","ε":"e","ζ":"z","η":"h","θ":"q",
         "ι":"i","κ":"k","λ":"l","μ":"m","ν":"n","ξ":"x","ο":"o","π":"p",
         "ρ":"r","σ":"s","τ":"t","υ":"u","φ":"f","χ":"c","ψ":"y","ω":"w"}


def greek_normalize(text):
    decomposed = unicodedata.normalize("NFD", text.lower()).replace("ς", "σ")
    plain = "".join(c for c in decomposed if not unicodedata.combining(c))
    return " ".join("".join(c if c in GREEK else " " for c in plain).split())


def greek_encode(text):
    normalized = greek_normalize(text)
    return "".join(GREEK.get(c, c) for c in normalized)


def greek_decode(text):
    inverse = {v: k for k, v in GREEK.items()}
    if any(c not in inverse and c != " " for c in text):
        raise ValueError("outside the declared Greek storage alphabet")
    return "".join(inverse.get(c, c) for c in text)


def tei_body(path):
    tree = ET.parse(path)
    body = tree.find(".//{http://www.tei-c.org/ns/1.0}body")
    if body is None:
        raise ValueError("TEI body absent")
    def render(node):
        tag = node.tag.rsplit("}", 1)[-1]
        if tag in {"note", "head", "bibl", "speaker"}:
            return ""
        value = node.text or ""
        for child in node:
            value += render(child) + (child.tail or "")
        return value + (" " if tag in {"div", "p", "l", "lb"} else "")
    return " ".join(render(body).split())


@dataclass(frozen=True)
class Corpus:
    id: str
    language: str
    work: str
    path: Path
    raw: str
    prepared: str
    normalization: str
    source_uri: str | None = None

    def display(self, text):
        return greek_decode(text) if self.language == "ancient-greek" else text

    @property
    def raw_hash(self):
        return digest(self.raw)


def load_corpora(root=ROOT):
    import json
    result = []
    for name, language, work, relative in (
        ("alfonsi", "latin", "Petrus Alfonsi, Disciplina clericalis", "data/latin_alfonsi.txt"),
        ("dante", "italian", "Dante, existing repository passage", "data/italian_dante.txt"),
        ("caesar", "latin", "Caesar, De bello Gallico (Holmes 1914 edition)",
         "data/laboratory_sources/phi0448.phi001.perseus-lat2.xml"),
        ("homer", "ancient-greek", "Homer, Iliad (Monro/Allen 1908–1920 edition)",
         "data/laboratory_sources/tlg0012.tlg001.perseus-grc2.xml")):
        path = root / relative
        xml = path.suffix == ".xml"
        raw = tei_body(path) if xml else path.read_text()
        prepared = greek_encode(raw) if language == "ancient-greek" else normalize(raw)
        metadata = json.loads(Path(str(path) + ".source.json").read_text()) if xml else {}
        result.append(Corpus(name, language, work, path, raw, prepared,
            "greek-fold-sigma-storage-alphabet-v1" if language == "ancient-greek" else
            "ascii-fold-ae-oe-preserve-ij-uv-v1", metadata.get("url")))
    return result
