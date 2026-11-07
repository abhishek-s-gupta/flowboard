# Flowboard — UI Interactive Elements Checklist & Test Matrix

This document provides a strict, exhaustive inventory of all visible interactive elements across all pages in Flowboard, their expected behavior, and verification status.

## 1. Landing Page (`/`)
| Element ID / Selector | Element Type | Expected Behaviour | Status |
|---|---|---|---|
| `#landingLoginForm` | Form | Client-side validation + server authentication | Tested |
| `#id_username` | Input | Focuses, accepts text input | Tested |
| `#id_password` | Input | Accepts password masked input | Tested |
| `#landingLoginBtn` | Button | Submits credentials, redirects to `/projects/` | Tested |
| `#linkGoToRegister` | Link | Navigates to `/accounts/register/` | Tested |

## 2. Authentication Pages (`/accounts/login/`, `/accounts/register/`)
| Element ID / Selector | Element Type | Expected Behaviour | Status |
|---|---|---|---|
| `#loginForm` | Form | Submits authentication credentials | Tested |
| `#btnLoginSubmit` | Button | Submits login, validates credentials | Tested |
| `#btnFillDemoCredentials` | Button | Fills `alex` / `password123` into form fields | Tested |
| `#linkRegister` | Link | Navigates to `/accounts/register/` | Tested |
| `#registerForm` | Form | Validates fields (unique username, email, passwords match) | Tested |
| `#btnRegisterSubmit` | Button | Creates account, logs in, redirects to `/projects/` | Tested |
| `#linkLogin` | Link | Navigates back to `/accounts/login/` | Tested |
| `#btnLogout` | Link/Button | Terminates session, redirects to `/accounts/login/` | Tested |

## 3. Global Top Bar & Sidebar (Present on all Authenticated Pages)
| Element ID / Selector | Element Type | Expected Behaviour | Status |
|---|---|---|---|
| `#navBrandLink` | Link | Navigates to `/projects/` | Tested |
| `#navMyTasks` | Link | Navigates to `/my-tasks/` | Tested |
| `#navNotifications` | Link | Navigates to `/notifications/` | Tested |
| `#navAllProjects` | Link | Navigates to `/projects/` | Tested |
| `#btnOpenNewProjectModal` | Button | Opens Create Project modal | Tested |
| `#sidebarUserProfileLink` | Link | Navigates to `/accounts/profile/` | Tested |
| `#sidebarProjectsList a` | Links | Navigates directly to project board | Tested |
| `#globalSearchInput` | Input | Submits search query on Enter, navigates to `/search/?q=...` | Tested |
| `#themeToggleBtn` | Button | Toggles `data-theme` between `light` and `dark` | Tested |
| `#notificationBellBtn` | Button | Toggles `#notificationsDropdown` | Tested |
| `#btnMarkAllReadDropdown` | Button | Marks all notifications read, clears badge | Tested |
| `#btnViewAllNotifications` | Link | Navigates to `/notifications/` | Tested |
| `#topbarProfileAvatar` | Link | Navigates to `/accounts/profile/` | Tested |

## 4. Projects List Page (`/projects/`)
| Element ID / Selector | Element Type | Expected Behaviour | Status |
|---|---|---|---|
| `#btnCreateProjectTop` | Button | Opens Create Project modal | Tested |
| `.project-card-item a` | Link | Navigates to project board | Tested |
| `[id^="btnOpenBoard-"]` | Link | Opens specific project board | Tested |
| `[id^="projSettingsBtn-"]` | Link | Opens specific project settings | Tested |

