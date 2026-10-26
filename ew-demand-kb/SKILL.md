---
name: ew-demand-kb
description: "读取用户的研究文件夹和已有洞察，把一手经验、外部摘录、解释与假设整理成可追溯输入。"
---

# EW Demand Knowledge Base

## Purpose

Use this skill before external research when the user supplies notes, documents, transcripts, spreadsheets, exports, screenshots, or a research folder. The knowledge base is first-party context, not automatic proof of market-wide demand.

## Workflow

1. Inventory files without uploading private material or silently expanding scope. Record path, title, author/owner when known, created/captured date, and format.
2. Read only relevant material and preserve the source locator (file path, heading, row, or note title).
3. Classify each claim as:
   - `direct_experience`: the user's own observation, delivery, task, interview, or payment;
   - `source_observation`: a copied quote or metric with an original URL;
   - `interpretation`: a reading of one or more observations;
   - `hypothesis`: a claim that still needs external or behavioral proof.
4. Convert checkable observations to `EvidenceRecord`-compatible records. Keep interpretations and hypotheses visible but do not count them as independent evidence.
5. Extract seed phrases, named users/markets, current workarounds, and explicit evidence gaps.
6. Preserve conflicting notes with dates and scope; create a follow-up question instead of overwriting either note.

## Output

```yaml
inventory: [{locator: "", title: "", captured_at: "", relevance: high|medium|low}]
internal_evidence: []
seed_phrases: []
known_workarounds: []
evidence_gaps: []
conflicts: []
privacy_notes: []
```

Each `internal_evidence` item should include `source_type: internal_kb`, `source_origin: first_party`, `source_locator`, `source_created_at`, `claim_kind`, `quote_or_observation`, `supports`, `evidence_strength`, `confidence`, and `does_not_prove`.

## Guardrails

- A direct personal experience can prove the user's context, not the frequency of the whole market.
- Copied external claims retain their original URL and should not be relabeled as first-party evidence.
- Do not infer a country, purchasing power, or willingness to pay from an unpriced note.
- Do not send private knowledge-base content to a third-party service unless the user explicitly authorizes it.
