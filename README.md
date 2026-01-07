# IdentityCrisis 🎭

A chaotic Discord bot that gives users a new identity every time they join a voice channel. Who are you? Nobody knows anymore.

## What does it do?

Every time someone joins a voice channel, IdentityCrisis automatically changes their server nickname to something completely random. Your friend Marco? Now he's "Gino Panino". Your buddy Sarah? She just became "Captain Spaghetti".

Optionally, the bot can restore the original nickname when users leave the voice channel, or just let the chaos accumulate.

## Features

- **Automatic Renaming**: Detects when users join voice channels and assigns random nicknames
- **Nickname Restoration**: Optionally restore original nicknames when users leave (configurable)
- **Per-Server Configuration**: Each server can have its own settings and nickname lists
- **Custom Nickname Lists**: Add your own nicknames via slash commands
- **Immunity Role**: Protect certain users from the chaos (if you're boring like that)

## Requirements

- Python 3.11+
- A Discord Bot Token
- A sense of humor

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/IdentityCrisis.git
   cd IdentityCrisis
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up your environment variables**
   
   Create a `.env` file in the root directory:
   ```env
   DISCORD_TOKEN=your_bot_token_here
   ```

5. **Run the bot**
   ```bash
   python main.py
   ```

## Discord Bot Setup

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application and add a bot
3. Enable the following **Privileged Gateway Intents**:
   - Server Members Intent
   - Message Content Intent (if you want text commands)
4. Generate an invite link with these permissions:
   - Manage Nicknames
   - View Channels
   - Connect (to detect voice channel joins)
5. Invite the bot to your server

## Commands

| Command | Description |
|---------|-------------|
| `/nicknames list` | Show current nickname list for this server |
| `/nicknames add <name>` | Add a nickname to the server's list |
| `/nicknames remove <name>` | Remove a nickname from the list |
| `/nicknames reset` | Reset to default nickname list |
| `/config restore <on/off>` | Toggle nickname restoration on voice leave |
| `/config immunity <role>` | Set the immunity role |
| `/stats` | Show renaming statistics |

## Default Nicknames

The bot comes with a curated selection of absurd nicknames mixing Italian and English humor. Here's a taste:

- Gino Panino
- Captain Spaghetti
- Lord Farquaad's Cousin
- Definitely Not A Bot
- Someone's Mom
- Il Magnifico
- Kevin (just Kevin)
- Professional Overthinker
- Certified Chaos Agent
- ...and many more

## Configuration

Each server can customize:
- **Nickname list**: Add server-specific nicknames
- **Restore mode**: Whether to restore original nicknames on voice leave
- **Immunity role**: A role that protects users from renaming

## Contributing

Got a funny nickname idea? Found a bug? Feel free to open an issue or submit a PR.

Please keep nicknames:
- Funny but not offensive
- Safe for a general audience
- No slurs or discriminatory content

## License

This project is licensed under the GNU General Public License v3.0. See [LICENSE](LICENSE) for details.

## Disclaimer

This bot is meant for fun among friends. Use responsibly. We are not responsible for any identity crises, existential dread, or confused Discord calls that may result from using this bot.

---

*"Who am I? Who are you? Does it even matter anymore?"*
