# EW-Repo Scout

[中文](README.zh-CN.md)

**Say what you want to build. Find the GitHub projects worth reading.**

Before you build a product, tool, or Skill, EW-Repo Scout helps you see who has built something close, how far they got, and what you can reuse. You can also use it to find an existing Skill for a task you need to complete.

## What it checks

GitHub search often returns projects with similar names but different users and jobs. EW-Repo Scout compares:

- who uses each project and in what situation;
- the problem it solves and the result it gives;
- the steps in its core workflow;
- what overlaps with your idea and what does not;
- maintenance, maturity, license, and evidence.

It checks important claims in source when needed. If a feature is only described in a README or cannot be confirmed, the report says so.

## Two ways to use it

- **Find projects to study:** compare users, workflows, product boundaries, and implementation choices before you build.
- **Find an existing Skill:** describe your task and get candidates with their capabilities, install or invocation path, prerequisites, maintenance, and license.

It does not install or run a Skill unless you explicitly ask for that next step.

## Use it

Tell Codex or Claude Code:

```text
Install the ew-repo-scout Skill from https://github.com/Ethan-Wang-dev/EW-Skills.
```

Then describe an idea:

```text
Use EW-Repo Scout to find an open-source project that clips web pages to local storage for personal organization and search.
```

Or find an existing Skill:

```text
Find a Skill that turns web articles into Markdown, and tell me how to install and use it.
```

If different interpretations would lead to different searches, the Skill asks one focused clarification question first.

## How it works

1. Clarify the requester, product users, situation, and desired outcome.
2. Search GitHub using problem, workflow, capability, topic, and related-project terms.
3. Deduplicate candidates and collect README, license, release, and maintenance evidence.
4. Trace the key workflow in source for leading or disputed candidates.
5. Return a compact card for each recommendation with fit ratings, overlap, differences, adoption path, and evidence.

Product fit, feature coverage, and technical fit are separate ratings. GitHub stars are never used as a similarity or quality score.

## Debug the scripts

From this directory:

```bash
python3 scripts/github_discover.py \
  --idea "Describe your idea or task" \
  --query "A query about the user task" \
  --query "A query about the workflow" \
  --output /tmp/discovery.json
```

Set `GITHUB_TOKEN` or `GH_TOKEN` to enable authenticated requests and Code Search. Without a token, Repository, Topic, and README retrieval still work, but GitHub rate limits are more likely. See [`references/retrieval.md`](references/retrieval.md) for all options.

## Customize it

- Change agent behavior and product rules in `SKILL.md`.
- Change GitHub retrieval, sources, or caching in `scripts/github_discover.py`.
- Change report fields or layout in `references/report-template.md` and `scripts/render_report.py`.
- Change fit definitions and evidence rules in `references/product-comparison.md`.
- Change the Codex display name and prompt in `agents/openai.yaml`.

Fork it and adapt it to your workflow. Improvements are welcome through [pull requests](https://github.com/Ethan-Wang-dev/EW-Skills/blob/main/CONTRIBUTING.md).

## Validation

```bash
python3 -m unittest discover -s tests -v
```

If you have Codex `skill-creator`, also run its `quick_validate.py`. The evaluation script is for maintainers with human labels; normal users do not need it.
