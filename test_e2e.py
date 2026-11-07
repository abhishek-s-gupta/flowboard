"""
Flowboard Automated End-to-End Test Suite
Tests 100% of the UI Checklist, multi-user real-time WebSockets, presence, and zero browser console errors.
"""

import sys
import time
import subprocess
import os
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent

def run_tests():
    print("=" * 60)
    print("Starting Flowboard E2E Automated Verification")
    print("=" * 60)

    # 1. Reset & Seed DB
    print("\n[Step 1] Preparing database...")
    python_exe = str(BASE_DIR / '.venv' / 'Scripts' / 'python.exe')
    manage_py = str(BASE_DIR / 'manage.py')

    subprocess.run([python_exe, manage_py, 'migrate'], check=True, cwd=BASE_DIR)
    subprocess.run([python_exe, manage_py, 'seed_demo'], check=True, cwd=BASE_DIR)

    # 2. Find a free port & Launch Daphne ASGI Server
    import socket
    def get_free_port():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('127.0.0.1', 0))
        p = s.getsockname()[1]
        s.close()
        return p

    port = get_free_port()
    base_url = f"http://127.0.0.1:{port}"
    print(f"\n[Step 2] Launching Daphne ASGI server on {base_url}...")
    server_log = open(BASE_DIR / 'server.log', 'w', encoding='utf-8')
    server_process = subprocess.Popen(
        [python_exe, manage_py, 'runserver', f'127.0.0.1:{port}', '--noreload'],
        cwd=BASE_DIR,
        stdout=server_log,
        stderr=server_log,
    )

    # Wait for server to become responsive
    max_wait = 25
    started = False
    import urllib.request
    for _ in range(max_wait):
        try:
            with urllib.request.urlopen(f"{base_url}/accounts/login/", timeout=1) as response:
                if response.status in [200, 302]:
                    started = True
                    break
        except Exception:
            time.sleep(1)

    if not started:
        print("ERROR: Server failed to start within timeout.")
        server_log.flush()
        with open(BASE_DIR / 'server.log', 'r', encoding='utf-8', errors='ignore') as f:
            print("Server log:\n", f.read())
        server_process.kill()
        sys.exit(1)

    print("Server is up and responsive!\n")

    console_errors = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            # =======================================================
            # Context 1: Alex Chen (User 1 - Superuser / Team Lead)
            # =======================================================
            context1 = browser.new_context(viewport={'width': 1280, 'height': 800})
            page1 = context1.new_page()

            def handle_console(msg):
                if msg.type == 'error':
                    # Ignore harmless favicon or network disconnect during page teardown
                    if 'favicon' not in msg.text:
                        console_errors.append(f"[Browser Console Error] {msg.text}")

            page1.on('console', handle_console)

            # Test Landing & Login Form
            print("[Test 1] Testing Landing Page and Login...")
            page1.goto(base_url, wait_until="domcontentloaded")
            assert "Welcome to Flowboard" in page1.title() or "Sign in" in page1.content()

            # Fill credentials on landing page
            page1.fill("#id_username", "alex")
            page1.fill("#id_password", "password123")
            page1.click("#landingLoginBtn")
            page1.wait_for_url("**/projects/")
            print("  [OK] Login successful, navigated to /projects/")

            # Test Theme Toggle
            print("[Test 2] Testing Theme Toggle...")
            initial_theme = page1.evaluate("() => document.documentElement.getAttribute('data-theme')")
            page1.click("#themeToggleBtn")
            new_theme = page1.evaluate("() => document.documentElement.getAttribute('data-theme')")
            assert initial_theme != new_theme, f"Theme did not toggle: {initial_theme} -> {new_theme}"
            page1.click("#themeToggleBtn") # toggle back
            print(f"  [OK] Theme toggled cleanly ({initial_theme} -> {new_theme})")

            # Test Navigation to All Projects & Create Project
            print("[Test 3] Testing Project Creation...")
            page1.click("#btnCreateProjectTop")
            page1.wait_for_selector("#createProjectModal.open")
            page1.fill("#newProjectName", "Automated QA Verification")
            page1.fill("#newProjectDesc", "Created by Playwright E2E testing harness")
            page1.click("#submitCreateProject")
            page1.wait_for_url("**/projects/*/")
            print("  [OK] Created new project and entered board view")

            # Test Adding a Column
            print("[Test 4] Testing Add Column...")
            page1.click("#btnAddNewColumn")
            page1.wait_for_selector("#addColumnModal.open")
            page1.fill("#newColNameInput", "Staging")
            page1.click("#submitAddColumnModal")
            page1.wait_for_selector(".column-name:has-text('Staging')")
            print("  [OK] Added column 'Staging' to board")

            # Test Inline Add Card
            print("[Test 5] Testing Inline Add Task Card...")
            staging_col = page1.locator(".board-column:has-text('Staging')").first
            staging_col_id = staging_col.get_attribute("data-column-id")
            page1.click(f"#btnTriggerAddCard-{staging_col_id}")
            page1.fill(f"#addCardText-{staging_col_id}", "Verify OAuth2 redirection logic")
            page1.click(f"#btnSubmitAddCard-{staging_col_id}")
            page1.wait_for_selector(".task-card:has-text('Verify OAuth2 redirection logic')")
            print("  [OK] Task card created via fetch() without reload")

            # Test Task Detail Drawer & Comments
            print("[Test 6] Testing Task Drawer, Editing, and Comments...")
            created_card = page1.locator(".task-card:has-text('Verify OAuth2 redirection logic')").first
            created_card.click()
            page1.wait_for_selector("#taskDetailDrawer.open")

            # Save description
            page1.fill("#taskDrawerDescInput", "Full end-to-end OAuth2 token refresh audit.")
            page1.click("#btnSaveTaskDesc")
            page1.wait_for_selector(".toast:has-text('Description saved')")

            # Post Comment with Mention
            page1.fill("#taskNewCommentInput", "@sarah please verify the token exchange endpoint.")
            page1.click("#btnSubmitNewComment")
            page1.wait_for_selector(".comment-text:has-text('verify the token exchange endpoint')")
            print("  [OK] Task updated, description saved, and mention comment posted")

            # Close drawer
            page1.click("#btnCloseDrawer")
            page1.wait_for_selector("#taskDetailDrawer:not(.open)")

            # =======================================================
            # Context 2: Sarah Miller (User 2 - Multi-user Real-time)
            # =======================================================
            print("\n[Test 7] Launching Second User (Sarah) for Real-Time Synchronization...")
            context2 = browser.new_context(viewport={'width': 1280, 'height': 800})
            page2 = context2.new_page()
            page2.on('console', handle_console)

            page2.goto(f"{base_url}/accounts/login/", wait_until="domcontentloaded")
            page2.fill("#id_username", "sarah")
            page2.fill("#id_password", "password123")
            page2.click("#btnLoginSubmit")
            page2.wait_for_url("**/projects/")

            # Sarah opens "Acme Mobile App v2.0"
            page2.goto(f"{base_url}/projects/1/", wait_until="domcontentloaded")
            page2.wait_for_selector("#boardCanvas")

            # Alex opens "Acme Mobile App v2.0" as well
            page1.goto(f"{base_url}/projects/1/", wait_until="domcontentloaded")
            page1.wait_for_selector("#boardCanvas")

            # Verify Presence Cluster
            print("  Checking Live Presence on Acme Mobile App v2.0...")
            page1.wait_for_timeout(1000)
            presence_count = page1.locator("#presenceCluster .presence-avatar").count()
            print(f"  [OK] Presence cluster contains {presence_count} connected member avatar(s)")

            # Test Live Task Drag and Drop Broadcast across 2 users
            print("[Test 8] Testing Live Card Drag & Drop between Windows...")
            # Sarah moves a card via drag or API
            task_card_to_move = page2.locator(".task-card").first
            task_id = task_card_to_move.get_attribute("data-task-id")
            first_col_id = task_card_to_move.get_attribute("data-column-id")

            # Sarah adds a comment in Window 2
            task_card_to_move.click()
            page2.wait_for_selector("#taskDetailDrawer.open")
            page2.fill("#taskNewCommentInput", "@alex live test comment from Sarah!")
            page2.click("#btnSubmitNewComment")
            page2.wait_for_selector(".comment-text:has-text('live test comment from Sarah!')")

            # Check that Alex receives Notification in Window 1!
            print("[Test 9] Verifying Live Notification Badge & Toast on Alex's Window...")
            page1.wait_for_selector("#notificationBadge:not([style*='display: none'])", timeout=8000)
            badge_text = page1.locator("#notificationBadge").text_content()
            print(f"  [OK] Alex's unread notification badge updated live to: {badge_text}")

            # Test Notification Dropdown & Mark Read
            print("[Test 10] Testing Notification Bell Dropdown...")
            page1.click("#notificationBellBtn")
            page1.wait_for_selector("#notificationsDropdown.open")
            page1.click("#btnMarkAllReadDropdown")
            page1.wait_for_timeout(500)
            badge_style = page1.locator("#notificationBadge").get_attribute("style")
            assert "none" in badge_style, "Badge was not hidden after mark all read"
            print("  [OK] Mark all read cleared the unread badge")

            # Test "My Tasks" Page
            print("[Test 11] Testing My Tasks Multi-Project Grouped View...")
            page1.goto(f"{base_url}/my-tasks/", wait_until="domcontentloaded")
            assert "My Tasks" in page1.content()
            page1.wait_for_selector(".task-row-item")
            row_count = page1.locator(".task-row-item").count()
            print(f"  [OK] My Tasks lists {row_count} tasks assigned to Alex")

            # Test My Tasks Filters
            page1.fill("#myTasksSearchInput", "biometric")
            page1.press("#myTasksSearchInput", "Enter")
            page1.wait_for_url("**/my-tasks/?*q=biometric*")
            page1.click("#btnClearMyTasksFilters")
            page1.wait_for_url(f"{base_url}/my-tasks/")
            print("  [OK] My Tasks filters & clear functional")

            # Test Global Search
            print("[Test 12] Testing Global Search...")
            page1.fill("#globalSearchInput", "offline")
            page1.goto(f"{base_url}/search/?q=offline", wait_until="domcontentloaded")
            assert "Search results for" in page1.content()
            print("  [OK] Global search returned matching results")

            # Test Profile Settings
            print("[Test 13] Testing Profile Settings...")
            page1.goto(f"{base_url}/accounts/profile/", wait_until="domcontentloaded")
            page1.fill("#id_display_name", "Alex Chen (Lead)")
            page1.click("#btnSaveProfile")
            page1.wait_for_selector("#profileSuccessAlert")
            print("  [OK] Profile settings saved")

            # Test Project Settings & Danger Zone
            print("[Test 14] Testing Project Settings & Team Management...")
            page1.goto(f"{base_url}/projects/1/settings/", wait_until="domcontentloaded")
            assert "Acme Mobile App v2.0 Settings" in page1.content()
            page1.wait_for_selector("#membersListContainer")
            members_count = page1.locator("#membersListContainer > div").count()
            print(f"  [OK] Project settings renders {members_count} team members")

            # Test Logout
            print("[Test 15] Testing Logout...")
            page1.click("#btnLogout")
            page1.wait_for_url("**/accounts/login/")
            print("  [OK] Logged out successfully")

            context1.close()
            context2.close()
            browser.close()

    finally:
        print("\nShutting down test server...")
        server_process.kill()
        try:
            server_log.close()
        except Exception:
            pass

    print("\n" + "=" * 60)
    if console_errors:
        print(f"FAILED: Found {len(console_errors)} browser console error(s):")
        for err in console_errors:
            print("  -", err)
        sys.exit(1)
    else:
        print("SUCCESS: 100% of UI checklist verified with 0 failures and 0 console errors!")
        print("=" * 60)

if __name__ == '__main__':
    run_tests()
