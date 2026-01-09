# IdentityCrisis 🎭

A chaotic Discord bot that gives users a new identity every time they join a voice channel. Now with a fancy web dashboard!

## What does it do?

Every time someone joins a voice channel, IdentityCrisis automatically changes their server nickname to something completely random. Your friend Marco? Now he's "Gino Panino". Your buddy Sarah? She just became "Captain Spaghetti".

## Features

- **Automatic Renaming**: Detects when users join voice channels and assigns random nicknames
- **Nickname Restoration**: Optionally restore original nicknames when users leave
- **Web Dashboard**: Beautiful web interface to manage settings per server
- **Discord OAuth2**: Login with Discord to manage your servers
- **Per-Server Configuration**: Each server can have its own settings and nickname lists
- **Custom Nickname Lists**: Add your own nicknames via the dashboard
- **Immunity Role**: Protect certain users from the chaos
- **Excluded Channels**: Skip renaming in specific voice channels

## Tech Stack

- **Bot**: Python 3.11+, discord.py
- **Web**: FastAPI, Jinja2, TailwindCSS, Alpine.js
- **Database**: PostgreSQL with SQLAlchemy (async)
- **Auth**: Discord OAuth2

## Project Structure

```
IdentityCrisis/
├── main.py              # Entry point (runs bot + web)
├── requirements.txt
├── .env.example
├── bot/                 # Discord bot
│   ├── bot.py
│   ├── cogs/
│   │   └── voice_handler.py
│   └── data/
│       └── nicknames.py
├── web/                 # Web dashboard
│   ├── app.py
│   ├── discord_oauth.py
│   ├── routes/
│   │   ├── auth.py
│   │   ├── api.py
│   │   └── pages.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── home.html
│   │   ├── dashboard.html
│   │   └── guild.html
│   └── static/
└── shared/              # Shared code
    ├── config.py
    └── database.py
```

## Installation

### Prerequisites

- Python 3.11+
- PostgreSQL database
- A Discord Bot Token
- A sense of humor

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/IdentityCrisis.git
cd IdentityCrisis
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up PostgreSQL

Create a database for the bot:

```bash
createdb identitycrisis
# Or via psql:
# CREATE DATABASE identitycrisis;
```

### 5. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

- `DISCORD_TOKEN`: Your bot token from Discord Developer Portal
- `DISCORD_CLIENT_ID`: Your application's Client ID
- `DISCORD_CLIENT_SECRET`: Your application's Client Secret
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: Random string for session security

### 6. Set up Discord OAuth2

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Select your application
3. Go to **OAuth2** > **General**
4. Add a redirect URI: `http://localhost:8000/auth/callback`
5. Copy Client ID and Client Secret to your `.env`

### 7. Set up Discord Bot

In the Developer Portal:

1. Go to **Bot** section
2. Enable these **Privileged Gateway Intents**:
   - Server Members Intent
   - Message Content Intent (optional)
3. Go to **OAuth2** > **URL Generator**
4. Select scopes: `bot`
5. Select permissions: `Manage Nicknames`, `View Channels`, `Connect`
6. Use the generated URL to invite the bot

### 8. Run the application

```bash
python main.py
```

This starts both the Discord bot and the web dashboard. Access the dashboard at `http://localhost:8000`.

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DISCORD_TOKEN` | Yes | Discord bot token |
| `DISCORD_CLIENT_ID` | Yes | Discord OAuth2 client ID |
| `DISCORD_CLIENT_SECRET` | Yes | Discord OAuth2 client secret |
| `DISCORD_REDIRECT_URI` | No | OAuth2 callback URL (default: `http://localhost:8000/auth/callback`) |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `SECRET_KEY` | No | Session encryption key (change in production!) |
| `WEB_HOST` | No | Web server host (default: `0.0.0.0`) |
| `WEB_PORT` | No | Web server port (default: `8000`) |
| `BASE_URL` | No | Public URL of the dashboard |
| `LOG_FILE_PATH` | No | Log file path (default: `logs/identitycrisis.log`) |
| `LOG_LEVEL` | No | Log level (default: `INFO`) |
| `LOG_VIEWER_ID` | No | Discord user ID allowed to view logs page |

## Deployment

### With Docker (Recommended)

Coming soon...

### Manual Deployment

1. Set up a PostgreSQL database
2. Configure environment variables for production
3. Use a process manager like `systemd` or `supervisor`
4. Put behind a reverse proxy (nginx/caddy) with HTTPS

Example nginx config:

```nginx
server {
    listen 443 ssl;
    server_name identitycrisis.yourdomain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Default Nicknames

The bot comes with a curated selection of absurd nicknames:

- Gino Panino, Captain Spaghetti, Lord Farquaad's Cousin
- Definitely Not A Bot, Someone's Mom, Kevin
- CEO of Nothing, Professional Screamer, Local Cryptid
- Human Lasagna, Angry Mozzarella, Espresso Depresso
- ...and many more

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
