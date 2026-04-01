# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

A user must be able to:

1. **Add a pet** — Register a pet by name, species, and age under an owner profile.
2. **Schedule a task** — Assign a care activity (walk, feed, medication, appointment) to a specific pet with a time, date, and frequency.
3. **View today's tasks** — See all tasks for the day, sorted by time, with any scheduling conflicts flagged.

### Classes

- **`Task`** — The atomic unit. Each task holds a description, time, frequency, completion status, and due date.
- **`Pet`** — An intermediate container. It owns a list of `Task` objects and provides helper methods for adding, removing, and filtering tasks.
- **`Owner`** — The top-level entity. An Owner owns a list of `Pet` objects and aggregates all tasks across them. This is the single source of truth for the entire system.
- **`Scheduler`** — The a non-dataclass, because it holds _behavior_, not data. It receives an `Owner` instance and acts as the engine for sorting, filtering, conflict detection, and recurrence.

**b. Design changes**

When I asked Copilot to review my initial skeleton, it flagged two things:

1. **Missing `pet_name` on Task** — My first draft had Tasks that only knew their description and time. Copilot pointed out that once a Scheduler aggregates tasks from multiple pets, you lose track of which pet each task belongs to. I added a `pet_name: str` field to `Task` to solve this.

2. **`Scheduler` should receive `Owner`, not a list of pets directly** — My first instinct was to pass `Scheduler` a flat list of pets. Copilot suggested passing the whole `Owner` so the Scheduler has access to owner-level context (e.g., the owner's name for display).

![](image1.png)

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

### Sorting

I used Python's built-in `sorted()` with a `lambda t: t.time` key. Because times are stored as `"HH:MM"` strings, lexicographic sorting works correctly without converting to `datetime` objects — a deliberate simplicity choice.

### Filtering

`filter_tasks()` accepts optional `pet_name` and `status` arguments. Using `None` as the default means "no filter," which keeps the call site clean: `scheduler.filter_tasks()` returns everything, while `scheduler.filter_tasks(pet_name="Buddy", status="pending")` narrows precisely.

### Conflict Detection

I used a dictionary keyed on `(due_date, time)` tuples. The first time a key is seen, it's stored. The second time, a warning string is generated. This is O(n) time and space complexity.

### Recurring Tasks

`Task.mark_complete()` returns a new `Task` (or `None` for one-time tasks). The caller is responsible for adding the returned task to the correct pet. This "caller adds the follow-up" pattern keeps `Task` from needing a reference back to its parent `Pet`, avoiding circular dependencies.

---

**b. Tradeoffs**

**Conflict detection only checks for exact time matches**, not overlapping durations. A 30-minute walk starting at 09:00 and a vet appointment at 09:15 would not be flagged. This is a deliberate simplicity tradeoff — tasks in PawPal+ don't have a duration attribute, so exact-match detection is the most honest check we can do without fabricating data.

**String times vs. `datetime.time`** — Storing time as `"HH:MM"` strings instead of `datetime.time` objects makes data entry simpler and JSON serialization trivial. The downside is that 12-hour format (e.g., "9:00 AM") would break sorting. The app enforces 24-hour input via Streamlit's `st.time_input`, which mitigates this risk.

---

## 3. AI Collaboration

**a. How you used AI**

I used AI tools across every phase of the project, but in different ways depending on the task. During Phase 1, I used Copilot Chat for design brainstorming — I described the four classes I had in mind and asked it to generate a Mermaid.js UML diagram, which helped me catch a missing relationship (the Scheduler needing access to the Owner, not just a raw list of pets) before writing a single line of code.

During Phase 2, I used Agent Mode to scaffold the full implementations of my classes, pointing it at my skeleton file with `#file:pawpal_system.py` so it worked within my existing design rather than inventing a new one. In Phase 4, I used Inline Chat to refine specific methods — for example, asking "how can I sort these Task objects by their time string using a lambda?" on just the `sort_by_time` method.

The most helpful kinds of prompts were **specific and context-anchored**. Vague prompts like "help me build a scheduler" produced generic code that didn't fit my architecture. Targeted prompts like "based on the classes in `#file:pawpal_system.py`, how should `Scheduler.detect_conflicts()` retrieve tasks without duplicating the aggregation logic already in `Owner.get_all_tasks()`?" produced suggestions that actually integrated cleanly.

**b. Judgment and verification**

When I asked Copilot to implement recurring task logic, it placed all of the recurrence handling inside the `Scheduler` class — a `reschedule_all()` method that checked each task's frequency, calculated the next due date, and created a new task. I did not accept this suggestion.

My concern was that this approach made the `Scheduler` responsible for knowing the internal rules of how a `Task` recurs — what "daily" means, what "weekly" means, how to calculate `timedelta`. That's information that belongs to the `Task` itself. Accepting the suggestion would have created a coupling where changing how recurrence works (say, adding a "bi-weekly" frequency) would require editing the `Scheduler` rather than just the `Task`.

I verified this by mentally tracing what would break if I added a new frequency type. With Copilot's version, I'd have to update the Scheduler's conditional logic. With my version — where `Task.mark_complete()` returns the next task — I'd only need to add a new branch inside the `Task` class. That confirmed my instinct to reject the suggestion and move the logic into `Task`.

---

## 4. Testing and Verification

**a. What you tested**

I tested the following behaviors:

- **Task completion** — that calling `mark_complete()` sets `is_complete` to `True`. This is foundational; if completion doesn't register, the entire status-tracking system is broken.
- **Recurrence for daily tasks** — that marking a daily task complete returns a new task with `due_date = today + 1 day`. This was important because recurrence is the feature most likely to have an off-by-one error.
- **Recurrence for weekly tasks** — same as above but with a 7-day offset.
- **One-time tasks return `None`** — that tasks with `frequency="once"` don't generate a follow-up. Without this test, a one-time vet appointment could silently keep rescheduling itself.
- **Adding a task increases pet task count** — basic sanity check that `add_task()` actually mutates the list.
- **Sorting correctness** — that `sort_by_time()` returns tasks in chronological `HH:MM` order regardless of insertion order.
- **Filtering by pet and status** — that the filter returns only the expected subset and doesn't leak tasks from other pets or wrong statuses.
- **Conflict detection** — that two tasks at the same time on the same day produce a warning, and that no false warnings are raised when there are no conflicts.
- **Empty pet edge case** — that a pet with no tasks doesn't cause exceptions anywhere in the scheduling pipeline.

These tests mattered because they verify the behaviors that the UI depends on silently. If sorting is broken, the user sees a scrambled schedule with no error. Tests make those silent failures loud.

**b. Confidence**

I am **4 out of 5 stars** confident that the scheduler works correctly for normal use. All tests pass and the core logic — sorting, filtering, conflict detection, recurrence — is exercised by the suite.

My confidence isn't a full 5 because of the following untested edge cases I would address next with more time:

- **Overlapping task durations** — the conflict detector only flags exact time matches. Two tasks at 09:00 and 09:15 with 30-minute durations would overlap in real life but pass silently through the system.
- **Midnight-crossing schedules** — a "daily" task completed at 23:50 should produce a task at 00:00 the next day, but the current logic uses `date.today()` as the base, which could behave unexpectedly depending on when `mark_complete()` is called.
- **Duplicate pet names** — adding two pets both named "Buddy" would cause `filter_tasks(pet_name="Buddy")` to return tasks from both, and `remove_pet("Buddy")` to only remove the first. This should either be prevented or handled explicitly.
- **Empty Owner** — an Owner with no pets should return an empty list everywhere, not raise an exception. I verified this manually but did not write an explicit test for it.

---

## 5. Reflection

**a. What went well**

I'm most satisfied with the architecture of the `Task` class and its `mark_complete()` method. Having the task return its own successor — rather than relying on an external class to calculate recurrence — kept the system modular in a way I could actually feel during development. When I was building the Streamlit UI, I didn't need to think about recurrence rules at all; I just called `mark_complete()` and handled whatever came back. That clean interface was a direct result of a design decision I made in Phase 1, which validated the value of planning before coding.

**b. What you would improve**

If I had another iteration, I would add a **duration field to `Task`** (in minutes) and upgrade `detect_conflicts()` to check for overlapping time windows instead of just exact matches. The current conflict detection gives a false sense of safety — two 45-minute tasks at 09:00 and 09:30 would never be flagged, even though they overlap. I would also redesign how the Streamlit app handles state: right now, all data lives in `st.session_state` and is lost when the browser tab closes. I would add JSON persistence (save/load on startup) so the owner's pet data survives between sessions.

**c. Key takeaway**

The most important thing I learned is that **AI is fast at writing code but blind to architectural consequences**. Every suggestion Copilot made was locally correct — it would work in isolation. But it had no awareness of the design principles I had established in earlier phases. It didn't know I wanted `Task` to own its recurrence logic, or that I wanted the Scheduler to be a thin layer over `Owner` rather than a fat controller. Those constraints existed only in my head, and holding them consistently across six phases of development was entirely my responsibility. Working with AI well doesn't mean accepting its output — it means knowing your architecture clearly enough to recognize when a suggestion moves toward it and when it doesn't.
