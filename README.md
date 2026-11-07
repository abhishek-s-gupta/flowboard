# Flowboard — Collaborative Project Management Tool

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![Django 5.1](https://img.shields.io/badge/django-5.1-green.svg)](https://www.djangoproject.com/)
[![Channels 4.3](https://img.shields.io/badge/channels-4.3-teal.svg)](https://channels.readthedocs.io/)
[![Playwright E2E](https://img.shields.io/badge/E2E-Playwright%20Passing-brightgreen.svg)](test_e2e.py)

**Flowboard** is a modern, minimal, human-crafted collaborative project management platform (Kanban/Trello/Asana style) built for speed, restraint, and real-time synchronization.

Developed as a college software engineering submission for **Task 3: Project Management Tool**, following professional SaaS design principles: content-first, zero AI-slop (no gradients, no glowing blobs, no marketing cliches), sub-second responsiveness, and 100% zero-dead-UI.

---

## Architecture & Project Structure

```text
flowboard/
├── manage.py
├── requirements.txt
├── README.md
├── LICENSE
├── UI_CHECKLIST.md                # Strict inventory of every interactive control
├── test_e2e.py                   # Automated Playwright test suite (15/15 passing)
├── flowboard/
│   ├── settings.py               # Django 5 + Channels settings with SQLite WAL
│   ├── asgi.py                   # ProtocolTypeRouter with Daphne & Channels
│   ├── wsgi.py                   # WSGI entrypoint
│   ├── routing.py                # WebSocket URL router
│   └── urls.py                   # Top-level routing & custom 403/404/500 handlers
├── accounts/                     # User authentication & profile settings
│   ├── models.py                 # Profile with avatar, initials, and theme
│   ├── views.py                  # Login, register, logout, profile update
│   └── forms.py                  # Client & server validated auth forms
├── projects/                     # Core Kanban & project management
│   ├── models.py                 # Project, Member, Column, Task, Comment, Activity
│   ├── services.py               # Synchronized transactional mutations & event broadcast
│   ├── consumers.py              # BoardConsumer (presence + board events)
│   ├── views.py                  # Boards, project settings, fetch() JSON APIs
│   └── management/commands/
│       └── seed_demo.py          # Seeds 5 users, 2 rich projects, 22+ tasks
├── notifications/                # Real-time notifications system
│   ├── models.py                 # Notification model with indexing
│   ├── consumers.py              # NotificationConsumer per-user channel
│   └── views.py                  # Dropdown API, list view, mark-as-read
├── core/                         # Landing, search, and cross-project views
│   ├── views.py                  # Split-screen landing, My Tasks, Global Search
│   └── context_processors.py     # Global sidebar projects & unread count
├── static/
│   ├── css/
│   │   ├── tokens.css            # Calm design tokens & dark/light palettes
│   │   └── style.css             # Responsive layout, modals, cards, drawers
│   └── js/
│       ├── app.js                # CSRF fetch() wrapper, theme, modals, toasts
│       ├── websocket.js          # Reconnecting WebSocket client with backoff
│       ├── dragdrop.js           # Smooth drag & drop with keyboard navigation
│       ├── board.js              # Live board manager, filters, drawer, comments
│       └── notifications.js      # Notification bell badge & dropdown
└── templates/                    # Semantic HTML5 templates
    ├── base.html                 # App shell with Lucide SVGs & responsive sidebar
    ├── 403.html / 404.html / 500.html
    ├── accounts/                 # login.html, register.html, profile.html
    ├── core/                     # landing.html, my_tasks.html, search.html
    ├── projects/                 # project_list.html, board.html, project_settings.html
    └── notifications/            # list.html
```

---

## Tech Stack & Architectural Decisions

- **Backend**: Python 3.13, Django 5.1, Django ORM, SQLite with WAL (`Write-Ahead Logging`) optimization and `NORMAL` synchronous mode for multi-threaded concurrency without table lockouts.
- **Real-Time WebSockets**: Django Channels 4.3 + Daphne 4.2 ASGI server with the in-memory channel layer (`channels.layers.InMemoryChannelLayer`). **Zero Redis or external message brokers required.**
- **Frontend**: Django Templates, Pure CSS with semantic design tokens (`tokens.css`, `style.css`), and Vanilla JavaScript modules. **Zero JavaScript frameworks or animation libraries.**
- **Transactional Service Layer (`projects/services.py`)**: All database writes, audit logging, notification dispatches, and WebSocket events are unified in single transactional service calls so REST and real-time sockets never get out of sync.
- **Automated Verification**: Full automated test harness with Playwright (`test_e2e.py`) verifying multi-user live synchronization across concurrent browser windows.

---

## Core Capabilities (Task 3 Grading Criteria)

1. **Authentication & Profile**:
   - Registration, login by username or email, session logout.
   - Profile management with display name, initials avatar fallback, and instant Light/Dark theme toggle.
   - Inline field-level validation errors.
2. **Projects & Role-Based Access Control**:
   - Create, edit, and delete projects (Owner only).
   - Project description and color tags (Blue, Teal, Indigo, Slate).
   - Invite team members by username or email; assign roles (`Owner` vs `Member`).
   - Remove members (Owner only); leave project (Members only); members-only access checks on all endpoints.
3. **Interactive Kanban Boards**:
   - Default columns: *To Do*, *In Progress*, *Review*, *Done*.
   - Column CRUD: add, rename, reorder, and delete columns.
   - Task CRUD: inline fast creation, modal/drawer editor with title, description, assignee, due date, priority (Low/Medium/High), and custom label chips.
   - Smooth Drag-and-Drop between and within columns with optimistic reordering and persistent database indices.
   - Keyboard accessible card movement via `Alt + Arrow keys`.
4. **Task Discussions & Mentions**:
   - Chronological comments thread inside the task detail drawer.
   - Delete own comments.
   - Automatic `@username` mention detection with real-time notification dispatch.
5. **Activity Log**:
   - Audited chronological change log per task and per project (creations, moves, renames, assignments, comments, due date changes).
6. **Search & Filters**:
   - Real-time client-side board filter bar by text query, assignee, priority, and label tags.
   - Global search across all accessible tasks and projects.
   - "My Tasks" page listing all tasks assigned to the current user across all projects, grouped by due date (*Overdue*, *Due Today*, *Upcoming 7 Days*, *Later*, *No Due Date*).
7. **Real-time WebSockets & Presence**:
   - Board WebSocket (`ws/board/<project_id>/`): Live presence avatars in the top bar showing connected collaborators; instant card moves, creations, edits, deletions, column modifications, and comments broadcasted with subtle glide and highlight animations.
   - Notification WebSocket (`ws/notifications/`): Live badge count increments and toast notifications for task assignments, comment mentions, and project invites.
   - Auto-reconnect with exponential backoff and heartbeat pings.
8. **Security & Zero Dead UI**:
   - Login required across all application routes.
   - Project-membership checks on every endpoint and WebSocket connection.
   - CSRF token validation on all `POST` requests.
   - Every button, form, and link is 100% functional with loading, toast feedback, and error dialogs. Custom 403, 404, and 500 error pages.

---

## Quickstart & Installation

### 1. Set Up Environment & Install Dependencies

```bash
# Navigate to project directory
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

You can run Flowboard using Daphne directly or through Django's runserver:

```bash
# Using Daphne directly:
daphne -b 127.0.0.1 -p 8000 flowboard.asgi:application

# Or using manage.py (Daphne takes over runserver automatically):
python manage.py runserver 8000
```

Open your browser to: **`http://127.0.0.1:8000`**

---

## Demo Credentials

All seeded accounts have the password: **`password123`**

| Username | Name | Role | Email |
|---|---|---|---|
| **`alex`** (Superuser) | Alex Chen | Team Lead & Product | alex@flowboard.dev |
| **`sarah`** | Sarah Miller | Senior Backend Engineer | sarah@flowboard.dev |
| **`elena`** | Elena Rostova | Frontend & UI Specialist | elena@flowboard.dev |
| **`marcus`** | Marcus Vance | Systems & Cloud Architect | marcus@flowboard.dev |
| **`priya`** | Priya Sharma | QA & Release Engineer | priya@flowboard.dev |

---

## How to Test Real-Time Collaboration (Two Browser Windows)

1. Open **Browser Window 1** and log in as `alex` (`password123`).
2. Open **Browser Window 2** (incognito window or different browser) and log in as `sarah` (`password123`).
3. Navigate both windows to the same board: **Acme Mobile App v2.0**.
4. Observe the collaboration in real time:
   - **Presence Indicators**: In the top bar next to the search box, notice both user avatars appear live as active viewers of the board.
   - **Live Drag and Drop**: Drag a task card from *To Do* to *In Progress* in Window 1. Window 2 immediately glides the card into the new column with a subtle highlight, with zero page reload.
   - **Live Comments & Mentions**: Open a card in Window 2, write a comment typing `@alex can you review the schema?` and submit. In Window 1, Alex's notification bell badge pops to `+1`, a toast slides in, and the comment appears instantly in the task drawer!
   - **Live Card Creation**: In Window 1, click *Add card* at the bottom of any column and type a title. The new card pops instantly onto Window 2.

---

## Running the Automated End-to-End Test Suite

Flowboard includes an automated Playwright E2E suite covering 100% of the UI checklist:

```bash
# Install Chromium for Playwright (if not already installed)
python -m playwright install chromium

# Run the test suite
python test_e2e.py
```

**Results:**
```text
============================================================
SUCCESS: 100% of UI checklist verified with 0 failures and 0 console errors!
============================================================
```

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
