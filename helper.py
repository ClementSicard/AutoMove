import os
import re
from typing import Tuple
import psutil

SERIES_REGEXP = r"\w+ - S\d*.*.\w+$"
HW_REGEXP = r"\w+ - HW\d*.*.\w+$"
EXAM_REGEXP = r"\w+ - E\d*.*.\w+$"
REVISION_REGEXP = r"\w+ - R\d*.*.\w+$"
LECTURE_REGEXP = r"\w+ - (\d*|Lecture notes|SLIDES|Slides).*.\w+$"
CS_REGEXP = r"\w+ - (Summary|Tricks|Useful to know|Cheatsheet|Formulaire)*.*.\w+$"
DIRNAME = os.path.dirname(__file__)
PATH_TO_INI_FILE = os.path.join(os.path.dirname(__file__), "config.ini")
PATH_TO_ALERTER = os.path.join(os.path.dirname(__file__), "res", "./alerter")
BUNDLE_ID = "com.apple.automator.AutoMove"

TIMEOUT = 4
IMPORTANT_TIMEOUT = 6


def send_notification(
    message: str,
    content="",
    error=False,
    important=False
):
    """Sends a terminal notification whenever something important happens during runtime.

    Args:

        `message` (`str`): Title of the notification

        `content` (`str`): Text content of the notification

        `error` (`bool`): Changes the timeout if there is an error. Defaults to `False`.

        `important` (`bool`): Changes timeout if it is important.
    """

    content_string = f'-message "{content}"'
    timeout_string = f"-timeout {IMPORTANT_TIMEOUT}" if important else f"-timeout {TIMEOUT}" if not error else ""

    cmd = f'{PATH_TO_ALERTER} -title "AutoMove" -sender {BUNDLE_ID} {timeout_string} -subtitle "{message}" {content_string if message else ""} -sound {"Blow" if error else "Glass"} > /dev/null 2>&1 &'

    os.system(cmd)


def checkPID() -> Tuple[bool, int]:
    """Checks whether the app is already running, and quits if so."""

    if "app.pid" in os.listdir(os.path.dirname(__file__)):
        with open(os.path.join(os.path.dirname(__file__), "app.pid"), "r") as f:
            pid = f.readline()

        if psutil.pid_exists(int(pid)):
            send_notification(
                message="❌ Oops",
                content=f"Une instance est déjà en cours [PID {pid}]",
                important=True
            )

            exit(f"AutoMove already running with PID {pid}")

        else:
            os.remove(os.path.join(os.path.dirname(__file__), "app.pid"))

            pid = os.getpid()
            path = os.path.join(os.path.dirname(__file__), "app.pid")
            with open(path, "w") as f:
                f.write(f'{pid}')

        return False, pid

    else:
        pid = os.getpid()
        path = os.path.join(os.path.dirname(__file__), "app.pid")
        with open(path, "w") as f:
            f.write(f'{pid}')

        return True, pid


def modified_path_with_regex(file_name: str) -> str:
    """Generates the arborescent-structure path infered by the name of a file, following rules given by above regular expressions

    Args:
        `file_name` (`str`): Name of the file we want to transform

    Returns:
        `str`: The modified path
    """

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
