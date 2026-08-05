# Monitor bioRxiv for Codex

`monitor-biorxiv` is a portable Codex skill for finding and triaging recent biology preprints. It searches **bioRxiv by default** and can filter by keywords, authors, titles, and posting dates.

The default preference profile emphasizes method-centered work: algorithms, data structures, compression, graphs and trees, set systems, combinatorics, and computational tools. It does not add arXiv unless a user explicitly requests it.

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
```

On first use, the skill returns a scan of papers first posted today and asks whether you want a daily Codex-task notification and whether to use the default filter or an unfiltered feed. Preferences remain in the active task unless you explicitly ask to document them in the skill.

## What is included

- `SKILL.md` — the Codex workflow and reporting rules.
- `agents/openai.yaml` — skill metadata for Codex.
- `scripts/search_biorxiv.py` — an optional standard-library Python search helper that queries Europe PMC's bioRxiv index.

The Python helper has no third-party dependencies. It needs Python 3 and internet access. It retrieves bioRxiv records through Europe PMC; recently posted records can be delayed in third-party indexing, so an empty result is not proof that no preprints exist.

## Daily digests

The skill can ask Codex to create a daily task notification after you confirm the schedule, timezone, filter profile, and whether only new papers should be included. Automations are configured locally in each user's Codex account; they are not shared by cloning this repository.

## Scope and limitations

This is a discovery aid, not a systematic review. Add topic synonyms, gene/protein aliases, author variants, organisms, and exclusions to reduce missed or irrelevant results. The computational-biology grouping is a metadata-based heuristic rather than an official bioRxiv category.
