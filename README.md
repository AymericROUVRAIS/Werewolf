# Werewolf (Loup-Garou) — Discord bot

A complete Werewolf game for Discord, built on [discord.py](https://github.com/Rapptz/discord.py) 2.x
(slash commands, buttons and select menus). Players are told their role by DM; nobody types names
or commands during the game, so the bot needs **no privileged intent**.

## Rules

- Players: 8 to 18.
- Roles: werewolves, villagers, and optional **seer**, **witch**, **cupid**, **hunter**.
- Each night the werewolves eat a villager; each day the village votes to eliminate a suspect.
- The **mayor** is elected on the first day (and re-elected if they die). Their vote counts double and
  they break ties.
- The **witch** has one healing and one poison potion, at most one potion per night.
- The **hunter** takes a player down with them when they die, whatever the cause.
- **Cupid** binds two players on the first night; if one dies the other dies too.
- Village wins when all werewolves are dead; werewolves win when every other player is dead; lovers
  from opposite camps win together if they are the last two alive.

Default number of werewolves (the rest are special roles, then villagers):

|players|werewolves|villagers with seer + witch + cupid + hunter|villagers with only the witch (original table)|
|---|---|---|---|
| 8 | 2 | 2 | 5 |
| 9–11 | 2 | 3–5 | 6–8 |
| 12–18 | 3 | 5–11 | 8–14 |

## Setup

1. Create a bot at <https://discord.com/developers/applications> and copy its token.
2. Invite it with the `bot` and `applications.commands` scopes. Permissions: *View Channels*,
   *Send Messages*, and (optional but recommended) *Manage Channels* so it can create a private
   lair for the werewolves. Without it, werewolves vote in their DMs instead.
   Invite URL template: `https://discord.com/oauth2/authorize?client_id=<APP_ID>&scope=bot+applications.commands&permissions=3088`
3. Install and run (Python 3.10+):

   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env          # then put your token in .env
   python bot.py
   ```

Every player must allow DMs from server members (roles are sent privately). If someone can't be
reached, the bot says who and cancels the game.

## Playing

| Command | What it does |
|---|---|
| `/werewolf start [werewolves] [seer] [witch] [cupid] [hunter] [language]` | Opens a lobby. Players press **Join**; the host presses **Begin**. |
| `/werewolf stop` | Stops the game (host or *Manage Server*). |
| `/werewolf rules` | Shows the rules (English or French, from your Discord language). |

Slash commands can take up to an hour to appear globally the first time. Set `DISCORD_GUILD_ID`
in `.env` to sync to your test server instantly.

## Configuration

See `.env.example`: timings (night actions, discussion, vote), default language (`en`/`fr`),
and `WEREWOLF_MIN_PLAYERS` (minimum 4) to try the bot with fewer people. With few players use
`/werewolf start werewolves:1` and switch off a few roles, otherwise the setup is rejected.

## Project layout

```
bot.py                  entry point
werewolf_bot/
  engine.py             pure game rules (no Discord): roles, deaths, votes, winners
  session.py            one game's flow: night, dawn, mayor, day vote, end
  ui.py                 buttons / select menus (lobby, votes, witch)
  cog.py                /werewolf commands
  i18n.py               English + French texts
  config.py             settings from environment
tests/                  pytest suite (engine, full games with scripted + random players)
```

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest
```

The game flow runs against a scripted "prompter", so the tests play whole games (including 150
random ones) without a Discord connection.
