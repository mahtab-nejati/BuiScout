from utils.helpers import get_mountpoint
from .how import build_process_msg


def init_BuiScout():
    mountpoint = get_mountpoint()
    mountpoint.mkdir(exist_ok=True, parents=True)
    print(
        "Initialization successful! As a reminder, here's the steps you must take:",
        end="\n\n",
    )
    print(build_process_msg())
    print("You can always run the 'how-to' command to see these intructions.")
