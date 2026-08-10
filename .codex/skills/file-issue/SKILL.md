---
name: file-issue
description: Use this skill whenever the user is getting ready to file a bug report or feature request for the current repo — phrases like "file a bug", "open an issue", "let's log this", "file a feature request", "report this", or when a bug/gap has just been found in conversation and the user wants it tracked. Produces a GitHub issue via `gh issue create` with a gitmoji-prefixed title and a body that matches the repo's existing issue style. Do NOT use for PR descriptions, commit messages, or general note-taking — only for actual GitHub issues.
---

# Filing a bug report or feature request

Goal: produce an issue that reads like the maintainer wrote it in two minutes, not like a template a model filled out. Every step below exists to strip AI tells, not to add process.

## 1. Check for duplicates first

`gh issue list --state all --search "<keywords>"` before drafting anything. If a close match exists, say so and ask whether to comment on it instead of opening a new one.

## 2. Actually investigate before writing

Don't draft from the user's one-line description alone. Read the relevant code/config, and if it's a bug, find the actual cause — not just the symptom. Look at 1-2 recent closed/open issues (`gh issue list --state all --limit 5`, `gh issue view <n>`) to recalibrate tone and length before every draft; don't rely on memory of past style.

## 3. Title: gitmoji + plain sentence

Prefix with one emoji per [gitmoji.dev](https://gitmoji.dev) conventions, then a plain, specific, lowercase-after-the-emoji sentence fragment — no title-case, no trailing period. Pick the emoji for what the *issue* is about, not what the fix will look like:

- 🐛 bug report
- ✨ feature request
- ⚡️ performance problem
- 🔒️ security issue
- 📝 docs gap
- ♻️ refactor/cleanup ask
- 🔧 config/tooling issue

Example: `🐛 tofu plan matrix skips domains with no changed files`

## 4. Body: match the repo's actual style, not a bug template

Use the recent issues pulled in step 2 as the reference point for tone — plain `##` sections used only when they earn their place (`Context`, `Plan` with checkboxes, `Notes`), full sentences that explain *why* something matters, no filler. A short bug report often needs no headers at all — one or two paragraphs plus a repro command is enough.

Do NOT default to a generic scaffold like "## Description / ## Steps to Reproduce / ## Expected Behavior / ## Actual Behavior / ## Environment / ## Additional Context" — that shape is the single biggest AI tell. Only include a section if it's carrying real information; skip "Environment" if there's nothing host-specific to say, skip "Steps to Reproduce" if a single command reproduces it inline.

Other tells to avoid:
- No opening throat-clearing ("I've noticed that...", "It appears that...", "Upon investigation...").
- No closing pleasantries ("Let me know if you need anything else!", "Happy to help further").
- No exhaustive bullet-pointing of things that are one sentence as prose.
- No em-dash-heavy or perfectly symmetrical sentence rhythm — vary sentence length, use contractions where a person would.
- State the cause plainly if you found it ("X does Y because Z"), don't hedge with "it seems like" unless genuinely uncertain.
- Reference real specifics (file paths, command output, actual values) over abstract description.

## 5. Labels

Check `gh label list` for what actually exists in this repo rather than assuming GitHub defaults. Apply the one that fits; don't over-label.

## 6. Confirm before creating

Filing an issue is visible to others — show the drafted title + body and get explicit confirmation before running `gh issue create`. Don't create it speculatively "to see how it looks."
