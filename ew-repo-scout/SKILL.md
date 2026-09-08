---
name: ew-repo-scout
description: "面向开发者和 AI 实践者，在 GitHub 找到满足需求的现成 Skill 或相似项目，并核对能力、使用方式、产品差异和实现证据。"
---

# EW-Repo Scout

## Purpose

Use this skill primarily when a developer or AI practitioner is exploring a technical idea, building a Skill, designing a product, or looking for an existing Skill to use. These are the intended audience, not a hardcoded requester value or search filter: infer the actual requester from context and mark it unknown when it cannot be established. The proposed project's end users may be different and must be inferred from the request. Understand both layers, then explain which projects serve the same end users, problem, workflow and outcome. Discover candidates quickly, then explain product fit through evidence. Product matching, functional coverage and technical similarity are separate judgments; retrieval scores alone do not answer the user's product question.

Do not treat this as a general market-sizing or commercial competitor report. GitHub is the primary source; external project pages may be used only to clarify a repository's product positioning.

## Two use modes

- **Find something to build or study**: compare similar projects by target user, problem, workflow, outcome, product boundary and implementation evidence.
- **Find something to use**: prioritize whether an existing Skill actually satisfies the requested task, how to install or invoke it, its prerequisites, maintenance and license. Do not turn this into a product-gap analysis unless the user also wants to build or compare alternatives.

Finding a Skill does not install or run it automatically. Only perform installation or other external actions when the user explicitly asks.

## Resolve intent before retrieval

This skill accepts ideas in any domain. An idea supplied for discovery is not necessarily an idea-management product. Treat product categories as hypotheses, not a fixed menu or a default workflow.

- Use the user's original request and relevant conversation to identify who will use the proposed project, their main job, desired outcome, and explicit constraints. Summarize this understanding in one sentence. Keep user-stated requirements, tentative interpretations, and missing information separate.
- Ask one short, focused clarification question when competing interpretations would materially change the target users, workflow, required behavior, or candidate categories. Explain the specific ambiguity briefly. Wait for the answer before generating or executing queries that depend on it; an unanswered question does not confirm an assumption. Independent work may continue, but do not issue a final shortlist against an unresolved interpretation.
- If the context already resolves the ambiguity, proceed without asking again. Minor unknowns that do not change retrieval can remain unknown. If the user explicitly wants exploration across interpretations, search them in labeled branches and keep their results separate.
- Do not add AI processing, voting, ownership, task execution, browser extensions, local-first storage, or Docker deployment merely because they are common in a category. Unspecified features are unknown, not requirements or exclusion filters. “我们” does not establish a team-management use case; “本地优先” does not establish personal use.
- If the user corrects the interpretation, update the problem card and rebuild the affected queries and ranking. Reassess earlier candidates against the corrected request instead of merely relabeling the old list.

Example: “有没有快速收集、处理 idea 的项目？” leaves both the user and “处理” ambiguous. Ask “你主要是个人记录、剪藏后整理回顾，还是多人收集建议、评审并推进任务？” before choosing that search direction. If the user already said “个人知识管理，剪藏那种”, use that context directly and leave AI, deployment, and task execution unspecified unless requested.

## Workflow

1. Apply the intent clarification rule above. Select product categories from the resolved user need, not from a familiar project list.
2. Write a problem card containing the actual Skill requester (infer developer, AI practitioner, other builder, or unknown), the proposed product's target user, triggering situation, problem, current alternative, core workflow, desired outcome, core capabilities, platform, and deployment model. Keep requester and end user separate. Do not force the intended audience into the requester field or use it as a query filter. Mark unknowns and tentative interpretations explicitly; do not invent values to complete the template. Include domain-specific details only when relevant to this request.
3. Create queries from distinct meaningful angles: user problem/outcome, workflow inputs and actions, required capabilities, and project category/topics or related-project leads. Usually cover the product job and workflow before technical mechanisms. For example, personal clipping may use `web clipper` or `bookmark manager`; team feedback may use `feedback portal`. Use synonyms and relevant languages, and retain the complete intent for judging results. Do not silently turn optional suggestions into filters. Preserve which queries found each candidate so incremental discoveries can be explained.
4. Read [references/retrieval.md](references/retrieval.md) for query syntax, available sources, request budgets and failure handling. Resolve script paths against this skill's directory, not the session's working directory. Start with a few repository queries; add targeted topic, code or issue queries where they answer a coverage gap. Write JSON to a file so raw API data does not flood the conversation:

   ```bash
   python3 <skill_dir>/scripts/github_discover.py --idea "..." --query "..." --query "..." --output /tmp/discovery.json
   python3 <skill_dir>/scripts/github_discover.py --seed-repo owner/repo --deep-limit 1 --activity --output /tmp/project-evidence.json
   ```

   Repository, topic, code and issue search discover candidates; README, LICENSE, release and optional recent activity provide evidence. Use existing `GITHUB_TOKEN` or `GH_TOKEN` when available. Code Search is explicitly skipped without authentication. Preserve `search_metadata`: per-query status, total counts, limits, incomplete results, cache age, errors and timing. Few results do not prove rate limiting; use actual HTTP/status evidence.
