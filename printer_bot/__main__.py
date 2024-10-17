from datetime import datetime
from typing import Tuple
import dateutil
from httpx import Response
from mmpy_bot import Bot, Settings
import argparse
from pathlib import Path
import re
from pathlib import Path
from mmpy_bot.function import listen_to
from mmpy_bot.plugins.base import List, Plugin
from mmpy_bot.wrappers import Message
import shutil
import unicodedata
import subprocess

def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')


class PrinterBotPlugin(Plugin):
    def __init__(self, print_command: str, scan_command: str):
        self.print_command = print_command
        self.scan_command = scan_command

    @listen_to('.*', re.IGNORECASE)
    async def process_any_message(self, message: Message):
        try:
            imgs = await self.try_get_images(message)
        except Exception as e:
            self.driver.reply_to(message, f'Error during image retrieval - {e}')
            return
        
        if (imgs is None) or len(imgs) == 0:
            text: str = message.text
            if not 'scan' in text.lower():
                self.driver.reply_to(message, f'No files attahed. Are you trying to scan? If so, try `scan` command.')
            else:
                self.scan(message)
            return

        self.print_files(imgs, message)

    def scan(self, message: Message) -> None:
        self.driver.reply_to(message, f'Starting scan...')
        try:
            file_path = Path(
                f'/tmp/mattermost_printer_bot/scan/{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.jpeg')
            file_path.parent.mkdir(parents=True, exist_ok=True)
            self.try_scan(file_path)
        except Exception as e:
            self.driver.reply_to(message, f'Error during image scanning - {e}')
        else:
            self.driver.reply_to(message, 'Result', file_paths=[str(file_path.resolve())])


    def print_files(self, imgs: List[Tuple[Path, str]], message: Message) -> None:
        self.driver.reply_to(message, f'Found some files attached, trying to print...')
        for file_path, file_name in imgs:
            try:
                self.try_print(file_path)
            except Exception as e:
                self.driver.reply_to(message, f'Error during image printing - {e}')
            else:
                self.driver.reply_to(message, f'Printed {file_name}!')

    def try_print(self, file_path: Path) -> None:
        self.run_command_expecting_success(f'{self.print_command} {file_path.resolve()}')

    def try_scan(self, file_path: Path) -> None:
        self.run_command_expecting_success(f'{self.scan_command} {file_path.resolve()}')

    def run_command_expecting_success(self, cmd: str) -> None:
        print(f"running command `{cmd}`...")
        proc = subprocess.run([cmd], shell=True, capture_output=True)
        if proc.returncode != 0:
            raise Exception(f'Bad returncode! `{cmd}` returned {proc.returncode}')

    async def try_get_images(self, message: Message) -> List[Tuple[Path, str]] | None:
        if not 'file_ids' in message.body['data']['post']:
            return None
        file_infos: List[Tuple[Path, str, str]] = [
            (Path(
                f'/tmp/mattermost_printer_bot/print/{slugify(message_info['id'])}.{message_info['extension']}'), 
             message_info['id'], 
             message_info['name'])
            for message_info in message.body['data']['post']['metadata']['files']]

        for file_path, file_id, file_name in file_infos:
            if file_path.exists():
                print(f'file with id {file_id} already downloaded, skipping')
                continue
            q: Response  = self.driver.files.get_file(file_id)
            if q.status_code != 200:
                raise Exception(f'{q.status_code} status_code when trying to get image {file_name}! {q.text}')
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'wb') as f:
                    print(f'Saving {file_id} to {file_path}')
                    f.write(q.read())

        return list([(file_path, file_name) for (file_path, _, file_name) in file_infos])

def main():
    parser = argparse.ArgumentParser(description="Mattermost printer bot")
    parser.add_argument("mattermost_url", type=str, help="Mattermost server URL")
    parser.add_argument("mattermost_team", type=str, help="Mattermost team name")
    parser.add_argument("mattermost_token", type=str, help="Mattermost bot token")
    parser.add_argument('-p', '--port', nargs='?', const=443, type=int, default=443, help="Mattermost server port")
    parser.add_argument('-P', '--print', nargs='?', const='lp', type=str, default='lp', help="Custom print command that takes one arg and prints [default = `lp`]")
    parser.add_argument('-S', '--scan', nargs='?', const='scanimage -o', type=str, default='scanimage -o', help="Custom scan command that takes one arg (destination) and scans to it [default - `scanimage -o`]")

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
