# import streamlit as st

# st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# st.title("🐾 PawPal+")

# st.markdown(
#     """
# Welcome to the PawPal+ starter app.

# This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
# but **it does not implement the project logic**. Your job is to design the system and build it.

# Use this app as your interactive demo once your backend classes/functions exist.
# """
# )

# with st.expander("Scenario", expanded=True):
#     st.markdown(
#         """
# **PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
# for their pet(s) based on constraints like time, priority, and preferences.

# You will design and implement the scheduling logic and connect it to this Streamlit UI.
# """
#     )

# with st.expander("What you need to build", expanded=True):
#     st.markdown(
#         """
# At minimum, your system should:
# - Represent pet care tasks (what needs to happen, how long it takes, priority)
# - Represent the pet and the owner (basic info and preferences)
# - Build a plan/schedule for a day that chooses and orders tasks based on constraints
# - Explain the plan (why each task was chosen and when it happens)
# """
#     )

# st.divider()

# st.subheader("Quick Demo Inputs (UI only)")
# owner_name = st.text_input("Owner name", value="Jordan")
# pet_name = st.text_input("Pet name", value="Mochi")
# species = st.selectbox("Species", ["dog", "cat", "other"])

# st.markdown("### Tasks")
# st.caption("Add a few tasks. In your final version, these should feed into your scheduler.")

# if "tasks" not in st.session_state:
#     st.session_state.tasks = []

# col1, col2, col3 = st.columns(3)
# with col1:
#     task_title = st.text_input("Task title", value="Morning walk")
# with col2:
#     duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
# with col3:
#     priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

# if st.button("Add task"):
#     st.session_state.tasks.append(
#         {"title": task_title, "duration_minutes": int(duration), "priority": priority}
#     )

# if st.session_state.tasks:
#     st.write("Current tasks:")
#     st.table(st.session_state.tasks)
# else:
#     st.info("No tasks yet. Add one above.")

# st.divider()

# st.subheader("Build Schedule")
# st.caption("This button should call your scheduling logic once you implement it.")

# if st.button("Generate schedule"):
#     st.warning(
#         "Not implemented yet. Next step: create your scheduling logic (classes/functions) and call it here."
#     )
#     st.markdown(
#         """
# Suggested approach:
# 1. Design your UML (draft).
# 2. Create class stubs (no logic).
# 3. Implement scheduling behavior.
# 4. Connect your scheduler here and display results.
# """
#     )



"""
app.py — Streamlit UI for PawPal+
Run with: streamlit run app.py
"""

import streamlit as st
from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

# ── Session State Initialization ───────────────────────────────────────────────
# st.session_state acts as a persistent dictionary for the current browser session.
# We check before creating so we don't reset the owner on every page interaction.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="My Pet Family", email="owner@pawpal.com")

owner: Owner = st.session_state.owner
scheduler = Scheduler(owner)

# ── Sidebar — Owner Setup ──────────────────────────────────────────────────────
st.sidebar.title("🐾 PawPal+")
st.sidebar.markdown("---")

with st.sidebar.expander("⚙️ Owner Settings", expanded=False):
    new_name = st.text_input("Owner Name", value=owner.name)
    new_email = st.text_input("Email", value=owner.email)
    if st.button("Update Owner"):
        owner.name = new_name
        owner.email = new_email
        st.success("Owner updated!")

# ── Main Header ────────────────────────────────────────────────────────────────
st.title("🐾 PawPal+ Pet Care Manager")
st.caption(f"Welcome, **{owner.name}** | {date.today().strftime('%A, %B %d %Y')}")

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📋 Schedule", "🐶 Pets & Tasks", "➕ Add", "⚙️ Manage"])

