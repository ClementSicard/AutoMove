import os
from helper import *
import psutil


def stop_automove():
    if "app.pid" in os.listdir(os.path.dirname(__file__)):
        with open(os.path.join(os.path.dirname(__file__), "app.pid")) as f:
            pid = f.readline()

        if not psutil.pid_exists(int(pid)):
            send_notification(
                message="❌ Oops",
                content=f"Le fichier .pid correspond a aucun processus en cours.",
                important=True
            )

        else:
            os.system(f"kill {pid}")

            print(f"Stopped AutoMove (killed PID [{pid}])")

            send_notification(message=f"✅ AutoMove a bien été arrêté !",
                              content=f"(PID [{pid}])")

        os.remove(os.path.join(os.path.dirname(__file__), "app.pid"))

    else:
        send_notification(
            message=f"🚨 AutoMove n'est pas en cours d'exécution, ou le fichier .pid a été supprimé.",
            important=True,
        )
        exit("AutoMove is not currently running or PID file has been deleted.")


if __name__ == "__main__":
    stop_automove()
