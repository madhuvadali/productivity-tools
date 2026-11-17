# Viva Examiner

**Status:** Built and delivered, 17 November 2026
**Files:** `viva-examiner.html` (the app, one self-contained file), plus sample `questions.txt` and `students.csv`

---

## What it is

A local, instructor-only app for running end-of-course viva exams. Open the HTML file in a browser (double-click). No installation, no server, nothing leaves the computer. Students never see it.

---

## Inputs

**Question bank (.txt)** — `Q:` and `A:` blocks, blank line between entries. Answers may span several lines.

```
Q: What is overfitting?
A: When a model learns noise in the training data and performs poorly on unseen data.

Q: What does regularisation do?
A: It penalises model complexity to reduce overfitting.
```

**Student list (.csv)** — `roll,name` header, one student per row. Order is kept. A file with one name per line also works.

```
roll,name
IC24001,Aarav Mehta
IC24002,Ananya Iyer
```

---

## How a session works

1. Load both files, set the options, tick one or more students, press Start. The stopwatch starts then.
2. **Settings:** questions per student, max time (minutes), no repeat questions per student, notes on each question, allow replacing a question.
3. Each selected student gets their own card with a different random question and its expected answer.
4. The instructor marks each question **Right (1)**, **Wrong (0)** or **Skip (0)**, with an optional note.
5. **Skip in a group:** the answer is saved as Skip (0) and the same question is passed to the next student in the group (it counts as one of their questions). A question is never passed to a student who already skipped it.
6. **Skip with one student:** shown as "Don't know"; automatically recorded as Wrong (0).
7. **Replace question** swaps an unsuitable question for another. It is not recorded.
8. **Timer:** one stopwatch per session, counting up to the max time. At the limit it turns red and beeps; marking can continue. Pause and End session are available.

---

## Saving and export

- Everything auto-saves in the browser (localStorage), so a refresh does not lose progress. A restored session comes back paused.
- **Export results (CSV):** one row per question — roll, name, question number, question, expected answer, result, score, note, auto-Wrong-from-skip flag, passed-on-from, time, session.
- **Export summary (CSV):** one row per student — questions, right, wrong, skip, total score.
- **Clear all results** deletes the saved answers.

The saved data lives only in the browser used. **Export the CSVs when the viva is finished**; clearing browser data deletes the answers.

---

## Design decisions

- Single HTML file, vanilla JavaScript, no dependencies, so it works offline and survives for years.
- Deliberately plain interface: no icons, coloured pills or helper text, and the three outcome buttons are identical, labelled with their points.
- Students are identified by roll number and name, so reloading the same student list keeps earlier results.
- A passed-on question is queued on the next student's card and shown once they finish their current question, so a question being asked is never replaced mid-answer.

---

## Verification performed

A scripted test in a simulated browser (jsdom) covered: parsing both input formats, distinct questions per card, Skip recorded as 0 and queued to the next student, skipper receiving a new question, student finishing at their quota, single-student Skip recorded as Wrong, no repeat after a skip, and results persisting. The layout and the beep were not checked in a real browser.

---

## Privacy

`students.csv` here holds made-up sample names. Do not commit real student lists or question banks to a public repository.

---

## Open items

- Try it with a real question bank and a real class list, then note any changes.
- Optional: colour on the Right/Wrong/Skip buttons, different export columns.
