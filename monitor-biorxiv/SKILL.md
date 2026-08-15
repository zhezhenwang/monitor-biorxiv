---
name: monitor-biorxiv
description: Search, triage, and track biology preprints on bioRxiv by keyword, author, or title, and search algorithmic research on arXiv only when explicitly requested. Adapt searches from a user's explicit preferences and feedback. Use when a scientist asks to find recent biology papers, make a daily or weekly preprint digest, infer a search profile from the current chat, monitor a research topic or author, or avoid missing relevant preprints.
---

# Monitor bioRxiv and algorithms

Use this skill to make a compact, reproducible preprint watchlist. Search **bioRxiv by default**. Add an arXiv algorithmic search only when the user explicitly requests arXiv, algorithms/theory, or non-biology papers. Do not add medRxiv, PubMed articles, or other sources unless the user explicitly asks.

## Build a search profile from this chat

Before searching, inspect the current task's conversation for the user's research subject, organism, biological system, methods, genes/proteins, disease or phenotype, collaborators/labs, and paper titles. Convert these into a concise proposed query profile and state any important assumption.

- Treat the active task's visible conversation as available context.
- Do not claim to see another task's, another user's, or deleted chat history. Ask the user to paste or name any context that is not present here.
- Let the user correct the profile, then retain those terms for later searches in this task.

## First-use setup

On the first invocation in a task, run an unfiltered bioRxiv scan for papers first posted **today** and present the complete result set under the normal overflow rule. Then ask these three short questions:

1. “Would you like a daily notification?”
2. “Use the default method/algorithm-centered filter, or an unfiltered feed? You can add keywords, authors, or titles. bioRxiv is the default source; arXiv is an optional source.”
3. “Should I keep these preferences only in this task, or document selected keywords/exclusions in `SKILL.md` for future uses?”

Do not wait for answers before returning the first daily scan. If the user does not specify a filter, use the default method/algorithm-centered filter: algorithms, data structures, compression, graph/tree methods, set systems, combinatorics, scalable bioinformatics tools, pipelines/workflows, genomic indexing/retrieval, synteny/orthogroup methods, and spatial-omics methods. Use an unfiltered bioRxiv feed only when the user explicitly asks for it. If the user asks to document preferences in `SKILL.md`, summarize the exact additions and update it only after direct confirmation; explain that project-skill changes affect future uses of this skill.

## Collect papers

Run the script from the skill folder. Use one or more filters; combine filters to narrow a feed. Search terms are case-insensitive in practice.

```bash
python3 scripts/search_biorxiv.py --keyword "single-cell" --keyword "spatial transcriptomics" --days 1 --state .biorxiv-state.json
python3 scripts/search_biorxiv.py --author "Jane Doe" --days 30
python3 scripts/search_biorxiv.py --title "immune atlas" --days 365
python3 scripts/search_biorxiv.py --any-keyword --keyword compression --keyword "data structure" --keyword graph --keyword tree --keyword combinatorics --days 7
python3 scripts/search_biorxiv.py --native-biorxiv --start-date 2026-08-11 --end-date 2026-08-11
```

- Use `--native-biorxiv` for daily digests: it reads bioRxiv's native feed and avoids third-party indexing delays. It retrieves the complete first-posted daily list before applying the method/tool ranking. Use Europe PMC for keyword, author, or title searches outside the daily feed. Use `--all-biorxiv` only for a broad, non-topic-ranked sample of recent biology preprints.
- Use `--state PATH` on repeat runs. It omits papers already reported and updates the state only after a successful search.
- Use `--all` to include already-seen papers, `--max N` to cap output, and `--json` for machine-readable output.
- Do not treat a failed request or an empty result as evidence that no papers exist; say which occurred.

## Search algorithmic research on arXiv

Run this step only when the user explicitly requests arXiv, algorithms/theory, or non-biology papers. Prioritize `cs.DS` (data structures and algorithms), `cs.IT`/`math.IT` (information theory and compression), `cs.CC` (complexity), `cs.DM`/`math.CO` (discrete mathematics and combinatorics), and `cs.LG` only when machine learning is part of the request. Search titles and abstracts using the user’s terms plus suitable equivalents, including `compression`, `succinct data structure`, `tree`, `graph`, `set system`, `subset`, `algorithm`, `data structure`, and `combinatorics`.

Use arXiv’s submitted date for the requested timeframe. Label the arXiv category beside every result. Do not call an applied biology paper algorithmic merely because it uses a model or an analysis method.

## Source order and large result sets

When arXiv was explicitly requested, render distinct sections in this order: `bioRxiv` then `arXiv — algorithms and theory`. Otherwise, render only `bioRxiv`. Include a zero-result section for every source that was searched.

For more than 15 bioRxiv results, apply the computational-biology overflow rule below. For more than 15 arXiv algorithmic results, show the 15 newest papers in the targeted algorithmic categories and report the total matching arXiv count plus the number not shown. Do not mix the two sources into one ranked list.

## Triage and report

When the user specifies a timeframe, list **every** matching bioRxiv paper first posted in that period. Do not silently select a top five or a representative sample. Include the post date beside every title, state the total count and the exact inclusive date range, and say plainly if the count is zero. Use `FIRST_PDATE`/first-posted date rather than a later indexing or revision date.

