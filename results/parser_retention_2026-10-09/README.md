# All-survivor synthetic parser calibration

The correct parser is retained AND blindly selected in 8/8 cases. Plaintext recovery improves to 28.5–75.0%, but remains below the frozen 90% gate in every case. This repairs a pruning failure without certifying the substitution-key solver. No new manuscript key search occurred.

| Case | Earlier nonspace accuracy | New nonspace accuracy | Oracle loss | Returned loss |
| --- | --- | --- | --- | --- |
| italian-encoded-19 | 12.5% | 75.0% | 3.089 | 3.538 |
| italian-encoded-7 | 25.4% | 29.6% | 3.389 | 4.026 |
| italian-preserve-19 | 5.7% | 73.6% | 3.634 | 3.983 |
| italian-preserve-7 | 16.1% | 66.1% | 3.786 | 4.387 |
| latin-encoded-19 | 16.6% | 68.5% | 3.438 | 3.960 |
| latin-encoded-7 | 14.2% | 39.1% | 3.486 | 4.355 |
| latin-preserve-19 | 9.3% | 69.9% | 3.806 | 4.315 |
| latin-preserve-7 | 13.9% | 28.5% | 3.634 | 4.565 |

177 policies, 32 reused searches, 145 new searches; 593,920 new evaluations and 724,992 represented evaluations. Beam width eight and 4,096 evaluations per policy unchanged. Keys were hidden during search; truth is used only in post-selection diagnostics. Eight cases are two texts × two spacing arms × two seeds, not eight independent sources.

[Verification record](verification.json)

[Full operating report](../unit_association_2026-10-09/report.html)

[Protocol](../../docs/protocols/PARSER_RETENTION_2026-10-09.md)

Producing module: voynich.laboratory.parser_retention. Verification: voynich.laboratory.parser_retention_verify. Reruns require PostgreSQL, the retained historical prior run IDs and a new output directory. Existing historical searches must not be overwritten. New specifications and all retained policy candidates are included here; large attempt archives remain under ignored results/runs/.
