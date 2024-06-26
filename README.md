# Discord Bot mit ChatGPT und DALL·E Integration
Author: Gam1ngCouch
Discordtag: gam1ngcouch    

Dies ist ein Discord-Bot, der mit OpenAI's ChatGPT und DALL·E integriert ist, um Textantworten und Bildgenerierungen basierend auf Benutzereingaben zu liefern. Der Bot kann auch temporäre Sprachkanäle erstellen, Nachrichten löschen und eine Hilfefunktion anzeigen.

## Voraussetzungen

- Python 3.8 oder höher
- Ein Discord-Bot-Token
- Ein OpenAI-API-Schlüssel

## Installation

1. **Klone das Repository**

   ```bash
   git clone https://github.com/Gam1ngCouch/ChatGPT-DiscordBot.git
   cd dein-repo

2. **Installiere die Abhängigkeiten**
    
    pip install -r requirements.txt

3- **FFmpeg installieren**
    FFMpeg herunterladen und installieren https://ffmpeg.org/

3. **Erstelle eine Datei namens config.py im Projektverzeichnis mit folgendem Inhalt**

    DISCORD_TOKEN = 'DEIN_DISCORD_BOT_TOKEN'
    OPENAI_API_KEY = 'DEIN_OPENAI_API_KEY'
    ROLE_ID = 'DISCORD_ROLE_ID'  # ID der Rolle, die den Löschbefehl ausführen darf

4. **starte den Bot**

    python discord_bot.py



**Verfügbare Befehle**

!ask <Nachricht> - Fragt ChatGPT für eine Textantwort an.
!bild <Beschreibung> - Generiert ein Bild basierend auf der Beschreibung mit DALL·E.
!del <Anzahl> - Löscht die angegebene Anzahl von Nachrichten im Kanal. (Nur für Benutzer mit der entsprechenden Rolle)
!voice <Kanalname> <Benutzerobergrenze> - Erstellt einen temporären Sprachkanal mit dem angegebenen Namen und der optionalen Benutzerobergrenze. Der Ersteller wird direkt in den Kanal verschoben.
!hilfe - Zeigt eine Hilfe-Nachricht mit allen verfügbaren Befehlen an.


**Wichtige Hinweise**
Stelle sicher, dass der Bot die erforderlichen Berechtigungen hat, um Nachrichten zu lesen, zu senden und zu löschen sowie Sprachkanäle zu verwalten.
Die ID der Rolle, die den Löschbefehl ausführen darf, sollte korrekt in der config.py Datei angegeben werden.
