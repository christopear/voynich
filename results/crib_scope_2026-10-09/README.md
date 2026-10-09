# Crib-test scoping inventory

No decryption or semantic test. See the [scope document](../../docs/protocols/CRIB_SCOPE_2026-10-09.md).

`inventory.json`: 299 ZL3b zodiac Lz labels, 271 clean under the existing parser,
22 distinct complete clean labels recurring across panels. Includes metadata,
uncertain boundaries and exact loci. The producing command is:

```bash
uv run --locked python -m voynich.laboratory.crib_inventory --output results/<new-scope-dir>
```

Image/label alignment and semantic anchors remain to be verified before execution.
