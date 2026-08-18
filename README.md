# Monitor bioRxiv for Codex

`monitor-biorxiv` is a portable Codex skill for finding and triaging recent biology preprints. It searches **bioRxiv by default** and can filter by keywords, authors, titles, and posting dates.

## Default curation

The default feed is curated for **computational-biology and bioinformatics method papers** on bioRxiv, not for biology papers that merely use a model or sequencing assay. It prioritizes:

- algorithms, data structures, compression, graph/tree methods, and combinatorics;
- computational or statistical method development, including feature selection and dimensionality reduction;
- scalable software, data systems, structural-similarity search, molecular retrieval, and genomics indexing;
- reusable bioinformatics pipelines, regenerable reference databases, and spatial-omics methods;
- harmonization or preprocessing benchmarks when they provide broadly reusable guidance.

Named-method titles such as `ToolName: method description` are a positive signal when the title or abstract establishes a real computational tool or method. The skill ranks incidental ML, simulations, clinical prediction, one-off datasets, and wet-lab workflows without reusable analysis infrastructure lower or excludes them.

This default is intentionally tunable. Ask for keyword, author, title, organism, disease, or method filters; request an unfiltered feed; identify unwanted topics; or ask to include another source. bioRxiv remains the default source, and arXiv is searched only when explicitly requested.

For a dated daily digest, the skill first enumerates every paper **first posted as v1** on that exact date; preferences rank that complete set rather than silently restricting the source collection. It reports later versions only for papers you explicitly open or ask to follow, in a separate `Updates to followed papers` section.

## Install

Copy the `monitor-biorxiv` folder into your local Codex skills directory:

```bash
mkdir -p ~/.codex/skills
cp -R monitor-biorxiv ~/.codex/skills/
```

Restart or start a new Codex task if the skill is not immediately listed. You can also keep the folder inside a project and ask Codex to read `monitor-biorxiv/SKILL.md` before use.

## Use

In Codex, ask for the skill by name:

```text
$monitor-biorxiv
$monitor-biorxiv find papers from this week on RNA biology in cancer
$monitor-biorxiv find papers by Jane Doe from the last month
$monitor-biorxiv find papers today with an unfiltered feed
$monitor-biorxiv find papers this week on spatial omics databases
$monitor-biorxiv find papers by Jane Doe and exclude clinical prediction
```

On first use, the skill returns a scan of papers first posted today and asks whether you want a daily Codex-task notification and whether to use the default filter or an unfiltered feed. Preferences remain in the active task unless you explicitly ask to document them in the skill.

## What is included

- `SKILL.md` — the Codex workflow and reporting rules.
- `agents/openai.yaml` — skill metadata for Codex.
- `scripts/search_biorxiv.py` — an optional standard-library Python search helper that queries Europe PMC's bioRxiv index.

The Python helper has no third-party dependencies. It needs Python 3 and internet access. For complete daily digests, the skill first uses bioRxiv's native daily feed. If that feed returns an invalid or empty response, it falls back to bioRxiv's website; it never treats such a failure as a zero-paper day.

## Daily digests

The skill can ask Codex to create a daily task notification after you confirm the schedule, timezone, filter profile, and whether only new papers should be included. Automations are configured locally in each user's Codex account; they are not shared by cloning this repository.

## Scope and limitations

This is a discovery aid, not a systematic review. Add topic synonyms, gene/protein aliases, author variants, organisms, and exclusions to reduce missed or irrelevant results. The computational-biology grouping is a metadata-based heuristic rather than an official bioRxiv category.
