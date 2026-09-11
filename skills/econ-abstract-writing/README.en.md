# Economics Abstract Writing · Econ Abstract Writing

[简体中文](README.md) | English

**Write the abstract last. Establish the results, develop the complete story, and write the Introduction.
Then use five questions to turn the paper into an abstract.**

This [AI Writing Lab](../../README.md) skill helps write English-language economics abstracts in three situations:

- Your main results and Introduction are ready, and you need to draft an abstract.
- Your full manuscript draft is largely complete, and you want to extract an abstract from it.
- You already have an abstract and want to review its structure, content selection, or English prose.

## Five questions, one abstract

| Part | Question to answer first |
|---|---|
| **W — What** | What is the paper's central research question? |
| **H — How** | What is the most important method used to answer it? |
| **F1 — Findings** | What is the most direct and important answer to the question? |
| **F2 — Findings** | Why does this result arise? What mechanism evidence supports the explanation? |
| **F3 — Findings** | What else should the reader remember: differences, contrasting results, trade-offs, longer-term effects, or economic consequences? |

You can answer in English or Chinese. The assistant checks how the answers connect, then organizes
an English abstract using **WHFFF**. If there is no mechanism evidence, F2 can present another
important finding; the question and method can also share a sentence.
Each finding should add information and come from your paper.

If you have only scattered results, the skill first helps organize the story and identify gaps;
the finished abstract comes after the Introduction.
If you provide a full manuscript, the assistant can extract the five answers for you to check.
An existing abstract can be reviewed directly.

## One skill, two reading languages

Install and invoke **`econ-abstract-writing`** in either language.
The assistant follows your preferred conversational language and writes the abstract in English by default.

[SKILL.md](SKILL.md) is the single English execution entry.
[SKILL.zh.md](SKILL.zh.md) is its Chinese reading translation.
The usage guide and references are available in both languages, with links to switch between them.
Install the whole folder; there is no separate `-zh` or `-en` skill to select.

## Use the skill

### Install in Codex

Send this to Codex with `skill-installer` available:

```text
Use $skill-installer to install skills/econ-abstract-writing
from https://github.com/Rostopher/AI_writing_lab.
```

Alternatively, download this repository and copy the entire `econ-abstract-writing` folder into
your paper project's `.agents/skills/`, giving you
`.agents/skills/econ-abstract-writing/SKILL.md`.
Keep the included `references/` and `agents/` directories.
See the [official skills documentation](https://learn.chatgpt.com/docs/build-skills)
for Codex discovery locations and installation guidance.

The repository's `skills/` directory holds the maintained source.
After downloading the repository, install as above or ask your assistant to read `SKILL.md` directly.
This skill requires no API key, additional script, or paper database.

### Three ways to start

**No abstract yet:**

```text
Use $econ-abstract-writing. My main results and Introduction are ready.
Guide me through the five questions, then help me write an English abstract.
Here are my Introduction and results: ...
```

**A full manuscript:**

```text
Use $econ-abstract-writing to extract the five answers from this complete draft.
Let me check the central question and three findings before drafting the abstract.
The word limit is ...
```

**An existing abstract:**

```text
Use $econ-abstract-writing to review the abstract below.
Check whether the research question is clear, the method is informative,
and each finding adds information. Start with revision suggestions.
Abstract: ...
```

You can also supply the five answers and source material together and ask for a draft directly.
For a revised abstract, ask the assistant to review and revise.
In a chat tool that does not support skill installation, provide [SKILL.md](SKILL.md) and any needed
reference files as conversation material. This shares the method without installing a skill.

## Files and evidence

- [SKILL.md](SKILL.md): the complete instructions for the assistant.
- [Abstract patterns](references/abstract_patterns.md): content roles and variations on WHFFF.
- [Teaching examples](references/examples.md): fictional research inputs, five answers, abstracts, and a revision example.
- [Corpus evidence and method origins](references/corpus_evidence.md): key observations from 4,250 abstracts and their scope.

The corpus covers available abstracts from AER, JPE, Econometrica, REStud, and QJE over 2015–2026;
2026 is a partial year. The statistics inform content organization.
“Write the abstract last” and the five questions are the author workflow chosen for this project.
The first version's editing effectiveness still needs comparison through real use cases.
Feedback with source material, before-and-after text, and unresolved problems is welcome.

For maintenance, update the English execution entry and references, then keep the Chinese translations
aligned within the same change. Reading both translations is unnecessary when carrying out a writing task.
