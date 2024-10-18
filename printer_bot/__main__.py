from mmpy_bot import Bot, Settings
import argparse
from printer_bot.plugin import PrinterBotPlugin



def main():
    parser = argparse.ArgumentParser(description="Mattermost printer bot")
    parser.add_argument("mattermost_url", type=str, help="Mattermost server URL")
    parser.add_argument("mattermost_team", type=str, help="Mattermost team name")
    parser.add_argument("mattermost_token", type=str, help="Mattermost bot token")
    parser.add_argument('-p', '--port', nargs='?', const=443, type=int, default=443, help="Mattermost server port")
    parser.add_argument('-P', '--print', nargs='?', const='lp', type=str, default='lp', help="Custom print command that takes one arg and prints [default = `lp`]")
    parser.add_argument('-S', '--scan', nargs='?', const='scanimage -o', type=str, default='scanimage -o', help="Custom scan command that takes one arg (destination) and scans to it [default = `scanimage -o`]")

    args = parser.parse_args()

    bot = Bot(
        settings=Settings(
            MATTERMOST_URL = args.mattermost_url,
            MATTERMOST_PORT = args.port,
            BOT_TOKEN = args.mattermost_token,
            BOT_TEAM = args.mattermost_team,
            SSL_VERIFY = True,
        ),
        plugins=[
            PrinterBotPlugin(args.print, args.scan)
        ],
    )
    bot.run()


if __name__ == "__main__":
    main()
