import os
from helper import *


def stop_automove():
    if "PID" in os.listdir(os.path.dirname(__file__)):
        with open(os.path.join(os.path.dirname(__file__), "PID")) as f:
            pid = f.readline()
        os.system(f"kill {pid}")
        os.remove(os.path.join(os.path.dirname(__file__), "PID"))

        print(f"Stopped AutoMove (killed PID [{pid}])")

        send_notification(message=f"✅ AutoMove a bien été arrêté !",
                          content=f"(PID [{pid}])")

    else:
        send_notification(
            message=f"🚨 AutoMove is not currently running, or PID file has been deleted.",
            important=True,
        )
        exit("AutoMove is not currently running or PID file has been deleted.")


if __name__ == "__main__":
    stop_automove()