# ══ TAB 1: Today's Schedule ════════════════════════════════════════════════════
with tab1:
    st.subheader("Today's Schedule")

    conflicts = scheduler.detect_conflicts()
    if conflicts:
        for w in conflicts:
            st.warning(w)

    all_tasks = scheduler.sort_by_time()
    if not all_tasks:
        st.info("No tasks yet. Add some pets and tasks to get started!")
    else:
        # Filter controls
        col1, col2 = st.columns(2)
        with col1:
            pet_names = ["All"] + [p.name for p in owner.pets]
            selected_pet = st.selectbox("Filter by Pet", pet_names)
        with col2:
            status_filter = st.selectbox("Filter by Status", ["All", "Pending", "Complete"])

        # Apply filters
        filtered = scheduler.filter_tasks(
            pet_name=None if selected_pet == "All" else selected_pet,
            status=None if status_filter == "All" else status_filter.lower(),
        )

        if not filtered:
            st.info("No tasks match your filters.")
        else:
            for task in sorted(filtered, key=lambda t: t.time):
                col_a, col_b, col_c, col_d, col_e = st.columns([1, 2, 3, 2, 2])
                status_icon = "✅" if task.is_complete else "⏳"
                col_a.write(status_icon)
                col_b.write(f"**{task.time}**")
                col_c.write(task.description)
                col_d.write(f"🐾 {task.pet_name}")
                col_e.write(f"_{task.frequency}_")

                if not task.is_complete:
                    if st.button(f"Mark Done — {task.description} ({task.pet_name})", key=f"done_{id(task)}"):
                        next_task = task.mark_complete()
                        if next_task:
                            for pet in owner.pets:
                                if pet.name == task.pet_name:
                                    pet.add_task(next_task)
                            st.success(f"✅ Done! Next '{task.description}' scheduled for {next_task.due_date}.")
                        else:
                            st.success(f"✅ '{task.description}' marked complete.")
                        st.rerun()

# ══ TAB 2: Pets Overview ═══════════════════════════════════════════════════════
with tab2:
    st.subheader("Your Pets")
    if not owner.pets:
        st.info("No pets added yet.")
    else:
        for pet in owner.pets:
            with st.expander(f"🐾 {pet.name} ({pet.species}, {pet.age} yrs)"):
                pending = pet.get_pending_tasks()
                completed = [t for t in pet.tasks if t.is_complete]

                st.metric("Total Tasks", len(pet.tasks))
                col1, col2 = st.columns(2)
                col1.metric("Pending", len(pending))
                col2.metric("Completed", len(completed))

                if pet.tasks:
                    st.markdown("**All Tasks:**")
                    for task in sorted(pet.tasks, key=lambda t: t.time):
                        icon = "✅" if task.is_complete else "⏳"
                        st.write(f"{icon} `{task.time}` — {task.description} _{task.frequency}_")

# ══ TAB 3: Add Pets & Tasks ════════════════════════════════════════════════════
with tab3:
    col_left, col_right = st.columns(2)

    # Add a Pet
    with col_left:
        st.subheader("🐶 Add a Pet")
        pet_name = st.text_input("Pet Name")
        pet_species = st.selectbox("Species", ["Dog", "Cat", "Bird", "Rabbit", "Fish", "Other"])
        pet_age = st.number_input("Age (years)", min_value=0, max_value=30, value=1)

        if st.button("Add Pet"):
            if pet_name.strip():
                new_pet = Pet(name=pet_name.strip(), species=pet_species, age=pet_age)
                owner.add_pet(new_pet)
                st.success(f"🎉 {pet_name} added!")
                st.rerun()
            else:
                st.error("Pet name cannot be empty.")

    # Add a Task
    with col_right:
        st.subheader("📅 Schedule a Task")
        if not owner.pets:
            st.info("Add a pet first before scheduling tasks.")
        else:
            task_pet = st.selectbox("Assign to Pet", [p.name for p in owner.pets])
            task_desc = st.text_input("Task Description", placeholder="e.g. Morning Walk")
            task_time = st.time_input("Time")
            task_freq = st.selectbox("Frequency", ["once", "daily", "weekly"])
            task_date = st.date_input("Date", value=date.today())

            if st.button("Add Task"):
                if task_desc.strip():
                    new_task = Task(
                        description=task_desc.strip(),
                        time=task_time.strftime("%H:%M"),
                        frequency=task_freq,
                        pet_name=task_pet,
                        due_date=task_date,
                    )
                    for pet in owner.pets:
                        if pet.name == task_pet:
                            pet.add_task(new_task)
                    st.success(f"✅ '{task_desc}' scheduled for {task_pet}!")
                    st.rerun()
                else:
                    st.error("Task description cannot be empty.")

# ══ TAB 4: Manage ══════════════════════════════════════════════════════════════
with tab4:
    st.subheader("🗑️ Remove a Pet")
    if owner.pets:
        pet_to_remove = st.selectbox("Select Pet to Remove", [p.name for p in owner.pets])
        if st.button("Remove Pet", type="primary"):
            owner.remove_pet(pet_to_remove)
            st.success(f"Removed {pet_to_remove}.")
            st.rerun()
    else:
        st.info("No pets to remove.")

    st.markdown("---")
    st.subheader("🔄 Reset All Data")
    if st.button("⚠️ Reset Everything", type="primary"):
        st.session_state.owner = Owner(name="My Pet Family", email="owner@pawpal.com")
        st.success("All data has been reset.")
        st.rerun()