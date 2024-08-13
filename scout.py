from utils.helpers import get_mountpoint
import sys, pathlib, argparse
from command_options import how_to_setup_BuiScout, build_msg

ROOT_PATH = pathlib.Path(__file__).parent

bold = "\033[1m"
blue = "\033[34m"
red = "\033[31m"
reset = "\033[0m"

welcome = f"{bold}{blue}Welcome to BuiScout!{reset}\n{bold}{red}Run the 'how-to' command for detailed instructions.{reset}"
parser = argparse.ArgumentParser(description=welcome)
command_parser = parser.add_subparsers(
    dest="command",
    help="Command to execute: 'how-to','init', 'test', or 'run'",
)
init_parser = command_parser.add_parser(
    "how-to",
    help="Prints instructions to successfully run BuiScout.",
)
init_parser = command_parser.add_parser(
    "init",
    help="Initializes the environment by creating the <[BuiScout_ROOT_DIR_PARENT]/_BuiScout_mountpoint> directory.",
)
test_parser = command_parser.add_parser(
    "test",
    help="Runs BuiScout on the configurations in the <[BuiScout_ROOT_DIR]/test/> directory.",
)
run_parser = command_parser.add_parser(
    "run",
    help="Runs BuiScout on the configurations and repositories passed to it in the <[BuiScout_ROOT_DIR_PARENT]/_BuiScout_mountpoint> directory (created by the 'init' option). This will be the volume you mounted on the container if you are running BuiScout in a Docker container.",
)

args = parser.parse_args()

if __name__ == "__main__":
    mountpoint = get_mountpoint()

    if args.command == "how-to":
        from command_options import how_to_setup_BuiScout

        how_to_setup_BuiScout()

    if args.command == "init":
        from command_options import init_BuiScout

        init_BuiScout()

    if args.command == "test":
        from command_options import test_BuiScout

        test_BuiScout()
    if args.command == "run":
        from command_options import run_BuiScout

        run_BuiScout()
