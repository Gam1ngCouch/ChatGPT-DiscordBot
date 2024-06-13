# Server aktualisieren und notwendige Pakete installieren
sudo apt update
sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv ffmpeg -y

# Virtuelle Umgebung erstellen und aktivieren
python3 -m venv myenv
source myenv/bin/activate

# Python-Abhängigkeiten in der virtuellen Umgebung installieren
pip install discord.py openai yt-dlp

# Bot-Dateien auf den Server hochladen (Beispiel mit SCP)
scp -r /path/to/your/bot/files username@your_server_ip:/path/to/remote/directory

# Konfigurationsdatei erstellen
echo "DISCORD_TOKEN = 'your-discord-bot-token'
OPENAI_API_KEY = 'your-openai-api-key'
ROLE_ID = 'your-role-id'" > /path/to/your/bot/files/config.py

# tmux installieren
sudo apt install tmux -y

# tmux-Sitzung erstellen und Bot starten
tmux new -s discord-bot
cd /path/to/your/bot/files
source /path/to/your/venv/bin/activate
python3 discord_bot.py

# tmux-Sitzung verlassen
Ctrl+B, dann D

# Zu tmux-Sitzung zurückkehren
tmux attach -t discord-bot