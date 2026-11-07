import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from projects.models import Project, ProjectMember

class BoardConsumer(AsyncWebsocketConsumer):
    # In-memory board presence set: project_id -> dict of user_id: {username, display_name, avatar_color, initials}
    presence = {}

    async def connect(self):
        self.project_id = self.scope['url_route']['kwargs']['project_id']
        self.room_group_name = f'board_{self.project_id}'
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close(code=4001)
            return

        # Check membership
        has_access = await self.check_project_access(self.user.id, self.project_id)
        if not has_access:
            await self.close(code=4003)
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Update presence
        user_info = await self.get_user_info(self.user.id)
        if self.project_id not in BoardConsumer.presence:
            BoardConsumer.presence[self.project_id] = {}
        BoardConsumer.presence[self.project_id][self.user.id] = user_info

        # Broadcast updated presence to group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'presence_update',
                'users': list(BoardConsumer.presence[self.project_id].values()),
            }
        )

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            # Remove from presence
            if self.project_id in BoardConsumer.presence:
                BoardConsumer.presence[self.project_id].pop(self.user.id, None)
                users = list(BoardConsumer.presence[self.project_id].values())
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'presence_update',
                        'users': users,
                    }
                )

            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        # Client messages if needed (e.g. typing ping or presence heartbeat)
        try:
            data = json.loads(text_data)
            action = data.get('action')
            if action == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
        except Exception:
            pass

    async def presence_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'presence_update',
            'users': event['users'],
        }))

    async def board_event(self, event):
        # Broadcast card/column/comment events to client
        await self.send(text_data=json.dumps({
            'type': 'board_event',
            'event': event['event'],
            'data': event['data'],
            'actor_id': event.get('actor_id'),
        }))

    @database_sync_to_async
    def check_project_access(self, user_id, project_id):
        try:
            project = Project.objects.get(id=project_id)
            user = User.objects.get(id=user_id)
            return project.is_member(user)
        except Exception:
            return False

    @database_sync_to_async
    def get_user_info(self, user_id):
        user = User.objects.select_related('profile').get(id=user_id)
        profile = getattr(user, 'profile', None)
        return {
            'id': user.id,
            'username': user.username,
            'display_name': profile.name if profile else user.username,
            'initials': profile.initials if profile else user.username[:2].upper(),
            'avatar_color': profile.avatar_color if profile else '#2563EB',
            'avatar_url': profile.avatar_url if profile else None,
        }
