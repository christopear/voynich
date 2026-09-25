from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

URLS = {
    "ZL3b-n.txt": "https://raw.githubusercontent.com/matthewdgreen/cipher_benchmark/main/benchmark/unsolved/sources/voynich/transcriptions/ZL3b-n.txt",
    "naibbe_cipher_pre.txt": "https://raw.githubusercontent.com/greshko/naibbe-cipher/main/encrypted/nathist_output_ciphertext.txt",
    "naibbe_cipher_respaced.txt": "https://raw.githubusercontent.com/greshko/naibbe-cipher/main/encrypted/nathist_output_ciphertext_respaced.txt",
    "naibbe_plain_units.txt": "https://raw.githubusercontent.com/greshko/naibbe-cipher/main/respaced_plaintext/nathist_pre_encryption_respaced_plaintext.txt",
    "naibbe_decrypted.txt": "https://raw.githubusercontent.com/greshko/naibbe-cipher/main/decrypted/nathist_output_ciphertext_decrypted.txt",
    "latin_alfonsi.txt": "https://raw.githubusercontent.com/cltk/lat_text_latin_library/master/alfonsi.disciplina.txt",
    "italian_dante.txt": "https://raw.githubusercontent.com/scstech85/DocEmul/master/divina.txt",
    "mhg_fh.txt": "https://raw.githubusercontent.com/Middle-High-German-Conceptual-Database/plain-txt-Texte/main/FH.txt",
}

for name, url in URLS.items():
    out = DATA / name
    print(f"Fetching {url}")
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    out.write_bytes(r.content)
    print(f"  -> {out} ({len(r.content):,} bytes)")
