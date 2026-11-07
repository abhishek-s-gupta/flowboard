import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from accounts.models import Profile
from projects.models import Project, ProjectMember, Column, Label, Task, Comment, Activity
from notifications.models import Notification

class Command(BaseCommand):
    help = 'Seeds database with 5 demo users, 2 rich realistic projects, 22+ tasks, comments, activities and notifications.'

    def handle(self, *args, **options):
        self.stdout.write("Seeding Flowboard demo data...")

        # 1. Clear existing seed data if any (or update idempotently)
        # Create users
        users_data = [
            {'username': 'alex', 'name': 'Alex Chen', 'email': 'alex@flowboard.dev', 'is_superuser': True},
            {'username': 'sarah', 'name': 'Sarah Miller', 'email': 'sarah@flowboard.dev', 'is_superuser': False},
            {'username': 'elena', 'name': 'Elena Rostova', 'email': 'elena@flowboard.dev', 'is_superuser': False},
            {'username': 'marcus', 'name': 'Marcus Vance', 'email': 'marcus@flowboard.dev', 'is_superuser': False},
            {'username': 'priya', 'name': 'Priya Sharma', 'email': 'priya@flowboard.dev', 'is_superuser': False},
        ]

        users = {}
        for u in users_data:
            user, created = User.objects.get_or_create(username=u['username'], defaults={'email': u['email']})
            user.set_password('password123')
            user.is_staff = True
            if u['is_superuser']:
                user.is_superuser = True
            user.save()

            profile, _ = Profile.objects.get_or_create(user=user)
            profile.display_name = u['name']
            profile.theme_preference = 'light'
            profile.save()
            users[u['username']] = user
            status_txt = "created" if created else "updated"
            self.stdout.write(f"  User {u['username']} ({u['name']}) {status_txt}.")

        alex = users['alex']
        sarah = users['sarah']
        elena = users['elena']
        marcus = users['marcus']
        priya = users['priya']

        today = timezone.now().date()

        # ==========================================
        # PROJECT 1: Acme Mobile App v2.0
        # ==========================================
        proj1, _ = Project.objects.get_or_create(
            name="Acme Mobile App v2.0",
            defaults={
                'owner': alex,
                'description': 'Next-generation iOS and Android flagship application with offline sync, biometric security, and streamlined onboarding.',
                'color': '#2563EB',
            }
        )
        proj1.owner = alex
        proj1.save()

        # Add memberships
        ProjectMember.objects.get_or_create(project=proj1, user=alex, defaults={'role': 'owner'})
        ProjectMember.objects.get_or_create(project=proj1, user=sarah, defaults={'role': 'member'})
        ProjectMember.objects.get_or_create(project=proj1, user=elena, defaults={'role': 'member'})
        ProjectMember.objects.get_or_create(project=proj1, user=marcus, defaults={'role': 'member'})
        ProjectMember.objects.get_or_create(project=proj1, user=priya, defaults={'role': 'member'})

        # Columns
        col_todo, _ = Column.objects.get_or_create(project=proj1, name="To Do", defaults={'order': 0})
        col_prog, _ = Column.objects.get_or_create(project=proj1, name="In Progress", defaults={'order': 1})
        col_rev, _ = Column.objects.get_or_create(project=proj1, name="Review", defaults={'order': 2})
        col_done, _ = Column.objects.get_or_create(project=proj1, name="Done", defaults={'order': 3})

        # Labels
        lbl_fe, _ = Label.objects.get_or_create(project=proj1, name="Frontend", defaults={'color': '#2563EB'})
        lbl_be, _ = Label.objects.get_or_create(project=proj1, name="Backend", defaults={'color': '#0D9488'})
        lbl_bug, _ = Label.objects.get_or_create(project=proj1, name="Bug", defaults={'color': '#DC2626'})
        lbl_perf, _ = Label.objects.get_or_create(project=proj1, name="Performance", defaults={'color': '#D97706'})
        lbl_sec, _ = Label.objects.get_or_create(project=proj1, name="Security", defaults={'color': '#4F46E5'})

        # Clear existing tasks for fresh seeding
        proj1.tasks.all().delete()

        tasks_p1 = [
            {
                'column': col_todo,
                'title': 'Implement biometric authentication (FaceID & Fingerprint)',
                'description': 'Support FaceID and Android BiometricPrompt with cryptographic key storage inside Secure Enclave and KeyStore.',
                'assignee': elena,
                'priority': 'high',
                'due_date': today + datetime.timedelta(days=2),
                'labels': [lbl_fe, lbl_sec],
                'comments': [
                    (alex, "Please make sure we fail gracefully to PIN fallback if sensors are dirty or unavailable."),
                    (elena, "@alex tested on iPhone 15 Pro and Pixel 8, PIN fallback is working as expected."),
                ]
            },
            {
                'column': col_todo,
                'title': 'Refactor navigation stack with deep link restoration',
                'description': 'Ensure incoming deep links from push notifications properly restore stack hierarchy rather than resetting root view.',
                'assignee': alex,
                'priority': 'medium',
                'due_date': today + datetime.timedelta(days=5),
                'labels': [lbl_fe],
                'comments': [
                    (sarah, "@alex check the new routing schema branch before implementing.")
                ]
            },
            {
                'column': col_todo,
                'title': 'Localize strings into Spanish, French, and Japanese',
                'description': 'Extract hardcoded strings into locale resource files and verify RTL layout mirroring.',
                'assignee': priya,
                'priority': 'low',
                'due_date': today + datetime.timedelta(days=12),
                'labels': [lbl_fe],
                'comments': []
            },
            {
                'column': col_prog,
                'title': 'Optimize list view rendering for large catalog items',
                'description': 'Current feed drops frames during rapid fling scrolls. Implement windowed recycling and bitmap downsampling.',
                'assignee': elena,
                'priority': 'high',
                'due_date': today + datetime.timedelta(days=1), # due soon!
                'labels': [lbl_fe, lbl_perf],
                'comments': [
                    (marcus, "Profiling showed image decoding on main thread was taking 14ms per frame."),
                    (elena, "@marcus moving decode to worker threads immediately gained 60fps lock.")
                ]
            },
            {
                'column': col_prog,
                'title': 'Audit token refresh race conditions under poor connectivity',
                'description': 'When multiple concurrent requests fail with 401, only trigger one refresh handshake and queue pending requests.',
                'assignee': sarah,
                'priority': 'high',
                'due_date': today - datetime.timedelta(days=1), # overdue!
                'labels': [lbl_be, lbl_sec],
                'comments': [
                    (alex, "@sarah this is high priority for the v2.0 beta release next Tuesday."),
                    (sarah, "Working on an async mutex wrapper in the HTTP interceptor right now.")
                ]
            },
            {
                'column': col_prog,
                'title': 'Add offline sync queue with SQLite and retry backoff',
                'description': 'Queue offline mutations locally and reconcile with server when connectivity returns.',
                'assignee': marcus,
                'priority': 'medium',
                'due_date': today + datetime.timedelta(days=4),
                'labels': [lbl_fe, lbl_be],
                'comments': []
            },
            {
                'column': col_rev,
                'title': 'Resolve memory leak when switching between camera and gallery',
                'description': 'Garbage collection was failing to release raw byte buffers from unclosed image streams.',
                'assignee': elena,
                'priority': 'high',
                'due_date': today, # due today!
                'labels': [lbl_bug, lbl_perf],
                'comments': [
                    (priya, "Tested on Android 14 emulator, memory remains flat at 84MB after 50 toggles. LGTM!"),
                ]
            },
            {
                'column': col_rev,
                'title': 'Redesign checkout bottom sheet for one-handed operation',
                'description': 'Move primary action button within thumb zone and simplify shipping address card accordion.',
                'assignee': alex,
                'priority': 'medium',
                'due_date': today + datetime.timedelta(days=3),
                'labels': [lbl_fe],
                'comments': [
                    (elena, "@alex animations feel very snappy on device.")
                ]
            },
            {
                'column': col_done,
                'title': 'Migrate push notification payload handler to APNs v3',
                'description': 'HTTP/2 token-based authentication replaces legacy binary APNs protocol.',
                'assignee': sarah,
                'priority': 'medium',
                'due_date': today - datetime.timedelta(days=4),
                'labels': [lbl_be],
                'comments': [
                    (sarah, "Deployed to staging and verified push delivery latency <120ms."),
                    (alex, "Excellent work!")
                ]
            },
            {
                'column': col_done,
                'title': 'Fix timezone offset bug in transaction timestamp display',
                'description': 'UTC timestamps were parsed without client local offset causing yesterday transactions to display tomorrow.',
                'assignee': priya,
                'priority': 'high',
                'due_date': today - datetime.timedelta(days=7),
                'labels': [lbl_bug],
                'comments': []
            },
            {
                'column': col_done,
                'title': 'Instrument network telemetry and crash analytics',
                'description': 'Integrate OpenTelemetry distributed tracing and symbolicated crash breadcrumbs.',
                'assignee': marcus,
                'priority': 'medium',
                'due_date': today - datetime.timedelta(days=10),
                'labels': [lbl_be, lbl_perf],
                'comments': []
            },
            {
                'column': col_done,
                'title': 'Prepare App Store submission assets and privacy manifest',
                'description': 'Compile required privacy manifest declarations and export high-resolution screenshots for all device sizes.',
                'assignee': alex,
                'priority': 'low',
                'due_date': today - datetime.timedelta(days=2),
                'labels': [lbl_fe, lbl_sec],
                'comments': []
            },
        ]

        for i, tdata in enumerate(tasks_p1):
            task = Task.objects.create(
                project=proj1,
                column=tdata['column'],
                title=tdata['title'],
                description=tdata['description'],
                assignee=tdata['assignee'],
                creator=alex,
                due_date=tdata['due_date'],
                priority=tdata['priority'],
                order=i,
            )
            task.labels.set(tdata['labels'])

            # Activity
            Activity.objects.create(
                project=proj1,
                task=task,
                user=alex,
                action='created',
                details=f"created task \"{task.title}\""
            )

            # Comments
            for c_user, c_text in tdata['comments']:
                Comment.objects.create(
                    task=task,
                    user=c_user,
                    content=c_text
                )
                Activity.objects.create(
                    project=proj1,
                    task=task,
                    user=c_user,
                    action='commented',
                    details=f"commented on \"{task.title}\""
                )

        # ==========================================
        # PROJECT 2: Cloud Platform Migration
        # ==========================================
        proj2, _ = Project.objects.get_or_create(
            name="Cloud Platform Migration",
            defaults={
                'owner': marcus,
                'description': 'Enterprise migration to containerized microservices, zero-trust network ingress, and automated multi-region failover.',
                'color': '#0D9488',
            }
        )
        proj2.owner = marcus
        proj2.save()

        ProjectMember.objects.get_or_create(project=proj2, user=marcus, defaults={'role': 'owner'})
        ProjectMember.objects.get_or_create(project=proj2, user=alex, defaults={'role': 'member'})
        ProjectMember.objects.get_or_create(project=proj2, user=sarah, defaults={'role': 'member'})
        ProjectMember.objects.get_or_create(project=proj2, user=priya, defaults={'role': 'member'})

        col2_backlog, _ = Column.objects.get_or_create(project=proj2, name="Backlog", defaults={'order': 0})
        col2_disc, _ = Column.objects.get_or_create(project=proj2, name="In Discovery", defaults={'order': 1})
        col2_exec, _ = Column.objects.get_or_create(project=proj2, name="Execution", defaults={'order': 2})
        col2_veri, _ = Column.objects.get_or_create(project=proj2, name="Verified", defaults={'order': 3})

        lbl2_infra, _ = Label.objects.get_or_create(project=proj2, name="Infrastructure", defaults={'color': '#0D9488'})
        lbl2_db, _ = Label.objects.get_or_create(project=proj2, name="Database", defaults={'color': '#475569'})
        lbl2_sec, _ = Label.objects.get_or_create(project=proj2, name="Security", defaults={'color': '#4F46E5'})
        lbl2_devops, _ = Label.objects.get_or_create(project=proj2, name="DevOps", defaults={'color': '#2563EB'})

        proj2.tasks.all().delete()

        tasks_p2 = [
            {
                'column': col2_backlog,
                'title': 'Transition batch ETL pipelines from EC2 cron to serverless workers',
                'description': 'Decompose legacy night jobs into event-driven tasks triggered by S3 bucket events.',
                'assignee': sarah,
                'priority': 'medium',
                'due_date': today + datetime.timedelta(days=14),
                'labels': [lbl2_devops, lbl2_infra],
                'comments': []
            },
            {
                'column': col2_backlog,
                'title': 'Define Terraform modules for ephemeral preview environments',
                'description': 'Spins up isolated sandbox on each PR and tears down automatically upon merge.',
                'assignee': marcus,
                'priority': 'low',
                'due_date': today + datetime.timedelta(days=18),
                'labels': [lbl2_infra, lbl2_devops],
                'comments': []
            },
            {
                'column': col2_disc,
                'title': 'Conduct penetration testing on external API endpoints',
                'description': 'Simulate DDoS, credential stuffing, and SQL injection vectors against public load balancers.',
                'assignee': priya,
                'priority': 'high',
                'due_date': today + datetime.timedelta(days=3),
                'labels': [lbl2_sec],
                'comments': [
                    (marcus, "@priya staging WAF rules have been relaxed for your testing IP range.")
                ]
            },
            {
                'column': col2_disc,
                'title': 'Provision Redis cluster with auto-scaling read replicas',
                'description': 'Benchmark throughput with 10k synthetic users and calibrate eviction policies.',
                'assignee': sarah,
                'priority': 'medium',
                'due_date': today + datetime.timedelta(days=6),
                'labels': [lbl2_db, lbl2_infra],
                'comments': []
            },
            {
                'column': col2_exec,
                'title': 'Migrate primary PostgreSQL cluster to high-availability replica set',
                'description': 'Zero-downtime replication stream cutoff during Sunday 02:00 UTC maintenance window.',
                'assignee': marcus,
                'priority': 'high',
                'due_date': today + datetime.timedelta(days=1), # due soon!
                'labels': [lbl2_db, lbl2_infra],
                'comments': [
                    (sarah, "@marcus pre-flight replication lag is holding steady under 15ms."),
                    (marcus, "Fantastic. Cutover script dry-run completed successfully.")
                ]
            },
            {
                'column': col2_exec,
                'title': 'Configure zero-trust ingress with mTLS and Cloudflare Workers',
                'description': 'Enforce client certificate authentication for all internal microservice calls.',
                'assignee': alex,
                'priority': 'high',
                'due_date': today + datetime.timedelta(days=2),
                'labels': [lbl2_sec, lbl2_infra],
                'comments': []
            },
            {
                'column': col2_exec,
                'title': 'Implement Prometheus scraping for worker pool saturation metrics',
                'description': 'Export CPU throttled percentage and event loop lag gauges to Grafana dashboard.',
                'assignee': sarah,
                'priority': 'medium',
                'due_date': today + datetime.timedelta(days=5),
                'labels': [lbl2_devops],
                'comments': []
            },
            {
                'column': col2_veri,
                'title': 'Set up automated daily encrypted backups to dual-region bucket',
                'description': 'KMS key rotation enabled, with weekly restore validation drill to isolated staging DB.',
                'assignee': marcus,
                'priority': 'high',
                'due_date': today - datetime.timedelta(days=3),
                'labels': [lbl2_db, lbl2_sec],
                'comments': [
                    (priya, "Verified restore integrity. Checksums match 100%."),
                    (marcus, "Documented in compliance audit logs.")
                ]
            },
            {
                'column': col2_veri,
                'title': 'Draft disaster recovery playbook and run failover simulation',
                'description': 'Document step-by-step DNS switchover and test recovery time objective (<15 minutes).',
                'assignee': alex,
                'priority': 'medium',
                'due_date': today - datetime.timedelta(days=5),
                'labels': [lbl2_infra],
                'comments': []
            },
            {
                'column': col2_veri,
                'title': 'Consolidate IAM roles and enforce least-privilege policies',
                'description': 'Pruned 42 legacy wildcards and attached boundary policies to all CI/CD service accounts.',
                'assignee': marcus,
                'priority': 'medium',
                'due_date': today - datetime.timedelta(days=9),
                'labels': [lbl2_sec],
                'comments': []
            },
        ]

        for i, tdata in enumerate(tasks_p2):
            task = Task.objects.create(
                project=proj2,
                column=tdata['column'],
                title=tdata['title'],
                description=tdata['description'],
                assignee=tdata['assignee'],
                creator=marcus,
                due_date=tdata['due_date'],
                priority=tdata['priority'],
                order=i,
            )
            task.labels.set(tdata['labels'])

            Activity.objects.create(
                project=proj2,
                task=task,
                user=marcus,
                action='created',
                details=f"created task \"{task.title}\""
            )

            for c_user, c_text in tdata['comments']:
                Comment.objects.create(
                    task=task,
                    user=c_user,
                    content=c_text
                )
                Activity.objects.create(
                    project=proj2,
                    task=task,
                    user=c_user,
                    action='commented',
                    details=f"commented on \"{task.title}\""
                )

        # ==========================================
        # Notifications for Alex
        # ==========================================
        Notification.objects.filter(recipient=alex).delete()

        # Some notifications for alex
        n1 = Notification.objects.create(
            recipient=alex,
            actor=sarah,
            verb='mentioned',
            project=proj1,
            title='Mentioned in Acme Mobile App v2.0',
            message='@alex check the new routing schema branch before implementing.',
            is_read=False
        )
        n2 = Notification.objects.create(
            recipient=alex,
            actor=elena,
            verb='commented',
            project=proj1,
            title='New comment on Redesign checkout bottom sheet',
            message='@alex animations feel very snappy on device.',
            is_read=False
        )
        n3 = Notification.objects.create(
            recipient=alex,
            actor=marcus,
            verb='project_added',
            project=proj2,
            title='Added to Cloud Platform Migration',
            message='Marcus Vance added you as a member of Cloud Platform Migration.',
            is_read=True
        )
        n4 = Notification.objects.create(
            recipient=alex,
            actor=None,
            verb='due_soon',
            project=proj1,
            title='Task due soon: Redesign checkout bottom sheet',
            message='This task is due in 3 days.',
            is_read=True
        )

        self.stdout.write(self.style.SUCCESS(
            "Demo data seeded successfully!\n"
            "Demo credentials:\n"
            "  Username: alex\n"
            "  Password: password123\n"
            "Other users: sarah, elena, marcus, priya (all with password: password123)"
        ))
