"""
PawPal+ System — Logic Layer
Manages Owners, Pets, Tasks, and smart Scheduling.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Optional


# ─────────────────────────────────────────────
# TASK
# ─────────────────────────────────────────────

@dataclass
class Task:
    """Represents a single care activity for a pet."""
    description: str
    time: str                        # "HH:MM" 24-hour format
    frequency: str                   # "once", "daily", "weekly"
    pet_name: str
    due_date: date = field(default_factory=date.today)
    is_complete: bool = False

    def mark_complete(self) -> Optional["Task"]:
        """
        Marks the task complete and returns a new Task for the next
        occurrence if the frequency is 'daily' or 'weekly'.
        Returns None for one-time tasks.
        """
        self.is_complete = True

        if self.frequency == "daily":
            return Task(
                description=self.description,
                time=self.time,
                frequency=self.frequency,
                pet_name=self.pet_name,
                due_date=self.due_date + timedelta(days=1),
            )
        elif self.frequency == "weekly":
            return Task(
                description=self.description,
                time=self.time,
                frequency=self.frequency,
                pet_name=self.pet_name,
                due_date=self.due_date + timedelta(weeks=1),
            )
        return None

    def reschedule(self, new_date: date) -> None:
        """Reschedules the task to a new date."""
        self.due_date = new_date
        self.is_complete = False

    def __str__(self) -> str:
        status = "✅" if self.is_complete else "⏳"
        return (
            f"{status} [{self.time}] {self.description} "
            f"({self.pet_name}) — {self.frequency} | Due: {self.due_date}"
        )


# ─────────────────────────────────────────────
# PET
# ─────────────────────────────────────────────

@dataclass
class Pet:
    """Represents a pet owned by an Owner."""
    name: str
    species: str
    age: int
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Adds a Task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, description: str) -> bool:
        """
        Removes the first task matching the given description.
        Returns True if found and removed, False otherwise.
        """
        for task in self.tasks:
            if task.description.lower() == description.lower():
                self.tasks.remove(task)
                return True
        return False

    def get_pending_tasks(self) -> List[Task]:
        """Returns all tasks that have not been marked complete."""
        return [t for t in self.tasks if not t.is_complete]

    def __str__(self) -> str:
        return f"{self.name} ({self.species}, {self.age} yrs) — {len(self.tasks)} task(s)"


# ─────────────────────────────────────────────
# OWNER
# ─────────────────────────────────────────────

@dataclass
class Owner:
    """Represents the pet owner who manages multiple pets."""
    name: str
    email: str
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Adds a Pet to the owner's pet list."""
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> bool:
        """
        Removes the first pet matching the given name.
        Returns True if found and removed, False otherwise.
        """
        for pet in self.pets:
            if pet.name.lower() == pet_name.lower():
                self.pets.remove(pet)
                return True
        return False

    def get_all_tasks(self) -> List[Task]:
        """Returns every task across all owned pets."""
        all_tasks = []
        for pet in self.pets:
            all_tasks.extend(pet.tasks)
        return all_tasks

    def __str__(self) -> str:
        return f"Owner: {self.name} | {len(self.pets)} pet(s)"


# ─────────────────────────────────────────────
# SCHEDULER
# ─────────────────────────────────────────────

class Scheduler:
    """
    The 'brain' of PawPal+.
    Retrieves, organizes, and manages tasks across all pets.
    """

    def __init__(self, owner: Owner) -> None:
        """Initializes the Scheduler with an Owner instance."""
        self.owner = owner

    def get_all_tasks(self) -> List[Task]:
        """Returns all tasks from all pets belonging to the owner."""
        return self.owner.get_all_tasks()

    def sort_by_time(self) -> List[Task]:
        """
        Returns all tasks sorted chronologically by their 'HH:MM' time string.
        Uses a lambda key so no datetime parsing is needed for simple sorting.
        """
        return sorted(self.get_all_tasks(), key=lambda t: t.time)

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Task]:
        """
        Filters tasks by pet name and/or completion status.

        Args:
            pet_name: If provided, only return tasks for this pet.
            status:   'complete', 'pending', or None (return all).
        """
        tasks = self.get_all_tasks()

        if pet_name:
            tasks = [t for t in tasks if t.pet_name.lower() == pet_name.lower()]

        if status == "complete":
            tasks = [t for t in tasks if t.is_complete]
        elif status == "pending":
            tasks = [t for t in tasks if not t.is_complete]

        return tasks

    def detect_conflicts(self) -> List[str]:
        """
        Checks all pending tasks for time conflicts (same time, same day).
        Returns a list of human-readable warning strings.
        """
        warnings = []
        pending = [t for t in self.get_all_tasks() if not t.is_complete]

        seen: dict = {}
        for task in pending:
            key = (task.due_date, task.time)
            if key in seen:
                warnings.append(
                    f"⚠️ Conflict: '{task.description}' ({task.pet_name}) and "
                    f"'{seen[key].description}' ({seen[key].pet_name}) "
                    f"are both at {task.time} on {task.due_date}."
                )
            else:
                seen[key] = task

        return warnings

    def handle_recurring(self) -> List[Task]:
        """
        Marks all recurring tasks due today (or earlier) as complete,
        generates their next occurrence, and adds them to the correct pet.
        Returns a list of newly created follow-up tasks.
        """
        today = date.today()
        new_tasks: List[Task] = []

        for pet in self.owner.pets:
            for task in list(pet.tasks):
                if (
                    not task.is_complete
                    and task.frequency in ("daily", "weekly")
                    and task.due_date <= today
                ):
                    next_task = task.mark_complete()
                    if next_task:
                        pet.add_task(next_task)
                        new_tasks.append(next_task)

        return new_tasks

    def todays_schedule(self) -> List[Task]:
        """Returns all tasks due today, sorted by time."""
        today = date.today()
        return sorted(
            [t for t in self.get_all_tasks() if t.due_date == today],
            key=lambda t: t.time,
        )

    def print_schedule(self) -> None:
        """Prints a formatted today's schedule to the terminal."""
        tasks = self.sort_by_time()
        conflicts = self.detect_conflicts()

        print("\n" + "=" * 50)
        print(f"  🐾 PawPal+ Schedule for {self.owner.name}")
        print("=" * 50)

        if not tasks:
            print("  No tasks scheduled.")
        else:
            for task in tasks:
                print(f"  {task}")

        if conflicts:
            print("\n--- ⚠️ Conflict Warnings ---")
            for w in conflicts:
                print(f"  {w}")

        print("=" * 50 + "\n")
