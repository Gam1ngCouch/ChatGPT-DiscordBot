import os

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ROLE_ID = os.getenv('ROLE_ID')

# Print for debugging purposes (remove in production)
print("DISCORD_TOKEN:", DISCORD_TOKEN)
print("OPENAI_API_KEY:", OPENAI_API_KEY)
print("ROLE_ID:", ROLE_ID)
