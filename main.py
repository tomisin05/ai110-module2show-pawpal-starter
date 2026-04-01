from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler

# ── 1. Create Owner ────────────────────────────────────────────────────────────
owner = Owner(name="Alex Johnson", email="alex@example.com")

# ── 2. Create Pets ─────────────────────────────────────────────────────────────
buddy = Pet(name="Buddy", species="Dog", age=3)
whiskers = Pet(name="Whiskers", species="Cat", age=5)

owner.add_pet(buddy)
owner.add_pet(whiskers)

# ── 3. Add Tasks ───────────────────────────────────────────────────────────────
today = date.today()

# Buddy's tasks (intentionally out of order to test sorting)
buddy.add_task(Task("Evening Walk",   "18:00", "daily",  "Buddy",    today))
buddy.add_task(Task("Morning Feed",   "07:00", "daily",  "Buddy",    today))
buddy.add_task(Task("Vet Appointment","09:00", "once",   "Buddy",    today))

# Whiskers' tasks
whiskers.add_task(Task("Medication",  "08:00", "daily",  "Whiskers", today))
whiskers.add_task(Task("Afternoon Feed","12:00","daily", "Whiskers", today))

# Deliberate conflict — same time as Buddy's Vet Appointment
whiskers.add_task(Task("Grooming",    "09:00", "once",   "Whiskers", today))

# ── 4. Create Scheduler and Print Schedule ─────────────────────────────────────
scheduler = Scheduler(owner)
scheduler.print_schedule()

# # ── 5. Demonstrate Filtering ───────────────────────────────────────────────────
# print("── Buddy's Tasks Only ──────────────────────────")
# for t in scheduler.filter_tasks(pet_name="Buddy"):
#     print(f"  {t}")

# print("\n── Pending Tasks Only ──────────────────────────")
# for t in scheduler.filter_tasks(status="pending"):
#     print(f"  {t}")

# # ── 6. Mark a task complete and show recurrence ────────────────────────────────
# print("\n── Marking 'Morning Feed' complete... ──────────")
# for task in buddy.tasks:
#     if task.description == "Morning Feed":
#         next_task = task.mark_complete()
#         if next_task:
#             buddy.add_task(next_task)
#             print(f"  ✅ Task completed. Next occurrence added: {next_task}")

# # ── 7. Reprint to confirm changes ─────────────────────────────────────────────
# scheduler.print_schedule()
