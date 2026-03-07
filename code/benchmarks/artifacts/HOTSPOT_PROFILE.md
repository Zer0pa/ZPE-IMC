# A4 Hotspot Profile

- Run ID: `A4-BENCH-20260307T131414Z`
- Timestamp (UTC): `2026-03-07T13:14:21Z`
- Profile source: `cProfile` self-time ranking
- Functions listed: `10`

| Rank | Function | Location | Self Time (s) | Wall-Time Share (%) |
|---:|---|---|---:|---:|
| 1 | _extend_checked | imc.py:734 | 0.123152 | 27.3173 |
| 2 | _detect_family_words | dual_dispatch.py:81 | 0.070597 | 15.6597 |
| 3 | _image_payload | dual_dispatch.py:69 | 0.049971 | 11.0845 |
| 4 | _word_fields | imc.py:131 | 0.038544 | 8.5498 |
| 5 | encode_quadtree_kernel | imc_native.py:136 | 0.031441 | 6.9741 |
| 6 | <built-in method builtins.isinstance> | ~:0 | 0.027408 | 6.0796 |
| 7 | _is_image_payload | imc.py:127 | 0.027311 | 6.0581 |
| 8 | <built-in method zpe_imc_kernel.zpe_imc_kernel.encode_quadtree> | ~:0 | 0.017591 | 3.9021 |
| 9 | <built-in method zpe_imc_kernel.zpe_imc_kernel.decode_quadtree> | ~:0 | 0.010098 | 2.2399 |
| 10 | <built-in method zpe_imc_kernel.zpe_imc_kernel.scan_stream> | ~:0 | 0.005347 | 1.1861 |
