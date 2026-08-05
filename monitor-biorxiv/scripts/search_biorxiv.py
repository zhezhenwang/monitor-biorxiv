#!/usr/bin/env python3
"""Search recent bioRxiv preprints indexed by Europe PMC."""

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


API = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
COMPUTATIONAL_SIGNALS = (
    "bioinformatics", "computational biology", "computational method", "in silico",
    "machine learning", "deep learning", "artificial intelligence", "algorithm",
    "software tool", "software package", "web server", "database resource",
)
TITLE_COMPUTATIONAL_SIGNALS = (
    "machine learning", "deep learning", "computational", "algorithm", "simulation",
    "inference", "bioinformatic", "in silico", "software", "database", "pipeline",
)


def quote(value):
    return '"' + value.replace('"', '\\"') + '"'


def make_query(args, start, end):
    parts = [
        'SRC:PPR',
        'PUBLISHER:"bioRxiv"',
        f'FIRST_PDATE:[{start.isoformat()} TO {end.isoformat()}]',
    ]
    keyword_clauses = [f'(TITLE:{quote(term)} OR ABSTRACT:{quote(term)})' for term in args.keyword]
    if args.any_keyword and keyword_clauses:
        parts.append("(" + " OR ".join(keyword_clauses) + ")")
    else:
        parts.extend(keyword_clauses)
    for author in args.author:
        parts.append(f'AUTH:{quote(author)}')
    for title in args.title:
        parts.append(f'TITLE:{quote(title)}')
    return " AND ".join(parts)


def fetch(query, maximum=None):
    """Retrieve every results page unless the caller explicitly sets a cap."""
    records = []
    cursor = "*"
    try:
        while True:
            params = urlencode({
                "query": query + " sort_date:y",
                "format": "json",
                "resultType": "core",
                "pageSize": 1000,
                "cursorMark": cursor,
            })
            with urlopen(f"{API}?{params}", timeout=30) as response:
                payload = json.load(response)
            page = payload.get("resultList", {}).get("result", [])
            records.extend(page)
            if maximum is not None and len(records) >= maximum:
                return records[:maximum]
            next_cursor = payload.get("nextCursorMark")
            if not page or not next_cursor or next_cursor == cursor:
                return records
            cursor = next_cursor
    except Exception as error:
        raise RuntimeError(f"Europe PMC request failed: {error}") from error


def paper_key(record):
    return record.get("doi") or record.get("pmid") or record.get("id")


def link(record):
    doi = record.get("doi", "")
    if doi:
        return f"https://www.biorxiv.org/content/{doi}"
    return record.get("fullTextUrlList", {}).get("fullTextUrl", [{}])[0].get("url", "")


def as_paper(record):
    return {
        "key": paper_key(record),
        "title": " ".join(record.get("title", "Untitled").split()),
        "authors": record.get("authorString", "Authors unavailable"),
        "date": record.get("firstPublicationDate") or record.get("firstIndexDate", "Date unavailable"),
        "doi": record.get("doi", ""),
        "url": link(record),
        "abstract": " ".join(record.get("abstractText", "").split()),
    }


def is_computational_biology(paper):
    title = paper["title"].lower()
    abstract = paper["abstract"].lower()
    if any(signal in title for signal in TITLE_COMPUTATIONAL_SIGNALS):
        return True
    if "prediction" in title and "open-source" in title:
        return True
    if "model" in title and any(cue in title for cue in ("sequence-to-function", "mathematical", "statistical", "computational")):
        return True
    # A lone incidental model, simulation, or clinical prediction is not enough.
    return any(signal in abstract for signal in COMPUTATIONAL_SIGNALS)


def report_set(papers):
    """Apply the user-facing overflow rule while retaining total-category counts."""
    computational = [paper for paper in papers if is_computational_biology(paper)]
    other_count = len(papers) - len(computational)
    if len(papers) <= 15:
        return papers, len(computational), other_count, 0
    selected = sorted(computational, key=lambda paper: paper["date"], reverse=True)[:15]
    return selected, len(computational), other_count, len(computational) - len(selected)


def load_seen(path):
    if not path or not path.exists():
        return set()
    try:
        return set(json.loads(path.read_text()).get("seen", []))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Cannot read state file {path}: {error}") from error


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keyword", action="append", default=[], help="Search title or abstract; repeatable")
    parser.add_argument("--any-keyword", action="store_true", help="Match any --keyword instead of requiring all")
    parser.add_argument("--author", action="append", default=[], help="Search author; repeatable")
    parser.add_argument("--title", action="append", default=[], help="Search title; repeatable")
    parser.add_argument("--days", type=int, default=7, help="Lookback window (default: 7)")
    parser.add_argument("--start-date", type=dt.date.fromisoformat, help="Inclusive YYYY-MM-DD start date")
    parser.add_argument("--end-date", type=dt.date.fromisoformat, help="Inclusive YYYY-MM-DD end date")
    parser.add_argument("--max", type=int, help="Optional cap on records; omit to retrieve every match")
    parser.add_argument("--state", type=Path, help="JSON file storing already-reported records")
    parser.add_argument("--all", action="store_true", help="Include records already in the state file")
    parser.add_argument("--all-biorxiv", action="store_true", help="Browse all recent bioRxiv records without a text filter")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown")
    args = parser.parse_args()
    if args.days < 1 or (args.max is not None and args.max < 1):
        parser.error("--days and --max must be positive")
    if bool(args.start_date) != bool(args.end_date):
        parser.error("Use --start-date and --end-date together")
    if not (args.keyword or args.author or args.title or args.all_biorxiv):
        parser.error("Specify a filter or use --all-biorxiv")

    if args.start_date:
        start, end = args.start_date, args.end_date
        if start > end:
            parser.error("--start-date must be on or before --end-date")
    else:
        end = dt.date.today()
        start = end - dt.timedelta(days=args.days - 1)
    query = make_query(args, start, end)
    records = [as_paper(record) for record in fetch(query, args.max)]
    seen = load_seen(args.state)
    papers = records if args.all else [paper for paper in records if paper["key"] not in seen]
    displayed, computational_count, other_count, hidden_computational_count = report_set(papers)

    if args.state:
        updated = sorted(seen | {paper["key"] for paper in records if paper["key"]})
        args.state.write_text(json.dumps({"seen": updated}, indent=2) + "\n")

    if args.json:
        print(json.dumps({
            "start": str(start), "end": str(end), "query": query,
            "count": len(papers), "computational_biology_count": computational_count,
            "other_biology_count": other_count,
            "hidden_computational_biology_count": hidden_computational_count,
            "papers": displayed,
        }, indent=2))
        return
    print(f"# bioRxiv results: {start} to {end} ({len(papers)} records)\n")
    print(f"Filters: {query}\n")
    if len(papers) > 15:
        print("Overflow rule: showing up to 15 metadata-classified computational-biology papers, newest first.  ")
        print(f"Computational biology: {computational_count}; other biology: {other_count}; additional computational-biology papers not shown: {hidden_computational_count}.\n")
    if not displayed:
        print("No matching new records.")
        return
    for paper in displayed:
        print(f"## {paper['title']}\n")
        print(f"{paper['authors']}  \nPosted: {paper['date']}  \n{paper['url']}\n")
        if paper["abstract"]:
            print(f"{paper['abstract'][:500]}{'…' if len(paper['abstract']) > 500 else ''}\n")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
