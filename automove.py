import paramiko
import configparser
import shutil
import os
import glob
import time
import configparser
import pync
import re
import paramiko
from fnmatch import fnmatch
from typing import List

SERIES_REGEXP = r"\w+ - S\d*.*.\w+$"
HW_REGEXP = r"\w+ - HW\d*.*.\w+$"
EXAM_REGEXP = r"\w+ - E\d*.*.\w+$"
REVISION_REGEXP = r"\w+ - R\d*.*.\w+$"
LECTURE_REGEXP = r"\w+ - (\d*|Lecture notes|SLIDES|Slides).*.\w+$"
CS_REGEXP = r"\w+ - (Summary|Tricks|Useful to know|Cheatsheet|Formulaire)*.*.\w+$"

PATH_TO_INI_FILE = "/Users/clementsicard/Developer/GitHub/Automove/config.ini"


class AutoMove:

    args: dict
    sftp_bool: bool
    sftp: paramiko.SFTPClient
    sftp_backup_path: str
    sftp_path: str
    icloud_path: str
    new_paths: List[str]
    tmp_paths: List[str]
    onedrive_path: str
    host: str
    port: int
    account: str
    pw: str

    def __init__(self, args: dict):
        config = configparser.ConfigParser()
        config.read(PATH_TO_INI_FILE)
        self.args = args
        self.sftp_bool = self.args["sftp"]

        self.icloud_path = config["PATHS"]["icloud_path"]
        self.onedrive_path = config["PATHS"]["onedrive_path"]

        if self.sftp_bool:
            self.sftp_path = config["PATHS"]["sftp_path"]
            self.sftp_backup_path = config["PATHS"]["sftp_backup_path"]
            self.host = config["SFTP"]["sftp_host"]
            self.port = int(config["SFTP"]["sftp_port"])
            self.account = config["SFTP"]["sftp_account"]
            self.pw = config["SFTP"]["sftp_pw"]
            self.sftp = self.__connect_to_SFTP()
            self.sftp.chdir(self.sftp_backup_path)

        pync.notify("📣 AutoMove a démarré !", title="AutoMove 🔁", actions="Close",
                    execute=f'open "{self.icloud_path}"')

    def run(self):
        nothing = False

        while True:
            icloud_folders = [folder for folder in next(os.walk(self.icloud_path))[
                1] if folder[0] != "."]

            self.tmp_paths = []
            self.new_paths = []

            for folder in icloud_folders:
                files_to_upload_by_folder = self.__get_files_to_upload(folder)

                if files_to_upload_by_folder:
                    self.tmp_paths.extend(files_to_upload_by_folder)

            if self.tmp_paths:
                nothing = False

                self.__copy_files_to_icloud()
                print("Done copying to iCloud")

                if self.sftp_bool:
                    self.__backup_files_on_NAS()
                    print("Done backing up files to NAS")

            elif not nothing:
                nothing = True

            time.sleep(1)

    def __connect_to_SFTP(self) -> paramiko.SFTPClient:
        transport = paramiko.Transport((self.host, self.port))
        transport.connect(None, self.account, self.pw)
        client = paramiko.SFTPClient.from_transport(transport)
        print("[SFTP] Connected to NAS.")
        return client

    def __get_files_to_upload(self, folder: str) -> List[str]:
        to_return = []

        folder_path = os.path.join(self.sftp_backup_path, folder) if self.sftp_bool else os.path.join(
            self.onedrive_path, folder)

        if self.__sftp_exists(folder_path) if self.sftp_bool else os.path.exists(folder_path):
            for f in self.sftp.listdir(folder_path) if self.sftp_bool else os.listdir(folder_path):
                if fnmatch(f, "*.pdf") and not f.startswith("."):
                    to_return.append(os.path.join(folder, f))
            return to_return
        else:
            return []

    def __sftp_exists(self, path: str) -> bool:
        try:
            self.sftp.stat(path)
            return True

        except FileNotFoundError:
            return False

    def __copy_files_to_icloud(self) -> None:
        try:
            silent = False
            # silent = len(self.tmp_paths) > 1
            err = False

            for f in self.tmp_paths:
                new_path = modified_path_with_regex(f)
                self.new_paths.append(new_path)

                file_name = f[f.rfind("/") + 1:]

                test_icloud_path = os.path.join(self.icloud_path, new_path)
                path_exists_on_icloud = os.path.exists(test_icloud_path)

                if not path_exists_on_icloud:
                    if new_path == f:
                        try:
                            if self.sftp_bool:
                                self.sftp.get(os.path.join(self.sftp_backup_path, f),
                                              os.path.join(self.icloud_path, f))
                            else:
                                shutil.move(os.path.join(self.onedrive_path, f),
                                            os.path.join(self.icloud_path, f))

                            if not silent:
                                pync.notify(f"❓ Oups! Path inconnu\n{file_name} a été déplacé à la racine du dossier.",
                                            title="AutoMove 🔁", actions="Close", execute=f'open "{os.path.join(self.icloud_path, f)}"')
                        except FileNotFoundError:
                            err = True
                            pync.notify(f"❌ Oups, impossible de déplacer {file_name}.",
                                        title="AutoMove 🔁", actions="Close")
                    else:
                        try:
                            if self.sftp_bool:
                                self.sftp.get(os.path.join(self.sftp_backup_path, f),
                                              os.path.join(self.icloud_path, new_path))
                            else:
                                shutil.move(os.path.join(self.onedrive_path, f),
                                            os.path.join(self.icloud_path, new_path))

                            if not silent:
                                pync.notify(f"✅ {file_name} a été déplacé depuis {'le NAS' if self.sftp_bool else 'OneDrive'} vers iCloud.", title="AutoMove 🔁",
                                            actions="Close", execute=f'open "{os.path.join(self.icloud_path, new_path)}"')
                        except FileNotFoundError:
                            err = True
                            pync.notify(f"❌ Oups, impossible de déplacer {file_name}.",
                                        title="AutoMove 🔁", actions="Close")

                else:
                    if self.sftp_bool:
                        self.sftp.get(os.path.join(self.sftp_backup_path, f),
                                      os.path.join(self.icloud_path, new_path))
                    else:
                        shutil.move(os.path.join(self.onedrive_path, f),
                                    os.path.join(self.icloud_path, new_path))

                    if not silent:
                        pync.notify(f"✅ {file_name} a été mis à jour sur iCloud.", title="AutoMove 🔁",
                                    actions="Close", execute=f'open "{os.path.join(self.icloud_path, new_path)}"')

                if self.sftp_bool:
                    self.__backup_on_NAS(f, new_path)

            if silent and not err:
                pync.notify(f"✅  Bonne nouvelle ! \n{len(self.tmp_paths)} fichier(s) copiés sur iCloud.",
                            title="AutoMove 🔁", actions="Close", execute=f'open "{self.icloud_path}"')
            elif silent and err:
                pync.notify(f"❌ Oups, il y a eu une erreur pendant la sauvegarde des fichiers sur iCloud.",
                            title="AutoMove 🔁", actions="Close")

        except FileNotFoundError:
            pync.notify(f"❓ Oups! Soucis de path sur {'le NAS' if self.sftp_bool else 'OneDrive'}...\nCliquer pour debug",
                        title="AutoMove 🔁", actions="Close", execute=f'code "/Users/clementsicard/Developer/GitHub/Automove"')

    def __backup_files_on_NAS(self) -> None:
        self.new_paths = [modified_path_with_regex(
            path) for path in self.tmp_paths]

        for tmp_path, new_path in zip(self.tmp_paths, self.new_paths):
            print(tmp_path, new_path)
            self.__backup_on_NAS(tmp_path, new_path)

    def __backup_on_NAS(self, tmp_path: str, new_path: str) -> None:
        try:

            print(os.path.join(self.sftp_backup_path, tmp_path))
            print(os.path.join(self.sftp_path, new_path))
            print(self.__sftp_exists(os.path.dirname(
                os.path.join(self.sftp_path, new_path))))
            print()
            self.sftp.posix_rename(os.path.join(self.sftp_backup_path, tmp_path),
                                   os.path.join(self.sftp_path, new_path))

        except EOFError:
            pync.notify(f"❓ Oups! Soucis de path pour la sauvegarde sur le NAS...\nCliquer pour debug",
                        title="AutoMove 🔁", actions="Close", execute=f'code "/Users/clementsicard/Developer/GitHub/Automove"')

    def close(self):
        self.sftp.close()


def modified_path_with_regex(file_name) -> str:
    if re.search(SERIES_REGEXP, file_name):
        idx = file_name[1:].find("/") + 1
        return file_name[:idx + 1] + "EXERCIZES" + file_name[idx:]
    elif re.search(HW_REGEXP, file_name):
        idx = file_name[1:].find("/") + 1
        return file_name[:idx + 1] + "HOMEWORKS" + file_name[idx:]
    elif re.search(LECTURE_REGEXP, file_name):
        idx = file_name[1:].find("/") + 1
        return file_name[: idx + 1] + "LECTURES" + file_name[idx:]
    elif re.search(CS_REGEXP, file_name):
        idx = file_name[1:].find("/") + 1
        return file_name[: idx + 1] + "CHEATSHEETS" + file_name[idx:]
    elif re.search(EXAM_REGEXP, file_name):
        idx = file_name[1:].find("/") + 1
        return file_name[: idx + 1] + "EXAMS" + file_name[idx:]
    elif re.search(REVISION_REGEXP, file_name):
        idx = file_name[1:].find("/") + 1
        return file_name[: idx + 1] + "REVISIONS" + file_name[idx:]
    else:
        return file_name
