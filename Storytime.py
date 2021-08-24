import discord
import time
import asyncio
from io import StringIO

channel_id = 816015583505809461
guild_id = 816015582385274961


class StoryBot(discord.Client):

    current_story_embed = None
    current_story_message_id = None

    current_story = ""

    previous_file_message = None

    participants = []
    contributors = []

    turn = 0

    setup = False

    setup_time_left = 60
    setup_duration = 60
    initial_time_check = None

    turn_timer = 180  # 180
    initial_turn_time = None

    def __init__(self):
        super().__init__()

        self.loop.create_task(self.update())

    async def update(self):
        await self.wait_until_ready()
        while not self.is_closed():
            if StoryBot.setup:
                StoryBot.setup_time_left = StoryBot.setup_duration - (time.time() - StoryBot.initial_time_check)
                if StoryBot.setup_time_left > 0:
                    await self.update_embed()
                    await self.update_message()
                else:
                    StoryBot.setup = False
                    StoryBot.initial_turn_time = time.time()
                    StoryBot.current_story_embed.set_field_at(0, name="Current Turn", value=self.get_guild(guild_id).get_member(StoryBot.participants[0]).nick)
                    await self.update_embed()
                    await self.update_message()

            if StoryBot.initial_turn_time is not None:
                time_left = StoryBot.turn_timer - (time.time() - StoryBot.initial_turn_time)
                StoryBot.current_story_embed.set_field_at(1, name="Turn Time", value=str(int(time_left)))
                await self.update_message()

                if time_left <= 0:
                    await self.remove_participant(StoryBot.participants[StoryBot.turn])


            await asyncio.sleep(1)

    async def remove_participant(self, participant_id):
        if len(StoryBot.participants) == 1:
            await self.end_story()
        else:
            index = StoryBot.participants.index(participant_id)
            del StoryBot.participants[index]
            print("PARTICIPANTS: " + str(StoryBot.participants))
            if index < StoryBot.turn:
                StoryBot.turn -= 1
            if StoryBot.turn >= len(StoryBot.participants):
                StoryBot.turn = 0

            StoryBot.initial_turn_time = time.time()
            await self.update_embed()
            await self.update_message()

    async def on_message(self, message):
        if message.author.id != self.user.id and message.channel.id == channel_id:
            if message.content[:3] == "new" and StoryBot.current_story_message_id is None:
                StoryBot.current_story_embed = discord.Embed(title=message.content[4:], description="Type \"join\" to join!")
                StoryBot.current_story_embed.add_field(name="Time Until Start", value="60")
                StoryBot.current_story_embed.add_field(name="Turn Time", value=str(StoryBot.turn_timer))
                new_message = await self.get_channel(channel_id).send(embed=StoryBot.current_story_embed)
                StoryBot.current_story_message_id = new_message.id
                StoryBot.participants.append(message.author.id)
                StoryBot.initial_time_check = time.time()
                StoryBot.setup = True
                await self.update_embed()
                await self.update_message()
                await message.delete()

            elif message.content == "join" and StoryBot.setup:
                if message.author.id not in StoryBot.participants:
                    StoryBot.participants.append(message.author.id)
                    await self.update_embed()
                    await self.update_message()
                await message.delete()

            elif StoryBot.current_story_message_id is not None and not StoryBot.setup and message.content == "leave":
                if message.author.id in StoryBot.participants:
                    await self.remove_participant(message.author.id)

                await message.delete()

            elif StoryBot.current_story_message_id is not None and not StoryBot.setup:
                print("Sent a story text")
                try:
                    index = StoryBot.participants.index(message.author.id)
                    if index == StoryBot.turn:
                        addition = message.content
                        addition.strip()
                        if StoryBot.current_story != "":
                            StoryBot.current_story += " "
                        StoryBot.current_story += addition
                        print("Current Story: " + StoryBot.current_story)

                        if message.author.id not in StoryBot.contributors:
                            StoryBot.contributors.append(message.author.id)

                        if StoryBot.turn + 1 >= len(StoryBot.participants):
                            StoryBot.turn = 0
                        else:
                            StoryBot.turn += 1

                        StoryBot.initial_turn_time = time.time()

                        await self.update_embed()
                        await self.update_message()
                        await self.send_file()

                except ValueError:
                    print("Someone typed who shouldn't be")

                finally:
                    await message.delete()

            else:
                await message.delete()

    async def end_story(self):

        if StoryBot.current_story == "":
            message = await self.get_channel(channel_id).fetch_message(StoryBot.current_story_message_id)
            await message.delete()
        else:
            contributors = ""
            for contributor in StoryBot.contributors:
                contributors += (self.get_guild(guild_id).get_member(contributor).name + ", ")
            StoryBot.current_story_embed.set_footer(text="Contributors: " + contributors)

            StoryBot.current_story_embed.clear_fields()

            await self.update_message()

        StoryBot.contributors = []

        StoryBot.initial_turn_time = None

        StoryBot.current_story_embed = None
        StoryBot.current_story_message_id = None

        StoryBot.current_story = ""

        StoryBot.previous_file_message = None

        StoryBot.participants = []

        StoryBot.turn = 0

        StoryBot.setup = False

        StoryBot.setup_time_left = 10
        StoryBot.initial_time_check = None

    async def send_file(self):
        if StoryBot.previous_file_message is not None:
            previous_message = await self.get_channel(channel_id).fetch_message(StoryBot.previous_file_message)
            await previous_message.delete()
        file = discord.File(StringIO(StoryBot.current_story), filename="Story.txt")
        new_message = await self.get_channel(channel_id).send(file=file)
        StoryBot.previous_file_message = new_message.id

    async def update_embed(self):
        print("Edited Embed")
        footer_text = "Joined Users: "
        for user_id in StoryBot.participants:
            user = self.get_guild(guild_id).get_member(user_id)
            footer_text += (user.name + ", ")
        print("Set footer to: " + footer_text)
        StoryBot.current_story_embed.set_footer(text=footer_text)

        if StoryBot.setup:
            StoryBot.current_story_embed.set_field_at(0, name="Time Until Start", value=str(int(StoryBot.setup_time_left)))

        elif StoryBot.current_story_message_id is not None:
            new_description = ""
            if len(StoryBot.current_story) > 2000:
                new_description += "..."
            new_description += StoryBot.current_story[-2000:]
            print("Story from embed function: " + StoryBot.current_story[-2000:])
            StoryBot.current_story_embed.description = new_description
            print("Set description to: " + StoryBot.current_story_embed.description)

            StoryBot.current_story_embed.set_field_at(0, name="Current Turn", value=self.get_guild(guild_id).get_member(StoryBot.participants[StoryBot.turn]).name)

    async def update_message(self):
        message = await self.get_channel(channel_id).fetch_message(StoryBot.current_story_message_id)
        await message.edit(embed=StoryBot.current_story_embed)
        print("Edited Message")


bot = StoryBot()
bot.run("")
