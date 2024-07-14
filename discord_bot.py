import discord
import openai
import yt_dlp as youtube_dl
import asyncio
from discord.utils import get
from config import DISCORD_TOKEN, OPENAI_API_KEY, ROLE_ID

openai.api_key = OPENAI_API_KEY

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True  # Erforderlich für das Löschen von Nachrichten
intents.voice_states = True  # Erforderlich für Sprachkanal-Events
client = discord.Client(intents=intents)

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # Bind to ipv4 since ipv6 addresses cause issues sometimes
}

# für Linux
ffmpeg_options = {
    'executable': '/usr/bin/ffmpeg',  # Pfad zu ffmpeg angeben
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_running_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class MusicPlayer:
    def __init__(self, loop):
        self.current = None
        self.queue = asyncio.Queue()
        self.next = asyncio.Event()
        self.voice_client = None
        self.loop = loop

    async def play_next(self):
        self.next.clear()
        try:
            self.current = await self.queue.get()
        except asyncio.QueueEmpty:
            self.current = None

        if self.current:
            self.voice_client.play(self.current, after=self.toggle_next)
            await self.next.wait()
        else:
            self.voice_client.stop()

    def toggle_next(self, error=None):
        if error:
            print(f'Player error: {error}')
        self.loop.call_soon_threadsafe(self.next.set)

    async def add_to_queue(self, song):
        await self.queue.put(song)
        if not self.voice_client.is_playing():
            await self.play_next()

    async def stop(self):
        if self.voice_client.is_playing():
            self.voice_client.stop()
        while not self.queue.empty():
            self.queue.get_nowait()
        self.next.set()
        await self.voice_client.disconnect()

    async def skip(self):
        if self.voice_client.is_playing():
            self.voice_client.stop()
        await self.play_next()

async def get_chatgpt_response(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response['choices'][0]['message']['content'].strip()
    except openai.error.RateLimitError:
        return "Ich habe mein Nutzungslimit erreicht. Bitte versuche es später erneut."
    except openai.error.OpenAIError as e:
        return f"Ein Fehler ist aufgetreten: {str(e)}"

async def generate_image(prompt):
    try:
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        return response['data'][0]['url']
    except openai.error.OpenAIError as e:
        return f"Ein Fehler ist aufgetreten: {str(e)}"

def get_help_embed():
    embed = discord.Embed(
        title="Hilfe - Verfügbare Befehle",
        description="Hier sind alle verfügbaren Befehle und deren Erklärungen.",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="!chat <Nachricht>",
        value="Fragt ChatGPT für eine Textantwort an.",
        inline=False
    )
    embed.add_field(
        name="!image <Beschreibung>",
        value="Generiert ein Bild basierend auf der Beschreibung mit DALL·E.",
        inline=False
    )
    embed.add_field(
        name="!del <Anzahl>",
        value="Löscht die angegebene Anzahl von Nachrichten im Kanal. (Nur für Benutzer mit der entsprechenden Rolle)",
        inline=False
    )
    embed.add_field(
        name="!voice <Kanalname> <Benutzerobergrenze>",
        value="Erstellt einen temporären Sprachkanal mit dem angegebenen Namen und der optionalen Benutzerobergrenze. Der Ersteller wird direkt in den Kanal verschoben.",
        inline=False
    )
    embed.add_field(
        name="!music <YouTube-Link>",
        value="Spielt das angegebene YouTube-Video im Sprachkanal des Benutzers ab.",
        inline=False
    )
    embed.add_field(
        name="!stop",
        value="Stoppt die Wiedergabe und leert die Warteschlange. Der Bot verlässt den Sprachkanal.",
        inline=False
    )
    embed.add_field(
        name="!skip",
        value="Überspringt den aktuellen Titel und spielt den nächsten in der Warteschlange.",
        inline=False
    )
    embed.add_field(
        name="!hilfe",
        value="Zeigt diese Hilfe-Nachricht an.",
        inline=False
    )
    embed.set_footer(text="Erstellt von deinem freundlichen Bot.")
    return embed

@client.event
async def on_ready():
    print(f'Wir sind eingeloggt als {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!chat'):
        prompt = message.content[len('!chat '):].strip()
        response = await get_chatgpt_response(prompt)
        await message.channel.send(response)

    elif message.content.startswith('!image'):
        prompt = message.content[len('!image '):].strip()
        image_url = await generate_image(prompt)
        await message.channel.send(image_url)

    elif message.content.startswith('!del'):
        # Überprüfen, ob der Benutzer die erforderliche Rolle hat
        role = discord.utils.get(message.guild.roles, id=int(ROLE_ID))
        if role in message.author.roles:
            try:
                number_of_messages = int(message.content[len('!del '):].strip())
                if number_of_messages > 0:
                    deleted = await message.channel.purge(limit=number_of_messages + 1)
                    await message.channel.send(f'{len(deleted) - 1} Nachrichten wurden gelöscht.', delete_after=5)
                else:
                    await message.channel.send('Bitte gib eine positive Zahl an.', delete_after=5)
            except ValueError:
                await message.channel.send('Bitte gib eine gültige Zahl an.', delete_after=5)
        else:
            await message.channel.send('Du hast keine Berechtigung, diesen Befehl auszuführen.', delete_after=5)

    elif message.content.startswith('!voice'):
        parts = message.content[len('!voice '):].strip().split()
        if len(parts) == 0:
            await message.channel.send('Bitte gib einen gültigen Kanalnamen an.', delete_after=5)
            return

        channel_name = parts[0]
        user_limit = None

        if len(parts) > 1:
            try:
                user_limit = int(parts[1])
            except ValueError:
                await message.channel.send('Bitte gib eine gültige Zahl für die Benutzerobergrenze an.', delete_after=5)
                return

        category = discord.utils.get(message.guild.categories, name="Temp Channels")
        if not category:
            category = await message.guild.create_category("Temp Channels")

        channel = await category.create_voice_channel(channel_name, user_limit=user_limit)

        # Ersteller in den neuen Sprachkanal verschieben
        if message.author.voice:
            await message.author.move_to(channel)
            await message.channel.send(f'Temporärer Sprachkanal "{channel_name}" wurde erstellt und du wurdest verschoben.', delete_after=10)
        else:
            await message.channel.send(f'Temporärer Sprachkanal "{channel_name}" wurde erstellt, aber du bist in keinem Sprachkanal.', delete_after=10)

    elif message.content.startswith('!music'):
        if message.author.voice:
            voice_channel = message.author.voice.channel
            url = message.content[len('!music '):].strip()

            voice_client = get(client.voice_clients, guild=message.guild)
            if not voice_client:
                voice_client = await voice_channel.connect()

            music_player.voice_client = voice_client

            async with message.channel.typing():
                player = await YTDLSource.from_url(url, loop=client.loop, stream=True)
                await music_player.add_to_queue(player)

            await message.channel.send(f'Zur Warteschlange hinzugefügt: {player.title}', delete_after=30)
        else:
            await message.channel.send('Du musst dich in einem Sprachkanal befinden, um Musik abzuspielen.', delete_after=10)

    elif message.content.startswith('!stop'):
        if music_player.voice_client:
            await music_player.stop()
            await message.channel.send('Musikwiedergabe gestoppt und Warteschlange geleert. Der Bot hat den Sprachkanal verlassen.', delete_after=10)

    elif message.content.startswith('!skip'):
        if music_player.voice_client:
            await music_player.skip()
            await message.channel.send('Titel übersprungen.', delete_after=10)

    elif message.content.startswith('!hilfe'):
        help_embed = get_help_embed()
        await message.channel.send(embed=help_embed)

@client.event
async def on_voice_state_update(member, before, after):
    if before.channel is not None and before.channel.category and before.channel.category.name == "Temp Channels":
        if len(before.channel.members) == 0:
            await before.channel.delete()

            # Überprüfen, ob noch Kanäle in der Kategorie vorhanden sind
            if not any(c for c in before.channel.category.channels if isinstance(c, discord.VoiceChannel)):
                await before.channel.category.delete()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    music_player = MusicPlayer(loop)
    client.run(DISCORD_TOKEN)
