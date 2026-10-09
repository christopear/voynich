"""Documented topic units for the page-association study; no network on import."""
from __future__ import annotations

import gzip
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

from voynich.decipher_search.core import normalize
from voynich.paths import ROOT

SOURCE = ROOT / 'data/unit_association_sources'


def render_xml(node):
    tag = node.tag.rsplit('}', 1)[-1]
    if tag in {'note', 'head', 'bibl', 'speaker'}:
        return ''
    if tag in {'gap', 'foreign'}:
        return ' '
    if tag in {'app', 'choice'}:
        raise NotImplementedError(f'Unresolved editorial alternative: {tag}')
    value = node.text or ''
    for child in node:
        value += render_xml(child) + (child.tail or '')
    return value + (' ' if tag in {'div', 'p', 'l', 'lb'} else '')


def medical_chapters(raw, books):
    tree = ET.fromstring(raw)
    result = []
    for book in tree.iter():
        if book.get('subtype') != 'book' or book.get('n') not in books:
            continue
        for chapter in book.iter():
            if chapter.get('subtype') == 'chapter':
                result.append({'id': f"book-{book.get('n')}-chapter-{chapter.get('n')}",
                               'words': normalize(render_xml(chapter)).split()})
    return result


class RecipeParagraphs(HTMLParser):
    """Keep body paragraphs, excluding centred headings and inline page/note markers."""
    def __init__(self):
        super().__init__()
        self.stack = []
        self.parts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        blocked = bool(self.stack and self.stack[-1][1]) or bool(
            set(attrs.get('class', '').split()) & {'center', 'pagenum', 'fnanchor'})
        if tag not in {'br', 'hr', 'img', 'meta', 'link', 'input'}:
            self.stack.append((tag, blocked))
        if tag in {'p', 'br'}:
            self.parts.append(' ')

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break
        if tag == 'p':
            self.parts.append(' ')

    def handle_data(self, data):
        if any(tag == 'p' for tag, _ in self.stack) and not self.stack[-1][1]:
            self.parts.append(data)


def recipe_chapters(raw):
    # Markers occur once each. Exclude the long editorial introduction and notes.
    start = raw.index('<h2 class="break"><a name="IL"')
    end = raw.index('<h2><a name="ANNOTAZIONI"', start)
    parts = re.split(r'<h3\b[^>]*>.*?</h3>', raw[start:end], flags=re.S)
    result = []
    for index, part in enumerate(parts[1:], 1):
        parser = RecipeParagraphs()
        parser.feed(part)
        result.append({'id': f'recipe-heading-{index}',
                       'words': normalize(''.join(parser.parts)).split()})
    return result


def sources():
    result = {}
    for name, books in [('celsus', set(map(str, range(1, 9)))),
                        ('pliny', set(map(str, range(20, 28))))]:
        path = SOURCE / f'{name}.xml.gz'
        raw = gzip.decompress(path.read_bytes())
        metadata = json.loads((SOURCE / f'{name}.source.json').read_text())
        assert hashlib.sha256(raw).hexdigest() == metadata['upstream_sha256']
        result[name] = medical_chapters(raw, books)
    raw = (SOURCE / 'cucina.html').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == json.loads(
        (SOURCE / 'cucina.source.json').read_text())['sha256']
    result['cucina'] = recipe_chapters(raw.decode('utf-8-sig'))
    for name, filename in [('alfonsi', 'latin_alfonsi.txt'), ('dante', 'italian_dante.txt')]:
        words = normalize((ROOT / 'data' / filename).read_text()).split()
        # Artificial 256-word blocks: no claim these are natural topic divisions.
        result[name] = [{'id': f'block-{start // 256}', 'words': words[start:start + 256]}
                        for start in range(0, len(words) - 255, 256)]
    return result


if __name__ == '__main__':
    for name, chapters in sources().items():
        eligible = [c for c in chapters if len(c['words']) >= 64]
        print(name, len(chapters), 'units;', len(eligible), 'with >=64 words')