## 5. Project Board Page (`/projects/<id>/`)
| Element ID / Selector | Element Type | Expected Behaviour | Status |
|---|---|---|---|
| `#btnProjectSettings` | Link | Navigates to `/projects/<id>/settings/` | Tested |
| `#boardCardFilterInput` | Input | Filters cards in real time as user types | Tested |
| `#boardAssigneeFilter` | Select | Filters cards by selected assignee | Tested |
| `#boardPriorityFilter` | Select | Filters cards by selected priority | Tested |
| `#boardLabelFilter` | Select | Filters cards by selected label | Tested |
| `#btnAddNewColumn` | Button | Opens Add Column modal | Tested |
| `#btnAddNewColumnEnd` | Button | Opens Add Column modal | Tested |
| `.btn-rename-col` | Button | Opens Rename Column modal | Tested |
| `.btn-delete-col` | Button | Confirms and deletes column + cards | Tested |
| `.btn-show-add-card` | Button | Shows inline textarea in column footer | Tested |
| `.btn-submit-add-card` | Button | Creates card in column via fetch() without reload | Tested |
| `.btn-cancel-add-card` | Button | Cancels inline add card form | Tested |
| `.task-card` | Draggable | Drags and drops card between columns, saves position | Tested |
| `.task-card` (Click) | Interactive | Opens Task Detail Drawer panel | Tested |
| `#btnCloseDrawer` | Button | Closes Task Detail Drawer panel | Tested |
| `#taskDrawerTitleInput` | Input | Edits task title, saves on blur / enter | Tested |
| `#taskDrawerColumnSelect` | Select | Moves task to selected column | Tested |
| `#taskDrawerAssigneeSelect` | Select | Assigns member, sends notification if changed | Tested |
| `#taskDrawerPrioritySelect` | Select | Updates task priority dot and metadata | Tested |
| `#taskDrawerDueDateInput` | Input | Sets / updates task due date | Tested |
| `.task-drawer-label-cb` | Checkboxes | Toggles label tags on card | Tested |
| `#btnSaveTaskDesc` | Button | Saves updated description via JSON API | Tested |
| `#btnSubmitNewComment` | Button | Posts new comment, handles @mentions | Tested |
| `.btn-delete-comment` | Button | Deletes comment (own comments or owner) | Tested |
| `#btnDeleteTaskInDrawer` | Button | Confirms and deletes task | Tested |

## 6. Project Settings Page (`/projects/<id>/settings/`)
| Element ID / Selector | Element Type | Expected Behaviour | Status |
|---|---|---|---|
| `#projectSettingsForm` | Form | Updates project title, description, and color | Tested |
| `#btnSaveProjectSettings` | Button | Saves project settings | Tested |
| `#inviteMemberForm` | Form | Invites user by username/email, assigns role | Tested |
| `#btnInviteMemberSubmit` | Button | Sends invitation, dispatches real-time notification | Tested |
| `.btn-remove-member` | Button | Removes member from project | Tested |
| `#btnDeleteProjectSubmit` | Button | Confirms and permanently deletes project (Owner only) | Tested |

## 7. My Tasks Page (`/my-tasks/`)
| Element ID / Selector | Element Type | Expected Behaviour | Status |
|---|---|---|---|
| `#myTasksSearchInput` | Input | Filters tasks by search query | Tested |
| `#myTasksProjectFilter` | Select | Filters tasks by specific project | Tested |
| `#myTasksPriorityFilter` | Select | Filters tasks by priority | Tested |
| `#btnClearMyTasksFilters` | Link | Clears active filters | Tested |
| `[id^="taskRowLink-"]` | Link | Navigates to project board with drawer open | Tested |

## 8. Notifications Page (`/notifications/`)
| Element ID / Selector | Element Type | Expected Behaviour | Status |
|---|---|---|---|
| `#tabAllNotifications` | Link | Shows all notifications | Tested |
| `#tabUnreadNotifications` | Link | Filters unread notifications | Tested |
| `#btnMarkAllReadPage` | Button | Marks all notifications as read | Tested |
| `[id^="btnMarkRead-"]` | Button | Marks single notification as read | Tested |

## 9. Profile Settings Page (`/accounts/profile/`)
| Element ID / Selector | Element Type | Expected Behaviour | Status |
|---|---|---|---|
| `#profileForm` | Form | Updates display name, theme, and avatar | Tested |
| `#btnSaveProfile` | Button | Saves profile changes | Tested |
| `#btnCancelProfile` | Link | Returns to `/projects/` | Tested |
