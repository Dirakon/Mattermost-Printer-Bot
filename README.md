<h1 align="center">
Mattermost Printer Bot
</h1>
<h4 align="center">Python-based Mattermost bot that can either print out received files or scan images (sending them back as a reply).</h4>

## Requirements

- Python3.x+ (poetry) or nix
- For printing capabilities - some command that can print out arbitrary file by path (i.e. `lp` of cups)
- For scanning capabilities - some command that can scan into given file path (i.e. `scanimage -o` of sane)
- Acessible and running Mattermost server
- Mattermost bot token

## Installation Instruction

### Nix

On systems with nix, you can just use the current repo as a flake input.

I.e.

```nix
# flake.nix
inputs.mattermost-printer-bot.url = "github:Dirakon/Mattermost-Printer-Bot";
```

and

```nix
# flake.nix
outputs = inputs:
{
  # mattermost-printer-bot program is now under inputs.mattermost-printer-bot.packages."${system}".default
  # install it in whatever way suits you
  # ...
}
```

(or use overlays)

### Non-nix

Standard poetry install - see `pyproject.toml`

## CLI Usage

### See help

```console
$ mattermost-printer-bot --help

usage: mattermost-printer-bot [-h] [-p [PORT]] [-P [PRINT]] [-S [SCAN]]
                              mattermost_url mattermost_team mattermost_token

Mattermost printer bot

positional arguments:
  mattermost_url        Mattermost server URL
  mattermost_team       Mattermost team name
  mattermost_token      Mattermost bot token

optional arguments:
  -h, --help            show this help message and exit
  -p [PORT], --port [PORT]
                        Mattermost server port
  -P [PRINT], --print [PRINT]
                        Custom print command that takes one arg and prints
                        [default = `lp`]
  -S [SCAN], --scan [SCAN]
                        Custom scan command that takes one arg (destination)
                        and scans to it [default - `scanimage -o`]
```

### Example of running it

```bash
mattermost-printer-bot "https://example.mattermost.server.com" "TEAM_NAME" "SOME_REAL_BOT_TOKEN"
```

## In-Mattermost usage

### Print

Any message with files in it received by the bot will call the provided print command once for each file (with the path to a downloaded copy of the sent file as an argument to the command).

### Scan

Any message without files and with word `scan` in it received by the bot will call the provided scan command. After the scan command finishes, the file is sent back as a reply through Mattermost.

## Development

To get started, run the following:

```console
$ nix develop
$ poetry install
$ poetry run python -m printer_bot *ARG1* *ARG2* ....
```

## License

This Project is licensed under the MIT License. Check license file for more info.