**bioRxiv overflow rule:** If a bioRxiv search returns more than 15 papers, show up to 15 computational-method/tool papers, with central algorithmic or scalable software contributions ranked ahead of generic model use and sorted by first-posted date to break ties. Give priority to data structures, compression, graph/tree algorithms, genomic indexing or retrieval, synteny/orthogroup analysis, genome reconstruction, spatial-omics methods, and reusable pipelines. Report the total result count, the number classified as computational biology, the number in other biology categories, and the number of computational-biology papers not shown. Call it a metadata-based classification, not a definitive bioRxiv subject category. If fewer than 15 papers meet that classification, show all of them and report the shortfall; do not fill the list with unrelated papers unless the user asks.

## Adapt to preferences

Maintain a concise preference profile for the active task from the user's explicit requests and feedback. Use it to adjust future queries and ranking. The profile can include:

- preferred topics, methods, organisms, authors, venues, and sources;
- synonyms, related concepts, and technical vocabulary to add;
- unwanted topics, techniques, authors, or sources to exclude;
- preferred result order, maximum digest size, date window, and delivery schedule.

Treat statements such as “more algorithmic,” “not what I want,” “show more papers like this,” and “exclude this topic” as feedback. State the resulting adjustment briefly in the next digest. Add accepted papers or themes as positive signals; add rejected themes as exclusions. Weight recent, repeated feedback more strongly than older feedback.

When clicks are visible in the active task, treat opening a paper link as a **weak positive signal** for its topic, methods, authors, and source. Repeated clicks on similar papers can increase their ranking and add their shared terms to the next search expansion. Do not interpret a single click as endorsement, use it to infer sensitive interests, or treat a lack of clicks as a negative signal. Give explicit feedback more weight than click behavior, and let the user ask to reset or ignore click-based learning at any time.

Do not infer personal interests from unrelated tasks, external data, or a paper merely because it appeared in a result. Do not persist a preference outside the active task or use it for automation without the user’s authorization. When a preference is ambiguous or would materially widen the source scope, propose the interpretation before making it permanent.

For each paper, retain the title, authors, posted date, DOI/link, and one-sentence relevance note tied to the chat-derived profile. State the filters and date range at the top. Group the complete list into `High relevance`, `Worth a look`, and `Watchlist` only when useful; do not omit lower-priority matches.

Be explicit that this is a discovery feed, not a systematic review: keyword and metadata indexing can miss synonym-heavy or newly posted work. Suggest adding synonyms, gene/protein aliases, methods, organisms, and author name variants to reduce false negatives.

## Practical everyday setup

Keep a short saved query list, for example: disease/phenotype, method, organism, competitor/lab authors, and exact project terms. Run it daily during active projects and weekly otherwise. Pair it with bioRxiv RSS alerts for the relevant subject areas; the overlap makes missed papers less likely.

## Daily notifications

After the first-use scan, always ask whether the user wants a daily **Codex task notification**. Do not create the automation merely because it was mentioned. State the schedule, timezone, and query profile before creating it. A daily digest must search papers first posted on the **previous calendar day** in the configured timezone (for example, an August 6 run covers August 5), not the period since the last run. Use `--native-biorxiv` with the exact inclusive start and end date: do not use a third-party metadata index for the daily scan, because it can lag and omit new papers. Include all new matches subject to the overflow rule, and do not use a seen-state file to suppress that previous-day list. When the user answers yes and confirms those details, create the recurring Codex-task automation using the platform's automation facility, then confirm the active schedule.

### Native-feed failure fallback

Treat an empty, invalid, or non-JSON native API response as a **source failure**, even when its HTTP status is `200 OK`; never interpret it as a zero-paper day. In that case:

1. Use bioRxiv's daily listings in the browser as the first-party fallback and wait briefly for any automatic security verification to clear.
2. If the browser presents an interactive CAPTCHA, do not bypass it. Tell the user that manual verification is required and do not report “no papers.”
3. If the website becomes available, collect and rank the requested day's papers from it, and state that the website fallback was used.
4. If neither path is available, report the retrieval failure plainly; do not substitute another source unless the user explicitly authorizes one.

## Computational-biology classification

Treat this as a **metadata-based estimate**, not an official bioRxiv category and never as a claim that every computational-biology paper was found. Mark a paper as computational biology only when its title or abstract indicates that computation is a central contribution, such as bioinformatics, algorithm development, scalable software, a reusable pipeline, retrieval/indexing, synteny/orthogroup analysis, genome reconstruction, spatial-omics methods, a database/resource, or a computational method/model.

Do not classify a paper solely because it uses or mentions transcriptomics, sequencing, proteomics, single-cell data, spatial data, multi-omics, generic statistical analysis, a one-off computational model, or a prediction of a biological/clinical outcome. Those techniques often support primarily experimental work. Exclude papers where computation is an auxiliary validation tool rather than the principal method or output. When an official bioRxiv subject category is available, report it separately and prefer it over a text heuristic. If the user needs an exhaustive subject-category feed, say that the metadata source and category definition must be agreed first.

## Resource

`scripts/search_biorxiv.py` searches recent bioRxiv records through Europe PMC using only the Python standard library. It retrieves all matching pages by default, applies the overflow rule to display output, and needs internet access.
