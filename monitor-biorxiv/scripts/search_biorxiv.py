#!/usr/bin/env python3
"""Search recent bioRxiv preprints indexed by Europe PMC."""

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


API = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
BIONATIVE_API = "https://api.biorxiv.org/details/biorxiv"
COMPUTATIONAL_SIGNALS = (
    "bioinformatics", "computational biology", "computational method", "in silico",
    "machine learning", "deep learning", "artificial intelligence", "algorithm",
    "software tool", "software package", "web server", "database resource",
    "pipeline", "workflow", "retrieval", "indexing", "orthogroup", "synteny",
    "phylogenetic", "genome duplication", "spatial omics", "spatial transcriptomics",
    "feature selection", "highly variable gene", "gene selection", "data harmonization",
    "analytical database", "embedded database", "reference database", "reference resource",
    "regenerable", "benchmarking", "preprocessing", "similarity search", "ligand binding",
    "molecular retrieval", "graph vae",
)
TITLE_COMPUTATIONAL_SIGNALS = (
    "machine learning", "deep learning", "computational", "algorithm", "simulation",
    "inference", "bioinformatic", "in silico", "software", "database", "pipeline",
    "workflow", "retrieval", "indexing", "orthogroup", "synteny", "genome duplication",
    "graph pca", "graph integration", "phylogenetic tree", "genome-scale",
    "feature selection", "highly variable gene", "gene selection", "data harmonization",
    "analytical database", "embedded analytical", "reference database", "regenerable",
    "similarity search", "ligand binding-site", "graph vae", "scalable",
)
METHOD_TITLE_SIGNALS = (
    "algorithm", "pipeline", "workflow", "tool", "software", "retrieval", "indexing",
    "orthogroup", "synteny", "genome duplication", "graph pca", "graph integration",
    "phylogenetic tree", "data structure", "compression", "scalable", "fast ",
    "feature selection", "highly variable gene", "data harmonization", "analytical database",
    "reference database", "regenerable", "similarity search", "ligand binding-site", "graph vae",
)
NAMED_METHOD_TERMS = (
    "algorithm", "method", "tool", "software", "pipeline", "workflow", "database",
    "reference", "retrieval", "search", "scalable", "selection", "harmonization",
    "benchmark", "graph", "latent space",
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


def fetch_native_biorxiv(start, end, maximum=None):
    """Retrieve all versions from bioRxiv's native daily feed."""
    records = []
    cursor = 0
    try:
        while True:
            with urlopen(f"{BIONATIVE_API}/{start}/{end}/{cursor}", timeout=30) as response:
                payload = json.load(response)
            page = payload.get("collection", [])
            records.extend(page)
            if maximum is not None and len(records) >= maximum:
                return records[:maximum]
            messages = payload.get("messages", [])
            total = int(messages[0].get("total", 0)) if messages else 0
            cursor += len(page)
            if not page or cursor >= total:
                return records
    except Exception as error:
        raise RuntimeError(f"bioRxiv API request failed: {error}") from error


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


def as_native_paper(record):
    doi = record.get("doi", "")
    return {
        "key": doi,
        "title": " ".join(record.get("title", "Untitled").split()),
        "authors": record.get("authors", "Authors unavailable"),
        "date": record.get("date", "Date unavailable"),
        "doi": doi,
        "url": f"https://www.biorxiv.org/content/{doi}" if doi else "",
        "abstract": " ".join(record.get("abstract", "").split()),
        "version": str(record.get("version", "")),
    }


def normalize_doi(value):
    """Accept a DOI or a bioRxiv content URL for a followed paper."""
    value = value.strip().lower()
    for prefix in ("https://www.biorxiv.org/content/", "http://www.biorxiv.org/content/", "https://doi.org/"):
        if value.startswith(prefix):
            value = value[len(prefix):]
    value = value.removesuffix(".full-text").split("?")[0].split("#")[0]
    return re.sub(r"v\d+$", "", value)


def matches_filters(paper, args):
    title = paper["title"].lower()
    abstract = paper["abstract"].lower()
    haystack = f"{title} {abstract}"
    keyword_matches = [term.lower() in haystack for term in args.keyword]
    if args.keyword and not (any(keyword_matches) if args.any_keyword else all(keyword_matches)):
        return False
    author = paper["authors"].lower()
    if any(term.lower() not in author for term in args.author):
        return False
    if any(term.lower() not in title for term in args.title):
        return False
    return True


def is_computational_biology(paper):
    title = paper["title"].lower()
    abstract = paper["abstract"].lower()
    if any(signal in title for signal in TITLE_COMPUTATIONAL_SIGNALS):
        return True
    if re.match(r"^[a-z][a-z0-9_-]{2,}:\\s", title) and any(term in title or term in abstract for term in NAMED_METHOD_TERMS):
        return True
    if "prediction" in title and "open-source" in title:
        return True
    if "model" in title and any(cue in title for cue in ("sequence-to-function", "mathematical", "statistical", "computational")):
        return True
    # A lone incidental model, simulation, or clinical prediction is not enough.
    return any(signal in abstract for signal in COMPUTATIONAL_SIGNALS)


def method_score(paper):
    title = paper["title"].lower()
    abstract = paper["abstract"].lower()
    score = 3 * sum(signal in title for signal in METHOD_TITLE_SIGNALS)
    score += sum(signal in abstract for signal in COMPUTATIONAL_SIGNALS)
    if re.match(r"^[a-z][a-z0-9_-]{2,}:\\s", title) and any(term in title or term in abstract for term in NAMED_METHOD_TERMS):
        score += 2
    if any(signal in title for signal in ("clinical utility", "prediction of", "predicting ")):
        score -= 2
    return score


def report_set(papers):
    """Apply the user-facing overflow rule while retaining total-category counts."""
    computational = [paper for paper in papers if is_computational_biology(paper)]
    other_count = len(papers) - len(computational)
    if len(papers) <= 15:
        return papers, len(computational), other_count, 0
    selected = sorted(computational, key=lambda paper: (method_score(paper), paper["date"]), reverse=True)[:15]
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
    parser.add_argument("--native-biorxiv", action="store_true", help="Use bioRxiv's native daily feed; ideal for complete daily digests")
    parser.add_argument("--follow-doi", action="append", default=[], help="On a native daily scan, report a new version of this followed DOI; repeatable")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown")
    args = parser.parse_args()
    if args.days < 1 or (args.max is not None and args.max < 1):
        parser.error("--days and --max must be positive")
    if bool(args.start_date) != bool(args.end_date):
        parser.error("Use --start-date and --end-date together")
    if not (args.keyword or args.author or args.title or args.all_biorxiv or args.native_biorxiv):
        parser.error("Specify a filter or use --all-biorxiv")

    if args.start_date:
        start, end = args.start_date, args.end_date
        if start > end:
            parser.error("--start-date must be on or before --end-date")
    else:
        end = dt.date.today()
        start = end - dt.timedelta(days=args.days - 1)
    query = "bioRxiv native daily feed" if args.native_biorxiv else make_query(args, start, end)
    followed_updates = []
    if args.native_biorxiv:
        native_records = [as_native_paper(record) for record in fetch_native_biorxiv(start, end, args.max)]
        # Daily corpus: all papers first posted as v1 on the requested date.
        # Revisions are never mixed into this new-paper list.
        records = [paper for paper in native_records if paper["version"] == "1" and matches_filters(paper, args)]
        followed_dois = {normalize_doi(value) for value in args.follow_doi}
        followed_updates = [
            paper for paper in native_records
            if paper["version"] != "1" and normalize_doi(paper["doi"]) in followed_dois
        ]
    else:
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
            "followed_paper_updates": followed_updates,
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
    if followed_updates:
        print("# Updates to followed papers\n")
        for paper in followed_updates:
            print(f"## {paper['title']} (v{paper['version']})\n")
            print(f"{paper['authors']}  \nUpdated: {paper['date']}  \n{paper['url']}\n")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
