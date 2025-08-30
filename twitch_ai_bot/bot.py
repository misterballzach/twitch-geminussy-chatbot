import os
import random
import asyncio
from twitchio.ext import commands
import google.generativeai as genai

class Bot(commands.Bot):
    def __init__(self, token, channel, personality, gemini_key, message_queue=None, rewrite_queue=None):
        super().__init__(token=token, prefix='!', initial_channels=[channel])
        self.personality = personality
        self.channel_name = channel
        self.message_queue = message_queue
        self.rewrite_queue = rewrite_queue
        genai.configure(api_key=gemini_key)
        self.model = genai.GenerativeModel('gemini-pro')
        self.is_ready = asyncio.Event()

    async def event_ready(self):
        print(f'Logged in as | {self.nick}')
        print(f'User id is | {self.user_id}')
        self.is_ready.set()
        if self.rewrite_queue:
            self.loop.create_task(self.process_rewrite_queue())
        self.loop.create_task(self.random_chatter())

    async def event_message(self, message):
        if message.echo:
            return
        if self.message_queue:
            self.message_queue.put(f"{message.author.name}: {message.content}")
        await self.handle_commands(message)

    @commands.command()
    async def ai(self, ctx: commands.Context, *, question: str):
        prompt = f"You are a Twitch bot with the following personality: {self.personality}. A user asked: '{question}'. Provide a concise and engaging response for the Twitch chat."
        try:
            response = self.model.generate_content(prompt)
            await ctx.send(response.text)
        except Exception as e:
            print(f"Error generating AI response: {e}")
            await ctx.send("Sorry, I'm having a little trouble thinking right now.")

    async def random_chatter(self):
        await self.is_ready.wait()
        while True:
            await asyncio.sleep(random.randint(300, 600))
            chat_prompt = f"You are a Twitch bot with the following personality: {self.personality}. Say something interesting or funny to keep the chat engaged. Don't ask a question, just make a statement."
            try:
                response = self.model.generate_content(chat_prompt)
                channel = self.get_channel(self.channel_name)
                if channel:
                    await channel.send(response.text)
            except Exception as e:
                print(f"Error generating random chatter: {e}")

    async def process_rewrite_queue(self):
        while True:
            if not self.rewrite_queue.empty():
                user_input = self.rewrite_queue.get()
                prompt = f"You are a Twitch bot with the following personality: {self.personality}. Rewrite the following user message in your voice: '{user_input}'"
                try:
                    response = self.model.generate_content(prompt)
                    channel = self.get_channel(self.channel_name)
                    if channel:
                        await channel.send(response.text)
                except Exception as e:
                    print(f"Error rewriting message: {e}")
            await asyncio.sleep(1)