5. Read [references/product-comparison.md](references/product-comparison.md) before judging candidates. Inspect README, documentation, homepage/demo, license and maintenance evidence. For the leading direct matches and disputed candidates, trace the decisive user-workflow steps through source: entry/trigger → processing → state/storage → output or next action. Record concrete files, call relationships and version, not merely that a clone or keyword search happened. Mark steps as code-observed, documentation-only or unconfirmed. This targeted Agent reading complements the retrieval script; it is not an automated proof that the whole workflow runs.
6. Audit coverage against the problem card. If a broad README query yields a huge pool but only a tiny top slice with many irrelevant hits, refine task phrases or follow topic/related-project leads; candidate count alone does not show coverage. If candidates belong to a different user group or workflow, revise queries rather than redefining the user's need. Clarify new material ambiguity before choosing a direction. Do not drop small projects solely for low stars.
7. Merge rounds without losing earlier candidates. The script merges case variants and known repository-ID aliases. It preserves distinct forks and exposes parent/source metadata when inspected; it does not prove mirrors are identical or group all multi-repository products. Review those relationships before counting alternatives, and keep meaningful divergent forks. Distinguish a public repository from confirmed open-source licensing; source-available/noncommercial projects and unknown licenses must be labeled separately.
8. For each retained repository, first summarize its actual target user, problem, workflow, and core capabilities from evidence. For a Skill candidate, also record its invocation/install path and prerequisites. Then classify it as one of: direct product match, adjacent product, reusable technical component, architecture/UX reference, or low-relevance match.
9. Rate product match, functional coverage and technical match independently using the five-star rubric in product-comparison.md. Render integer stars such as ⭐️⭐️⭐️⭐️（4/5） with a short reason for each, replacing vague high/medium/low labels. Use ❔未确认 for insufficient evidence or an unspecified technical baseline; unknown is not one star. Do not average the dimensions or equate ratings with accuracy, popularity or production quality. Explain concrete overlaps and differences in separate bullet groups.
10. Keep project form, maintenance and maturity separate. CLI, library and browser extension describe form, not maturity. Maintenance needs dated observations; `pushed_at` is last push, not necessarily a code commit, and open issue counts include PRs. Maturity ranges from prototype to usable/established product and needs evidence of completeness, documentation, distribution and use. Docker instructions alone do not establish production readiness; little recent activity can also mean stable software. Missing release/license endpoints differ from failed or rate-limited requests.
11. Cite the evidence used for each non-trivial conclusion. Never infer active users, production readiness, or licensing rights from stars alone.

## Ranking guidance

Rank primarily by problem, target user, workflow, and outcome overlap. Use technical overlap to discover candidates and identify reuse opportunities, not as a substitute for product similarity. Report activity and maturity separately from similarity. Useful health signals include `archived`, last push, latest release, issue responsiveness, documentation quality, installation path, and license.

## Accuracy and evidence

Review intent fidelity, query coverage, shortlist ranking, relationship classification and evidence correctness. This self-check is not a measured accuracy score. Attach evidence to each decisive claim: official description, code observation, metadata or inference; these support different conclusions. An Issue may request an absent feature and code may be unexecuted; neither proves deployed behavior. Use uncertainty explicitly and check the source version/date.

The quantitative evaluation material in [references/evaluation.md](references/evaluation.md) and `scripts/evaluate_results.py` is maintainer-only QA. Do not run it, request labels, or expose its metrics during normal discovery. Use it only when a maintainer explicitly asks to benchmark or regression-test the skill.

## Output

For a completed report, read [references/report-template.md](references/report-template.md), write its product-comparison JSON and run `scripts/render_report.py --input <report.json> --output <report.md>`. The Agent handles this step; the user does not operate a script. Required fields and star formats are checked before readable cards are generated. Put the rendered, complete project cards directly in the final answer. A linked Markdown/JSON artifact may add detailed evidence, query logs and long URLs, but a short summary or file link must not replace the cards or omit their fields. Formatting validation does not verify truth.

Product reasoning belongs in every card, while the presentation stays compact. Use the same card for every recommended project: user/scenario, problem/outcome, workflow, core capabilities, adoption or install/use path, three reasoned ratings, separate overlap/difference bullets, workflow checks, maintenance, maturity, license and why it matters. State the Skill requester once in the idea understanding, and do not repeat it in every project card unless it changes the comparison. Keep each workflow to at most five steps, capabilities to six, overlap and differences to three each, and workflow checks to five; compress wording before rendering instead of dropping evidence. Recommend at most five complete projects (usually 3–5); keep other candidates in the raw artifact. Put a one-sentence idea understanding first and a short source/coverage note last. Avoid repeating the same conclusion in the ratings, overlap, differences and takeaway; each should add a distinct decision point. Never omit unknown fields to make a report look complete. Preserve the user's corrected intent throughout.

## Boundaries

- Do not claim that no one has built an idea; say what was found in the searched public GitHub data.
- Do not call a library or SDK a product competitor without explaining the relationship.
- Do not equate stars, forks, or recent commits with product quality.
- Do not invent README content, features, users, or license terms. Mark missing evidence as unknown.
- Do not claim hidden gems, superior recall or unique product awareness without evidence. Describe sample-bounded discoveries through logged query/source comparisons; low stars alone are not proof. Competitor positioning and our intended product focus are not evidence that competitors lack those capabilities.
