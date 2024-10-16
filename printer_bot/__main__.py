from typing import Tuple
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


class MyPlugin(Plugin):
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
                self.driver.reply_to(message, f'scan funtionality is not yet implemented')
            return

        self.driver.reply_to(message, f'Found some files attached, trying to print...')
        for file_path, file_name in imgs:
            try:
                self.try_print(file_path)
            except Exception as e:
                self.driver.reply_to(message, f'Error during image printing - {e}')
            else:
                self.driver.reply_to(message, f'Printed {file_name}!')

    def try_print(self, file_path: Path) -> None:
        lp_bin_path = shutil.which('lp')
        if lp_bin_path is None:
            raise Exception('`lp` binary not found! Is cups installed?')
        subprocess.run([lp_bin_path, str(file_path.resolve())])

    async def try_get_images(self, message: Message) -> List[Tuple[Path, str]] | None:
        if not 'file_ids' in message.body['data']['post']:
            return None
        file_infos: List[Tuple[Path, str, str]] = [
            (Path(
                f'/tmp/mattermost_printer_bot/{slugify(message_info['id'])}.{message_info['extension']}'), 
             message_info['id'], 
             message_info['name'])
            for message_info in message.body['data']['post']['metadata']['files']]

        for file_path, file_id, file_name in file_infos:
            if file_path.exists():
                print(f'file with id {file_id} already downloaded, skipping')
                continue
            q: Response  = self.driver.files.get_file(file_id)
            if q.status_code != 200:
                raise Exception(f'Non 200 status_code when trying to get image {file_name}! {q.text}')
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'wb') as f:
                    print(f'Saving {file_id} to {file_path}')
                    f.write(q.read())

        return list([(file_path, file_name) for (file_path, _, file_name) in file_infos])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mattermost Bot Token Handler")
    parser.add_argument("mattermost_team", type=str, help="Mattermost team name")
    parser.add_argument("mattermost_url", type=str, help="Mattermost URL")
    parser.add_argument("mattermost_token_file", type=str, help="Path to Mattermost bot token file")

    args = parser.parse_args()

    print(f"Mattermost Team: {args.mattermost_team}")
    print(f"Mattermost URL: {args.mattermost_url}")
    print(f"Mattermost Token File: {args.mattermost_token_file}")

    bot = Bot(
        settings=Settings(
            MATTERMOST_URL = args.mattermost_url,
            MATTERMOST_PORT = 443, # TODO: parametrize?
            BOT_TOKEN = Path(args.mattermost_token_file).read_text().split()[0],
            BOT_TEAM = args.mattermost_team,
            SSL_VERIFY = True,
        ),
        plugins=[
            MyPlugin()
        ],
    )
    bot.run()
