import pytest
from datetime import date, timedelta
from pawpal_system import Owner, Pet, Task, Scheduler


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_owner():
    """Returns an Owner with two pets and several tasks."""
    owner = Owner(name="Test Owner", email="test@example.com")
    today = date.today()

    dog = Pet(name="Rex", species="Dog", age=2)
    dog.add_task(Task("Walk",   "08:00", "daily", "Rex",   today))
    dog.add_task(Task("Feed",   "06:00", "daily", "Rex",   today))
    dog.add_task(Task("Bath",   "14:00", "weekly","Rex",   today))

    cat = Pet(name="Luna", species="Cat", age=4)
    cat.add_task(Task("Feed",   "07:00", "daily", "Luna",  today))
    cat.add_task(Task("Meds",   "08:00", "daily", "Luna",  today))  # conflict with Rex's Walk

    owner.add_pet(dog)
    owner.add_pet(cat)
    return owner


# ── Task Tests ─────────────────────────────────────────────────────────────────

def test_mark_complete_changes_status(sample_owner):
    """Task.mark_complete() should set is_complete to True."""
    task = sample_owner.pets[0].tasks[0]
    assert task.is_complete is False
    task.mark_complete()
    assert task.is_complete is True


def test_mark_complete_daily_returns_next_task(sample_owner):
    """Marking a daily task complete should return a new Task for tomorrow."""
    task = sample_owner.pets[0].tasks[0]  # daily Walk
    today = task.due_date
    next_task = task.mark_complete()

    assert next_task is not None
    assert next_task.due_date == today + timedelta(days=1)
    assert next_task.is_complete is False


def test_mark_complete_weekly_returns_next_task(sample_owner):
    """Marking a weekly task complete should return a new Task 7 days later."""
    # Bath is weekly (index 2)
    task = sample_owner.pets[0].tasks[2]
    today = task.due_date
    next_task = task.mark_complete()

    assert next_task is not None
    assert next_task.due_date == today + timedelta(weeks=1)


def test_mark_complete_once_returns_none():
    """Marking a one-time task complete should return None (no recurrence)."""
    task = Task("Vet", "10:00", "once", "Rex", date.today())
    result = task.mark_complete()
    assert result is None


# ── Pet Tests ──────────────────────────────────────────────────────────────────

def test_add_task_increases_count(sample_owner):
    """Adding a task to a pet should increase its task count by 1."""
    dog = sample_owner.pets[0]
    initial_count = len(dog.tasks)
    dog.add_task(Task("Play", "15:00", "daily", "Rex", date.today()))
    assert len(dog.tasks) == initial_count + 1


def test_remove_task_decreases_count(sample_owner):
    """Removing a task by description should decrease task count."""
    dog = sample_owner.pets[0]
    initial_count = len(dog.tasks)
    result = dog.remove_task("Walk")
    assert result is True
    assert len(dog.tasks) == initial_count - 1


def test_get_pending_tasks_excludes_complete(sample_owner):
    """get_pending_tasks() should exclude completed tasks."""
    dog = sample_owner.pets[0]
    dog.tasks[0].mark_complete()
    pending = dog.get_pending_tasks()
    assert all(not t.is_complete for t in pending)


# ── Owner Tests ────────────────────────────────────────────────────────────────

def test_get_all_tasks_returns_all(sample_owner):
    """Owner.get_all_tasks() should return tasks from every pet."""
    all_tasks = sample_owner.get_all_tasks()
    total = sum(len(p.tasks) for p in sample_owner.pets)
    assert len(all_tasks) == total


def test_add_and_remove_pet(sample_owner):
    """Owner should correctly add and remove pets by name."""
    new_pet = Pet("Goldie", "Fish", 1)
    sample_owner.add_pet(new_pet)
    assert len(sample_owner.pets) == 3

    removed = sample_owner.remove_pet("Goldie")
    assert removed is True
    assert len(sample_owner.pets) == 2


# ── Scheduler Tests ────────────────────────────────────────────────────────────

def test_sort_by_time_returns_chronological_order(sample_owner):
    """sort_by_time() should return tasks ordered earliest to latest."""
    scheduler = Scheduler(sample_owner)
    sorted_tasks = scheduler.sort_by_time()
    times = [t.time for t in sorted_tasks]
    assert times == sorted(times)


def test_filter_by_pet_name(sample_owner):
    """filter_tasks(pet_name) should only return tasks for that pet."""
    scheduler = Scheduler(sample_owner)
    rex_tasks = scheduler.filter_tasks(pet_name="Rex")
    assert all(t.pet_name == "Rex" for t in rex_tasks)


def test_filter_by_status_pending(sample_owner):
    """filter_tasks(status='pending') should only return incomplete tasks."""
    scheduler = Scheduler(sample_owner)
    # Complete one task first
    sample_owner.pets[0].tasks[0].mark_complete()
    pending = scheduler.filter_tasks(status="pending")
    assert all(not t.is_complete for t in pending)


def test_detect_conflicts_finds_same_time(sample_owner):
    """detect_conflicts() should flag tasks scheduled at identical times."""
    scheduler = Scheduler(sample_owner)
    # Rex Walk and Luna Meds are both at 08:00
    warnings = scheduler.detect_conflicts()
    assert len(warnings) >= 1
    assert any("08:00" in w for w in warnings)


def test_detect_conflicts_empty_when_no_overlap():
    """detect_conflicts() should return no warnings with no time overlaps."""
    owner = Owner("Solo", "solo@test.com")
    pet = Pet("Pip", "Bird", 1)
    pet.add_task(Task("Feed", "07:00", "daily", "Pip", date.today()))
    pet.add_task(Task("Play", "09:00", "daily", "Pip", date.today()))
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    assert scheduler.detect_conflicts() == []


def test_no_tasks_pet(sample_owner):
    """A pet with no tasks should not cause errors in scheduling."""
    empty_pet = Pet("Ghost", "Hamster", 1)
    sample_owner.add_pet(empty_pet)
    scheduler = Scheduler(sample_owner)
    # Should not raise any exceptions
    result = scheduler.sort_by_time()
    assert isinstance(result, list)
