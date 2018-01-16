# AnonBot

A bot to allow simple anonymous posting on discord by forwarding DM message to a certain pre-configured channel on user's behalf.

## Usage (User)

Make sure you have the corresponding authorization. You just need to DM the bot. It will forward your message to the anonymous channel.

## Usage (Admin)

1. Clone
   ```console
   $ git clone https://github.com/8zu/anon-bot.git
   ```

2. Install dependencies
   ```console
   $ pip install -r requirements.txt
   ```

3. Fill in token in `config.toml` with a token from a bot user created at [discord developer console](https://discordapp.com/developers/applications/me).

4. Run the bot `python bot.py` and wait for it to spring up

5. Initialize
   First you need to prepare
    1. a **role** to be eligible to post anonymously, (you can also use `@everyone`)
    2. a channel for the bot to forward message to
    3. [header text](#header)

   You can run
   ```
   ?init
   ```
   in any channel and the bot should guide you through the initialization process

###<a name="header"></a> Header syntax

The header supports simple substitution syntax through string interpolation

1. `{counter}`: a monotonically increasing counter. Showing four digits (0000~9999)
2. `id`: a RNG'ed string of five digits (10000~99999). The "id" doesn't really identify the user.
