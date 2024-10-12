import pytchat
import os
import sys
import threading
import asyncio
from collections import deque
from dotenv import load_dotenv
from twitchio.ext import commands as twitch_commands

class YouTubeChatHandler:
    def __init__(self, video_id, mod_names):
        # Resolve the base path for PyInstaller
        self.base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        self.chat = pytchat.create(video_id=video_id, interruptable=False)
        self.mod_names = set(mod_names)
        self.queue = [deque(maxlen=1) for _ in range(3)]  # 3 separate deques for the top 3 chats
        self.super_chat_file = self.resource_path('../Data/Chat/Special/superchat.chloe')
        self.super_chat_username_file = self.resource_path('../Data/Chat/Special/superviewer.chloe')
        self.mod_chat_file = self.resource_path('../Data/Chat/Special/modmessage.hana')
        self.mod_chat_username_file = self.resource_path('../Data/Chat/Special/moderator.hana')
        self.chat_files = [
            self.resource_path('../Data/Chat/General/input1.hana'),
            self.resource_path('../Data/Chat/General/input2.hana'),
            self.resource_path('../Data/Chat/General/input3.hana')
        ]
        self.username_files = [
            self.resource_path('../Data/Chat/General/viewer1.hana'),
            self.resource_path('../Data/Chat/General/viewer2.hana'),
            self.resource_path('../Data/Chat/General/viewer3.hana')
        ]
        self._stop_event = threading.Event()

    def handle_chat(self, item):
        message = item.message
        username = item.author.name

        # Check for super chat
        if item.type == 'superChat':
            self.save_to_file(self.super_chat_file, message)
            self.save_to_file(self.super_chat_username_file, username)

        # Check if the user is a moderator
        elif username in self.mod_names:
            self.save_to_file(self.mod_chat_file, message)
            self.save_to_file(self.mod_chat_username_file, username)

        # Handle regular chat messages
        else:
            # Shift chats in the queue
            for i in range(2, 0, -1):
                if self.queue[i-1]:
                    self.queue[i].append(self.queue[i-1].pop())

            self.queue[0].append((username, message))

            # Save to respective files
            for i, q in enumerate(self.queue):
                if q:
                    self.save_to_file(self.chat_files[i], q[0][1])
                    self.save_to_file(self.username_files[i], q[0][0])

    def save_to_file(self, file_path, content):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"{content}\n")

    def start(self):
        while not self._stop_event.is_set() and self.chat.is_alive():
            for item in self.chat.get().sync_items():
                self.handle_chat(item)

    def stop(self):
        self._stop_event.set()

    def resource_path(self, relative_path):
        """ Get the absolute path to the resource, works for dev and for PyInstaller """
        return os.path.join(self.base_path, relative_path)

class TwitchChatHandler(twitch_commands.Bot):
    def __init__(self, token, client_id, nick, prefix, initial_channels, mod_names):
        super().__init__(token=token, client_id=client_id, nick=nick, prefix=prefix, initial_channels=initial_channels)
        # Resolve the base path for PyInstaller
        self.base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        self.mod_names = set(mod_names)
        self.queue = [deque(maxlen=1) for _ in range(3)]  # 3 separate deques for the top 3 chats
        self.super_chat_file = self.resource_path('../Data/Chat/Special/superchat.chloe')
        self.super_chat_username_file = self.resource_path('../Data/Chat/Special/superviewer.chloe')
        self.mod_chat_file = self.resource_path('../Data/Chat/Special/modmessage.hana')
        self.mod_chat_username_file = self.resource_path('../Data/Chat/Special/moderator.hana')
        self.chat_files = [
            self.resource_path('../Data/Chat/General/input1.hana'),
            self.resource_path('../Data/Chat/General/input2.hana'),
            self.resource_path('../Data/Chat/General/input3.hana')
        ]
        self.username_files = [
            self.resource_path('../Data/Chat/General/viewer1.hana'),
            self.resource_path('../Data/Chat/General/viewer2.hana'),
            self.resource_path('../Data/Chat/General/viewer3.hana')
        ]
        self._stop_event = threading.Event()

    async def event_message(self, message):
        if self._stop_event.is_set():
            return  # Stop processing messages when the event is set
        await self.handle_chat(message)

    async def handle_chat(self, message):
        username = message.author.name
        content = message.content

        # Check for special messages (like Super Chat)
        if message.tags.get('badges') and 'broadcaster' in message.tags.get('badges'):
            self.save_to_file(self.super_chat_file, content)
            self.save_to_file(self.super_chat_username_file, username)

        # Check if the user is a moderator
        elif username in self.mod_names:
            self.save_to_file(self.mod_chat_file, content)
            self.save_to_file(self.mod_chat_username_file, username)

        # Handle regular chat messages
        else:
            # Shift chats in the queue
            for i in range(2, 0, -1):
                if self.queue[i-1]:
                    self.queue[i].append(self.queue[i-1].pop())

            self.queue[0].append((username, content))

            # Save to respective files
            for i, q in enumerate(self.queue):
                if q:
                    self.save_to_file(self.chat_files[i], q[0][1])
                    self.save_to_file(self.username_files[i], q[0][0])

    def save_to_file(self, file_path, content):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"{content}\n")

    def stop(self):
        self._stop_event.set()
        asyncio.run_coroutine_threadsafe(self.close(), self.loop)

    def run(self):
        # Start bot as normal
        super().run()

    def resource_path(self, relative_path):
        """ Get the absolute path to the resource, works for dev and for PyInstaller """
        return os.path.join(self.base_path, relative_path)

        
def youtube_chat():
    load_dotenv()
    video_id = os.getenv('Video-Url')
    mod_names = ["mod1", "mod2", "mod3"]  # Replace with actual moderator names
    handler = YouTubeChatHandler(video_id, mod_names)
    handler.start()


def twitch_chat():
    load_dotenv()
    token = os.getenv('Twitch-Token')
    client_id = os.getenv('Twitch-Client-ID')
    nick = os.getenv('Twitch-Nick')
    prefix = os.getenv('Twitch-Prefix')
    initial_channels = [os.getenv('Twitch-Channel')]
    mod_names = ["mod1", "mod2", "mod3"]  # Replace with actual moderator names

    bot = TwitchChatHandler(token=token, client_id=client_id, nick=nick, prefix=prefix, initial_channels=initial_channels, mod_names=mod_names)
    bot.run()

if __name__ == "__main__":
    youtube_chat()