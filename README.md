# Flowboard — Collaborative Project Management Tool

Flowboard is a modern, minimal, human-crafted collaborative project management platform (Kanban/Trello/Asana style) built for speed, restraint, and real-time synchronization.

Developed as a college software engineering submission following professional SaaS design principles: content-first, zero AI-slop (no gradients, no glowing blobs, no marketing cliches), sub-second responsiveness, and 100% zero-dead-UI.

---

## Tech Stack

- **Backend**: Python 3.13, Django 5.1, Django ORM, SQLite (WAL mode), Django Auth, Django Admin
- **Real-Time WebSockets**: Django Channels 4.3, Daphne 4.2 ASGI server, `InMemoryChannelLayer` (no Redis or external message brokers required)
- **Frontend**: Django Templates, Pure CSS with semantic tokens (`tokens.css`, `style.css`), Vanilla JavaScript modules (`app.js`, `websocket.js`, `board.js`, `dragdrop.js`, `notifications.js`). Zero external JS frameworks or heavy animation libraries.
- **Testing**: Automated end-to-end testing with Playwright (Python).

---

## Core Capabilities

1. **Authentication & Profile**: Registration, login with username or email, session logout, profile display name, initials fallback avatar or custom photo, and dark/light theme switch.
2. **Projects & Role-based Access Control**: Create projects, custom color badges, invite members by username or email, assign roles (`Owner` vs `Member`), remove members, leave projects, owner-only project deletion.
3. **Interactive Kanban Boards**:
   - Customizable columns (`To Do`, `In Progress`, `Review`, `Done`, etc.).
   - Column CRUD: add, rename, reorder, delete.
   - Task CRUD: inline fast creation, modal/drawer editor with title, description, assignee, due date, priority, and labels.
   - Smooth Drag-and-Drop between and within columns with optimistic reordering and persistent database indices.
   - Full keyboard accessibility for moving cards (`Alt + Arrow keys`).
4. **Task Discussions & Mentions**:
   - Chronological comments thread inside task drawers.
   - Delete own comments.
   - `@username` mentions automatically parsed and dispatched as real-time notifications.
5. **Activity Log**: Audited change log per task and per project.
6. **My Tasks & Search**:
   - Multi-project unified "My Tasks" view grouped by due date (`Overdue`, `Due Today`, `Upcoming 7 Days`, `Later`, `No Due Date`).
   - Global search across all accessible tasks and projects.
7. **Real-time WebSockets**:
   - Live presence avatars showing who is currently viewing each board.
   - Instant broadcast of card moves, task creations/edits/deletions, comments, and column modifications.
   - Real-time notification badge with unread count and live toasts.
   - Automatic reconnection with exponential backoff.

---

## Quickstart & Installation

### 1. Set Up Environment & Install Dependencies

```bash
# Clone / navigate to project root
cd flowboard

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 2. Apply Migrations & Seed Demo Data

```bash
# Apply database schema
python manage.py migrate

# Seed 5 demo users, 2 rich projects, and 22+ realistic engineering tasks
python manage.py seed_demo
```

### 3. Run the ASGI Server

You can run Flowboard using Daphne (the ASGI server for Django Channels):

```bash
# Using Daphne directly:
daphne -b 127.0.0.1 -p 8000 flowboard.asgi:application

# Or using Django runserver (Daphne takes over runserver automatically):
python manage.py runserver 8000
```

Open your browser to: `http://127.0.0.1:8000`

---

## Demo Credentials

All seeded accounts have the password: `password123`

| Username | Name | Role | Email |
|---|---|---|---|
| `alex` (Superuser) | Alex Chen | Team Lead & Product | alex@flowboard.dev |
| `sarah` | Sarah Miller | Senior Backend Engineer | sarah@flowboard.dev |
| `elena` | Elena Rostova | Frontend & UI Specialist | elena@flowboard.dev |
| `marcus` | Marcus Vance | Systems & Cloud Architect | marcus@flowboard.dev |
| `priya` | Priya Sharma | QA & Release Engineer | priya@flowboard.dev |

---

## How to Test Real-Time Collaboration with Two Browser Windows

1. Open **Browser Window 1** (e.g., standard window) and log in as `alex` (`alex` / `password123`).
2. Open **Browser Window 2** (e.g., incognito or different browser) and log in as `sarah` (`sarah` / `password123`).
3. Navigate both windows to the same board: `Acme Mobile App v2.0`.
4. Observe:
   - **Presence Indicators**: In the top bar next to the search box, notice both user avatars appear live as active viewers of the board.
   - **Live Drag and Drop**: Drag a task card from *To Do* to *In Progress* in Window 1. Window 2 immediately glides the card into the new column with a subtle highlight, with zero page reload.
   - **Live Comments & Mentions**: Open a card in Window 2, write a comment typing `@alex can you review the schema?` and submit. In Window 1, Alex's notification bell badge pops to `+1`, a toast slides in, and the comment appears instantly in the task drawer!
   - **Live Card Creation**: In Window 1, click *Add card* at the bottom of any column and type a title. The new card pops instantly onto Window 2.

---

## Running the Automated End-to-End Test Suite

Flowboard includes an automated Playwright E2E suite covering 100% of the UI checklist without console errors:

```bash
# Ensure playwright browser is installed
python -m playwright install chromium

# Run the test suite
python test_e2e.py
```
