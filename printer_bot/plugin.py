from datetime import datetime
from typing import Tuple
from httpx import Response
from pathlib import Path
import re
from pathlib import Path
from mmpy_bot.function import listen_to
from mmpy_bot.plugins.base import List, Plugin
from mmpy_bot.wrappers import Message
import subprocess
import sys
from printer_bot.utils import truncate_str, slugify


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
                self.driver.reply_to(
                    message, 
                    f'No files attahed. Are you trying to scan? If so, try `scan` command.')
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
            raise Exception(f'Bad returncode! `{cmd}` returned {proc.returncode}:' +
                f'\n```\n{truncate_str(proc.stderr.decode(sys.stderr.encoding), 500)}\n```')

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
