# Brandable .com domain finder

Scans **Porkbun marketplace** listings and checks **generated registration candidates** for short, brandable `.com` names within a budget.

## Setup

Add credentials to `.env` (never commit real keys):

```bash
PORKBUN_API_KEY=pk1_...
PORKBUN_SECRET_KEY=sk1_...
```

Create keys at https://porkbun.com/account/api

## Run

```bash
uv run python scripts/find_domains.py
```

Useful flags:

| Flag | Default | Purpose |
|------|---------|---------|
| `--budget` | 20 | Max USD |
| `--min-len` / `--max-len` | 4 / 6 | SLD length window |
| `--max-checks` | 30 | Registration lookups (~10s each) |
| `--skip-registration-scan` | off | Marketplace only (fast) |
| `--skip-marketplace-scan` | off | Registration only |
| `--output` | `output/domain_finder/report.json` | JSON report |

## Scoring

Each candidate gets:

- **Brand score** — length, public pronunciation (C/V alternation), friendly letters, syllables, negative fragments
- **Hard filter** — rejects any name with consecutive duplicate letters (`tt`, `gg`, `ll`, …)
- **SEO score** — `.com` trust, typing ease, price fit, clean SLD (no numbers/hyphens)
- **Total** — 55% brand + 45% SEO

## Limits

- Porkbun allows about **1 availability check per 10 seconds**.
- At **$20**, most short brandable names come from **marketplace buy-now listings**, not auctions (Porkbun API has no auction bidding endpoint).
- Fresh **.com registration is ~$11.08**, but 4–6 letter invented names are usually taken; use `--max-checks 100+` for better registration coverage (~17 min).
