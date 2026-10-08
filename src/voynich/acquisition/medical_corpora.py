"""Explicit download/extraction of pinned Latin medical calibration texts."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import requests
from voynich.paths import ROOT

COMMIT = '128a05afa9cc7179ab18f8d05f78a9f1dd50e415'
SOURCES = {
    'celsus': ('phi0836', 'phi002', 'perseus-lat4', tuple(str(n) for n in range(1,9)),
               'Celsus, De Medicina; W. G. Spencer edition, 1935–1938'),
    'pliny': ('phi0978', 'phi001', 'perseus-lat2', tuple(str(n) for n in range(20,28)),
              'Pliny, Naturalis Historia 20–27; Mayhoff edition, 1906'),
}


def extract_books(raw, books):
    tree = ET.fromstring(raw)
    selected = [e for e in tree.iter() if e.get('subtype') == 'book' and e.get('n') in books]
    if [e.get('n') for e in selected] != list(books):
        raise ValueError('missing, duplicated or reordered source books')
    def render(node):
        tag = node.tag.rsplit('}',1)[-1]
        if tag in {'note','head','bibl','speaker'}:
            return ''
        if tag in {'gap','foreign'}:
            return ' '
        if tag in {'app','choice'}:
            raise NotImplementedError('editorial alternatives require explicit selection')
        text = node.text or ''
        for child in node:
            text += render(child) + (child.tail or '')
        return text + (' ' if tag in {'div','p','l','lb'} else '')
    return '\n\n'.join(' '.join(render(book).split()) for book in selected)


def fetch(output):
    output.mkdir(parents=True,exist_ok=True)
    for name,(author,work,edition,books,title) in SOURCES.items():
        url=f'https://raw.githubusercontent.com/PerseusDL/canonical-latinLit/{COMMIT}/data/{author}/{work}/{author}.{work}.{edition}.xml'
        response=requests.get(url,timeout=90);response.raise_for_status()
        raw=response.content
        text=extract_books(raw,books)
        path=output/f'{name}_medical.txt'
        if path.exists():
            raise FileExistsError(path)
        path.write_text(text+'\n')
        metadata={'id':name,'work':title,'url':url,'commit':COMMIT,'books':books,
            'upstream_sha256':hashlib.sha256(raw).hexdigest(),
            'text_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'extraction':'medical-tei-books-v1: remove notes/headings; replace gaps and foreign-language spans with spaces; keep inline tails; collapse whitespace within books',
            'language':'latin','genre':'medical/herbal calibration; ancient, not medieval recipe transcription',
            'license':'CC BY-SA 4.0, repository license retained alongside sources',
            'attribution':'Perseus Digital Library / Trustees of Tufts University; edition editors named in work'}
        Path(str(path)+'.source.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
        print(name,len(text),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'data/laboratory_sources')
    fetch(p.parse_args().output)
