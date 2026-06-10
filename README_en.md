# AI Research Detective 🔍

**English** · [中文](README.md)

An AI research analysis toolkit powered by the **Detective Method** — a meta-analysis paradigm that uses LLMs for more stable long-range memory support and more systematic global scanning to complement standard qualitative and quantitative analysis.

This repository is a [**Claude Code plugin**](https://docs.claude.com/en/docs/claude-code/plugins) — Claude Code's extension mechanism that packages several collaborating skills into a one-click installable toolkit.

---

## Why it exists

A researcher's biggest bottleneck isn't methodology — interview analysis, survey statistics, and competitive teardowns are all mature techniques. The bottleneck is the human executing them:

| Human cognitive limit | Consequence |
| --- | --- |
| Memory decay | By the 15th transcript you've forgotten the details of the 3rd |
| Confirmation bias | Anomalies that don't fit expectations get ignored |
| Pattern-recognition ceiling | You can't hold the N×N cross-links across 20 documents in your head |
| Poor frequency estimation | "I feel like a few people mentioned this" is an unreliable gut call |

The Detective Method doesn't replace traditional research methods — it adds a meta-analysis layer on top of them, with five "detective moves" that systematically cover these blind spots.

## Does it actually work

Validated on a real project with 250+ user interviews and surveys. **The case is anonymized and the raw data is not published** — the findings below are illustrative, not an independently reproducible benchmark:

- **Context correction**: a certain feature was mentioned frequently, but the overwhelming majority of mentions appeared in a privacy-fear context — looking at frequency alone would yield the wrong conclusion
- **Contradiction audit**: users who claimed to "have no red lines" heavily overlapped with users who simultaneously expressed privacy concerns; the truly unconcerned were rare — an intuitive audience segmentation falls apart once cross-referenced against the evidence

These two kinds of findings are exactly what the Detective Method is built to catch (context collapse, selective ignoring of contradictions).

## What it does

Three collaborating skills:

```text
Raw material
   │
   ▼
[research-archivist: ingest] ──► wiki knowledge base
                                      │
                                      ▼
                          [research-detective: analyze]
                                      │
                ┌─────────────────────┴─────────────────────┐
                ▼                                           ▼
     ① Brief form (for a specific question)      ② Full research report
        A1 one-page summary                          + detective memo
        A2 evidence-chain map                            │
        B1 info pack (optional, for downstream AI)        ▼
                                       [research-reviewer: adversarial review] (on demand)
                                                          │
                                                          ▼
                                       review.md → [detective revises] → final delivery
```

- **research-archivist**: incrementally ingests raw material into a structured wiki knowledge base (the **LLM_wiki** methodology: analysis works directly on "compiled knowledge" instead of re-reading source files each time; the wiki keeps growing with every analysis). Can be skipped for ≤50 documents.
- **research-detective**: runs five detective moves on the wiki (or `data/`) — full-memory encoding, blind-spot scan, global association discovery, contradiction audit, evidence-chain tracing. Produces one of two outputs: ① a brief (A1+A2, optional B1); ② a full report + detective memo.
- **research-reviewer**: adversarially validates a full report, filtering core conclusions by the standard "if it can be overturned, the report fails," ruling each as confirmed / weakened / challenged, after which the detective revises accordingly.

## Install

In Claude Code, add this repo as a marketplace, then install the plugin from it (this repo serves as both marketplace and plugin):

```text
/plugin marketplace add myfmarco-arch/ai-research-detective
/plugin install ai-research-detective@ai-research-detective
```

> `@ai-research-detective` is the marketplace name; the format is `<plugin>@<marketplace>`.
>
> A local path also works: `/plugin marketplace add /path/to/ai-research-detective`.
>
> To update later: `/plugin marketplace update ai-research-detective`.

For local development you can just symlink:

```bash
ln -s "$(pwd)" ~/.claude/plugins/ai-research-detective
```

After installation, the three skills are auto-discovered by Claude Code and triggered by description matching — "help me ingest these interviews" activates archivist, "analyze these user interviews" activates detective, "review this report" activates reviewer. You can also force-load with an explicit `load the research-detective skill`.

> The project-level `CLAUDE.md` (quality red lines for research output) is **auto-copied from the plugin's `shared/CLAUDE.md` into your research project root** by each skill at cold start — no manual step needed.

## Usage

### Step 1: Ingest

```bash
cd ~/my-research
claude
```

Put your material in the current directory or a `data/` subdirectory, then say:

```text
help me ingest the interview material into a wiki
```

Archivist activates automatically, reads each document, and builds out `wiki/`. For new material later: `there's new survey data, help me update the wiki` — runs an incremental update.

### Step 2: Detective analysis

Once ingestion is done:

```text
use research-detective to analyze the data in the wiki
```

Or with a specific question:

```text
load the research-detective skill, analyze users' true attitudes toward privacy
```

When detective detects `wiki/`, it skips evidence collection and goes straight to detective analysis.

### Step 3: Adversarial review (optional but recommended)

After the report is produced:

```text
use research-reviewer to review this report
```

Reviewer actively searches for counter-evidence and produces `outputs/review.md`, then have the detective revise: `revise the report based on the review results in review.md`.

### Runs without a wiki too

For ≤50 documents you can skip ingestion: `analyze the user interviews in data/` — detective will do evidence collection and analysis itself. The wiki mode shines in high-volume and incremental-update scenarios.

## Supported material types

| Type | Format | Handling |
| --- | --- | --- |
| Qualitative interviews | .md / .txt / .json | LLM reads each document |
| Quantitative surveys | .csv / .xlsx | Python statistics + LLM interpretation |
| Literature | .md / .pdf | LLM extracts theoretical frameworks |
| Competitive material | .md | LLM extracts capability matrices |

## Deep-dive features

The four sections below are ordered by value, describing this tool's core design choices.

### 1. LLM_wiki: a continuously growing knowledge base

> This section implements [Andrej Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) specialized for research analysis — treating the LLM as a "compiler" that compiles raw material into a structured, maintainable markdown knowledge base instead of re-reading source files each time. This tool extends that pattern with a research-methodology layer (detective moves + adversarial-review write-back + material/interpretation separation).

During ingestion, archivist has the LLM read each document and **compile the raw content into a structured markdown wiki** — theme pages, contradiction logs, user verbatims, statistics, literature frameworks, and so on. Later, detective analysis works directly on this "compiled knowledge," with no need to go back to the source.

**The core feature is "continuous growth"** — the wiki isn't a one-shot dead artifact:

- New themes, contradictions, associations, and blind spots that **emerge during each detective analysis** are auto-written back to the wiki, tagged with the source `#analysis_YYYYMMDD`
- Counter-examples, refuted theories, and covered blind spots **found during each reviewer pass** are auto-written back, tagged `#review_YYYYMMDD`
- First-hand citations (`#interview_xx`) and analytical emergence (`#analysis_xx`) are strictly separated into different columns, so **fact and interpretation are always distinguishable**
- The second analysis stands on the shoulders of the first instead of starting from scratch; a researcher who picks up the project six months later can reconstruct how every judgment evolved by reading the wiki

Design choices:

- **The compiled artifact is markdown, not embedding vectors** — readable, auditable, and hand-editable by researchers
- **Write-back only appends, never overwrites** — even when an earlier conclusion turns out wrong, you open a new `#analysis_xx correction: ...` entry, preserving the old one so the evolution of judgment stays visible

The material/analysis format contract is in [contracts/wiki_format.md](contracts/wiki_format.md); write-back rules are in [contracts/analysis_writeback.md](contracts/analysis_writeback.md).

### 2. Detective toolkit (26 analysis tools)

On-demand specialized analysis tools, organized in four layers:

- **Collection layer**: clue extraction, evidence grading, triangulation, collection discipline
- **Structure layer**: pattern scanning, causal mechanisms, JTBD, Kano, user journey, mental models, etc.
- **Judgment layer**: ACH (analysis of competing hypotheses), red teaming, linchpin check, pre-mortem, etc.
- **Synthesis layer**: evidence synthesis

Each tool comes with use cases and operational steps — detective isn't a "general analysis assistant," it "picks tools by methodology and makes judgments by evidence strength." See the quick-reference table at the end of [detective_toolkit.md](skills/research-detective/guides/detective_toolkit.md).

### 3. Quality assurance: adversarial review + writing-style constraints

The quality of research output is guarded by two independent mechanisms — the argumentation layer and the writing layer.

**Adversarial review** (argumentation layer · run independently by research-reviewer)

For full research reports, playing the "fact-checker" role:

- Filters core conclusions by the standard "**if overturned, the report fails**" (≤3 conclusions per batch for a deep review; multi-topic reports are reviewed in batches)
- Doesn't just read the existing report — **actively searches for counter-evidence** — reading the wiki's contradiction pages, uncategorized pages, and quotes, and spot-checking back to the raw material
- Rules each conclusion: confirmed (survives the adversary) / weakened (needs qualifying conditions) / challenged (may be wrong)
- The detective revises accordingly; weakened or overturned judgments are written back to the wiki's "analysis increment" column, tagged `#review_YYYYMMDD`, **preserving the evolution of judgment**

The brief form (A1+A2) currently doesn't go through reviewer. The report form is strongly recommended for external publication, decision-making, or when evidence strength is in doubt.

**Writing-style constraints** (writing layer · self-check before and after drafting)

Before and after drafting, the researcher self-checks against [writing_style.md](skills/research-detective/guides/writing_style.md) + [report_principles.md](skills/research-detective/guides/report_principles.md) to block the typical patterns of AI writing (concept-itis, straw men, weasel wording, end-of-section punchlines, etc.) along with quantitative discipline. The machine-checkable parts are auto-run by scripts as a backstop; structural issues still require a human walkthrough of the checklist.

### 4. B1 info pack: AI-to-AI decision-context delivery

Research output gets consumed by downstream AI workflows — a product AI writing a PRD, a design AI producing options, a strategy AI planning. The B1 info pack is a structured envelope designed for this delivery step:

- Not raw material, but the researcher's extraction of material into **decision slices** — user segments / pain-point lists / design constraints / scenario success states. Downstream AI uses them directly, without having to do the "raw evidence → action seed" conversion itself
- Comes with a **negative list** and **unresolved questions** as guardrails — explicitly telling downstream AI which conclusions can't be extrapolated and which areas the research didn't cover
- Comes with an **AI operating protocol** — every citation carries an ID, cross-ID integrity is machine-verifiable

Triggered on demand after a brief or report is complete; the researcher packages it via a conversational command. On generation, a **B1 structure lint runs automatically** as a backstop (no leftover placeholders / all cross-ID citations resolve / required sections non-empty). Full contract in [contracts/information_pack.md](contracts/information_pack.md).

## Operations & troubleshooting

**Daily operations**:

- **Adding material**: drop new files into `data/`, say "update the wiki," archivist runs an incremental update (only processes new additions, doesn't touch old conclusions)
- **Ingestion re-check**: runs automatically after each ingestion — pulls 3 raw documents and cross-checks against the wiki for coverage, traceability, and contradiction completeness. Can also be triggered manually: `run an ingestion re-check on the current wiki`
- **Empty-project startup**: `help me initialize a research project` → archivist runs cold start to generate CONTEXT.md + wiki skeleton

**Common issues**:

- On first use, explicitly `load the research-archivist skill` or `load the research-detective skill` to ensure the skill is loaded before analysis begins
- If Claude starts analyzing without stopping to ask the research question, remind it: "ask me what the research question is first"
- After analysis, check that the five detective-move artifacts exist under `process/`: `3a_coding.md` / `3b_blind_spots.md` / `3c_associations.md` / `3d_contradictions_audit.md` / `3e_evidence_chains.md` (3a can be omitted in wiki mode). You can also run `python3 ${CLAUDE_PLUGIN_ROOT}/skills/research-detective/scripts/lint_process.py process/` to have the script check them in one pass

## Project structure

```text
ai-research-detective/                   # repo root = plugin root
├── .claude-plugin/                      # plugin metadata (plugin.json + marketplace.json)
├── README.md / README_en.md / LICENSE
├── contracts/                           # shared contracts across skills / boundaries
│   ├── wiki_format.md                   # wiki page format
│   ├── analysis_writeback.md            # analysis write-back rules
│   └── information_pack.md              # B1 info-pack contract
├── shared/                              # resources shared by all three skills (not a skill)
│   ├── CLAUDE.md                        # project-level hard constraints
│   ├── cold_start.md                    # cold-start flow
│   ├── templates/                       # CONTEXT.md / README.md templates
│   └── scripts/                         # cross-skill lint (lint_context.py) + tests
└── skills/                              # skills auto-discovered by Claude Code
    ├── research-archivist/
    │   ├── SKILL.md
    │   └── scripts/                     # verify_quotes.py (full wiki-citation validation) + tests
    ├── research-detective/
    │   ├── SKILL.md                     # general flow + step 4 routes to a workflow
    │   ├── workflows/                   # brief / report output workflows
    │   ├── guides/                      # detective methodology + 26-tool toolkit + writing rules
    │   ├── templates/                   # report / A1 / A2 / B1 templates
    │   └── scripts/                     # lint_report / lint_information_pack / lint_process + tests
    └── research-reviewer/
        ├── SKILL.md
        └── scripts/                     # lint_review.py (search log + evidence-strength re-check + sampling mode) + tests
```

> **shared/ vs contracts/**: `shared/` holds process resources (templates, starters) that users copy and then modify; `contracts/` holds interface specs (protocols across skills / boundaries) that all skills follow and must not change independently.
>
> Inside SKILL.md, use `../../shared/...` or `../../contracts/...` to go up two levels.

## Feedback & contributing

Feedback, suggestions, and code contributions are welcome via [GitHub Issues](https://github.com/myfmarco-arch/ai-research-detective/issues). See [CONTRIBUTING.md](CONTRIBUTING.md) for the contribution flow, testing, and versioning conventions. Current version is in `.claude-plugin/plugin.json`.

## Acknowledgements

- **LLM Wiki pattern** — this tool's ingestion + analysis architecture is based on Andrej Karpathy's [llm-wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f): treating the LLM as a "compiler" and maintaining a continuously growing markdown knowledge base. This tool builds a research-methodology layer on top (detective moves, adversarial review, B1 info pack, strict material/interpretation separation).
- The English AI-pattern detection in **writing-style lint** references the patterns from [blader/humanizer](https://github.com/blader/humanizer) (based on Wikipedia's "Signs of AI writing"); the Chinese research-report-specific rules are original to this project.

## License

MIT
