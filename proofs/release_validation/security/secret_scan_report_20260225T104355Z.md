# Secret Scan Report

- generated_utc: 2026-02-25T10:43:55Z
- boundary: /Users/Zer0pa/ZPE/ZPE-IMC/release_staging/imc_repo_01_20260223T123035Z
- tool: rg (ripgrep)
- command: `rg -n --hidden -S --follow --glob '!proofs/release_validation/security/**' -e 'AKIA[0-9A-Z]{16}' -e 'ASIA[0-9A-Z]{16}' -e 'ghp_[A-Za-z0-9]{36}' -e 'github_pat_[A-Za-z0-9_]{82}' -e '-----BEGIN (RSA|OPENSSH|EC|DSA|PGP) PRIVATE KEY-----' -e 'xox[baprs]-[A-Za-z0-9-]{10,}' -e 'AIza[0-9A-Za-z_-]{35}' -e '(?i)aws(.{0,20})?(secret|access).{0,5}[=:].{0,5}[A-Za-z0-9/+=]{40}' '/Users/Zer0pa/ZPE/ZPE-IMC/release_staging/imc_repo_01_20260223T123035Z'`
- result: PASS

No high-signal secret patterns matched.
