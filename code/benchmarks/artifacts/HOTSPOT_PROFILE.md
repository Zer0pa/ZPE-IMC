# A4 Hotspot Profile

- Run ID: `A4-BENCH-20260307T230025Z`
- Timestamp (UTC): `2026-03-07T23:00:32Z`
- Profile source: `cProfile` self-time ranking
- Functions listed: `10`

| Rank | Function | Location | Self Time (s) | Wall-Time Share (%) |
|---:|---|---|---:|---:|
| 1 | _extend_checked | imc.py:734 | 0.127348 | 26.2814 |
| 2 | _detect_family_words | dual_dispatch.py:81 | 0.078082 | 16.1141 |
| 3 | _image_payload | dual_dispatch.py:69 | 0.054689 | 11.2863 |
| 4 | _word_fields | imc.py:131 | 0.042739 | 8.8203 |
| 5 | encode_quadtree_kernel | imc_native.py:136 | 0.032778 | 6.7647 |
| 6 | _is_image_payload | imc.py:127 | 0.028953 | 5.9751 |
| 7 | <built-in method builtins.isinstance> | ~:0 | 0.028879 | 5.9599 |
| 8 | <built-in method zpe_imc_kernel.zpe_imc_kernel.encode_quadtree> | ~:0 | 0.018703 | 3.8598 |
| 9 | <built-in method zpe_imc_kernel.zpe_imc_kernel.decode_quadtree> | ~:0 | 0.011001 | 2.2704 |
| 10 | <built-in method zpe_imc_kernel.zpe_imc_kernel.scan_stream> | ~:0 | 0.005813 | 1.1996 |
