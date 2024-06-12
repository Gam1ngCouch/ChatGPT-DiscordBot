import discord
import openai
from config import DISCORD_TOKEN, OPENAI_API_KEY, ROLE_ID

openai.api_key = OPENAI_API_KEY

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True  # Erforderlich für das Löschen von Nachrichten
intents.voice_states = True  # Erforderlich für Sprachkanal-Events
client = discord.Client(intents=intents)

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

    if message.content.startswith('!ask'):
        prompt = message.content[len('!ask '):].strip()
        response = await get_chatgpt_response(prompt)
        await message.channel.send(response)

    elif message.content.startswith('!bild'):
        prompt = message.content[len('!bild '):].strip()
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

client.run(DISCORD_TOKEN)
