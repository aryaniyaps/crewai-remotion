"""Brandable .com domain finder using Porkbun API."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from rich.console import Console
from rich.table import Table

from .analyzers import DomainAnalysis, analyze_sld
from .generator import generate_candidates
from .porkbun_client import DomainCheckResult, MarketplaceListing, PorkbunClient

console = Console()


@dataclass(frozen=True)
class RankedDomain:
    domain: str
    sld: str
    price_usd: float
    source: str
    available: bool
    premium: bool
    brand_score: float
    seo_score: float
    total_score: float
    brand_notes: list[str]
    seo_notes: list[str]
    syllables: int
    acquisition: str


def _load_credentials() -> tuple[str, str]:
    api_key = os.getenv("PORKBUN_API_KEY", "").strip()
    secret_key = os.getenv("PORKBUN_SECRET_KEY", "").strip()
    if not api_key or not secret_key:
        raise SystemExit(
            "Missing Porkbun credentials. Set PORKBUN_API_KEY and PORKBUN_SECRET_KEY "
            "in your environment or .env file."
        )
    return api_key, secret_key


def _analysis_to_ranked(
    analysis: DomainAnalysis,
    *,
    domain: str,
    price_usd: float,
    source: str,
    available: bool,
    premium: bool,
) -> RankedDomain:
    return RankedDomain(
        domain=domain,
        sld=analysis.sld,
        price_usd=price_usd,
        source=source,
        available=available,
        premium=premium,
        brand_score=analysis.brand_score,
        seo_score=analysis.seo_score,
        total_score=analysis.total_score,
        brand_notes=analysis.brand_notes,
        seo_notes=analysis.seo_notes,
        syllables=analysis.syllables,
        acquisition=analysis.acquisition,
    )


def scan_marketplace(
    client: PorkbunClient,
    *,
    max_price: float,
    min_len: int,
    max_len: int,
    queries: list[str],
) -> list[RankedDomain]:
    seen: set[str] = set()
    ranked: list[RankedDomain] = []

    search_specs: list[dict] = [{"query": None}]
    search_specs.extend({"query": q} for q in queries)

    for spec in search_specs:
        listings = client.list_marketplace(
            tlds=["com"],
            query=spec["query"],
            sld_length_min=min_len,
            sld_length_max=max_len,
            sort_name="price",
            sort_direction="asc",
        )
        for listing in listings:
            if listing.domain in seen:
                continue
            seen.add(listing.domain)
            if listing.price_usd > max_price:
                continue
            analysis = analyze_sld(
                listing.sld,
                price_usd=listing.price_usd,
                source="marketplace",
            )
            if analysis is None or analysis.total_score < 55:
                continue
            ranked.append(
                _analysis_to_ranked(
                    analysis,
                    domain=listing.domain,
                    price_usd=listing.price_usd,
                    source="marketplace",
                    available=True,
                    premium=False,
                )
            )

    ranked.sort(key=lambda item: item.total_score, reverse=True)
    return ranked


def scan_registrations(
    client: PorkbunClient,
    *,
    candidates: list[str],
    max_checks: int,
    max_price: float,
    registration_price: float,
) -> list[RankedDomain]:
    ranked: list[RankedDomain] = []
    checks = 0

    for sld in candidates:
        if checks >= max_checks:
            break
        domain = f"{sld}.com"
        try:
            result: DomainCheckResult = client.check_domain(domain)
        except RuntimeError as exc:
            message = str(exc).lower()
            if "rate" in message or "limit" in message or "seconds" in message:
                console.print(f"[yellow]Rate limited on {domain}; waiting 12s and retrying once…[/yellow]")
                time.sleep(12)
                try:
                    result = client.check_domain(domain)
                except RuntimeError as retry_exc:
                    console.print(f"[yellow]Skipping {domain}: {retry_exc}[/yellow]")
                    continue
            else:
                console.print(f"[yellow]Skipping {domain}: {exc}[/yellow]")
                continue
        checks += 1

        if not result.available or result.premium:
            continue
        price = result.price_usd if result.price_usd is not None else registration_price
        if price > max_price:
            continue

        analysis = analyze_sld(
            sld,
            price_usd=price,
            source="registration",
            premium=result.premium,
        )
        if analysis is None or analysis.total_score < 60:
            continue

        ranked.append(
            _analysis_to_ranked(
                analysis,
                domain=domain,
                price_usd=price,
                source="registration",
                available=True,
                premium=result.premium,
            )
        )
        console.print(
            f"[green]Available[/green] {domain} ${price:.2f} "
            f"(brand={analysis.brand_score:.0f}, seo={analysis.seo_score:.0f}, total={analysis.total_score:.1f})"
        )

    ranked.sort(key=lambda item: item.total_score, reverse=True)
    return ranked


def render_report(items: list[RankedDomain], *, top_n: int) -> None:
    if not items:
        console.print("[red]No domains matched your budget and quality bar.[/red]")
        console.print(
            "Try increasing --max-checks, widening --max-len, or raising --min-score slightly."
        )
        return

    table = Table(title=f"Top {min(top_n, len(items))} brandable .com domains (≤ budget)")
    table.add_column("#", justify="right")
    table.add_column("Domain")
    table.add_column("Price", justify="right")
    table.add_column("Source")
    table.add_column("Brand", justify="right")
    table.add_column("SEO", justify="right")
    table.add_column("Total", justify="right")

    for idx, item in enumerate(items[:top_n], start=1):
        table.add_row(
            str(idx),
            item.domain,
            f"${item.price_usd:.2f}",
            item.source,
            f"{item.brand_score:.0f}",
            f"{item.seo_score:.0f}",
            f"{item.total_score:.1f}",
        )
    console.print(table)

    best = items[0]
    console.print("\n[bold]Recommended pick[/bold]")
    console.print(f"  Domain: [cyan]{best.domain}[/cyan]")
    console.print(f"  Price: ${best.price_usd:.2f} via {best.acquisition}")
    console.print(f"  Scores: brand {best.brand_score:.0f} | SEO {best.seo_score:.0f} | total {best.total_score:.1f}")
    console.print("  Brand notes:")
    for note in best.brand_notes:
        console.print(f"    - {note}")
    console.print("  SEO notes:")
    for note in best.seo_notes:
        console.print(f"    - {note}")

    console.print("\n[bold]Detailed shortlist[/bold]")
    for idx, item in enumerate(items[:top_n], start=1):
        console.print(
            f"\n{idx}. [cyan]{item.domain}[/cyan] — ${item.price_usd:.2f} ({item.source}) "
            f"| brand {item.brand_score:.0f}, seo {item.seo_score:.0f}, total {item.total_score:.1f}"
        )
        console.print(f"   Acquisition: {item.acquisition}")


def save_report(items: list[RankedDomain], output_path: Path) -> None:
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "count": len(items),
        "domains": [asdict(item) for item in items],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Find short, brandable .com domains for a tech parent company using Porkbun. "
            "Scans marketplace listings and checks generated registration candidates."
        )
    )
    parser.add_argument("--budget", type=float, default=20.0, help="Max price in USD (default: 20)")
    parser.add_argument("--min-len", type=int, default=4, help="Minimum SLD length")
    parser.add_argument("--max-len", type=int, default=6, help="Maximum SLD length")
    parser.add_argument("--max-checks", type=int, default=30, help="Registration availability checks (10s each)")
    parser.add_argument("--candidate-pool", type=int, default=600, help="Generated names to rank before checking")
    parser.add_argument("--top", type=int, default=10, help="How many domains to print")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/domain_finder/report.json"),
        help="JSON report path",
    )
    parser.add_argument(
        "--skip-registration-scan",
        action="store_true",
        help="Only analyze Porkbun marketplace listings",
    )
    parser.add_argument(
        "--skip-marketplace-scan",
        action="store_true",
        help="Only check generated registration candidates",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for candidate generation")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    args = build_parser().parse_args(argv)
    api_key, secret_key = _load_credentials()
    client = PorkbunClient(api_key, secret_key)

    console.print("[bold]Porkbun brandable domain finder[/bold]")
    console.print(
        f"Budget: ${args.budget:.2f} | Length: {args.min_len}-{args.max_len} | .com only"
    )
    console.print("Filters: public-friendly pronunciation, no double letters (e.g. tt, ll, gg)\n")

    try:
        ping = client.ping()
        console.print(f"API connected (IP: {ping.get('yourIp', 'unknown')})")
        reg_price = client.get_com_registration_price()
        console.print(f".com registration baseline: ${reg_price:.2f}\n")
    except Exception as exc:
        console.print(f"[red]Porkbun API error:[/red] {exc}")
        return 1

    marketplace_queries = ["+va", "+ex", "+on", "+um", "+ly", "+ra", "+en", "+zo", "+neo", "+lum"]
    all_ranked: list[RankedDomain] = []

    if not args.skip_marketplace_scan:
        console.print("[bold]Phase 1:[/bold] Scanning Porkbun marketplace listings…")
        marketplace_hits = scan_marketplace(
            client,
            max_price=args.budget,
            min_len=args.min_len,
            max_len=args.max_len,
            queries=marketplace_queries,
        )
        console.print(f"  Found {len(marketplace_hits)} curated marketplace candidates\n")
        all_ranked.extend(marketplace_hits)

    if not args.skip_registration_scan:
        console.print("[bold]Phase 2:[/bold] Checking generated registration candidates…")
        console.print(
            f"  Porkbun allows ~1 availability check / 10s — checking up to {args.max_checks} names "
            f"(~{int(args.max_checks * 10.5 / 60)} min).\n"
        )
        candidates = generate_candidates(
            count=args.candidate_pool,
            min_len=args.min_len,
            max_len=args.max_len,
            seed=args.seed,
        )
        pre_scored: list[tuple[float, str]] = []
        for sld in candidates:
            analysis = analyze_sld(
                sld,
                price_usd=reg_price,
                source="registration",
            )
            if analysis is not None:
                pre_scored.append((analysis.total_score, sld))
        pre_scored.sort(reverse=True)
        prioritized = [sld for _, sld in pre_scored] or candidates

        registration_hits = scan_registrations(
            client,
            candidates=prioritized,
            max_checks=args.max_checks,
            max_price=args.budget,
            registration_price=reg_price,
        )
        console.print(f"\n  Found {len(registration_hits)} available registration candidates\n")
        all_ranked.extend(registration_hits)

    all_ranked.sort(key=lambda item: item.total_score, reverse=True)

    # De-duplicate by domain keeping best score.
    deduped: dict[str, RankedDomain] = {}
    for item in all_ranked:
        existing = deduped.get(item.domain)
        if existing is None or item.total_score > existing.total_score:
            deduped[item.domain] = item
    final = sorted(deduped.values(), key=lambda item: item.total_score, reverse=True)

    render_report(final, top_n=args.top)
    save_report(final, args.output)
    console.print(f"\nSaved JSON report to [cyan]{args.output}[/cyan]")
    console.print(
        "\n[dim]Note: Porkbun marketplace uses fixed-price listings, not incremental auctions. "
        "For $20 you mostly get marketplace/reseller inventory; fresh registrations are ~$11.08 "
        "but short brandable names are rarely available.[/dim]"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
