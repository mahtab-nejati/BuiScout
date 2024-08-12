from utils.helpers import get_mountpoint, setup_is_completed
import sys, pathlib

ROOT_PATH = pathlib.Path(__file__).parent


def print_docker_note():
    print(
        '\n\t*** IMOPRTANT: If your are running this on a docker container, the directory "/_BuiScout_mountpoin/" refers to the volume you have mounted on the container. ***\n'
    )


def print_instructions(mountpoint):
    print_docker_note()
    inst_msg = f"{'*'*25}"
    inst_msg += '\nAfter running "scout init"and before running either "scout run", make sure you:'
    inst_msg += f"\n\t1. place your config.json file in \n\t\t{mountpoint}"
    inst_msg += f"\n\t2. for analysis on a local repository, clone your subject project's repository into \n\t\t{mountpoint}"
    inst_msg += "\n\t3. make sure that your config.json points to the correct location for the repository."
    inst_msg += "\n\nThen you can:"
    inst_msg += (
        '\n1. use "scout test" to run a test analysis on ET-Legacy five commits.'
    )
    inst_msg += '\n2. use "scout run" to run BuiScout on your specified subject project based on your config.json file.'
    inst_msg += f'\n{"*"*25}'

    print(inst_msg)
    print_docker_note()


def print_help_msg(mountpoint):
    print_docker_note()
    help_msg = f'{"*"*25}'
    help_msg += "\nBuiScout takes one option at a time."
    help_msg += "\nYour options are:"
    help_msg += '\n\n1. "scout init" to initialize the environement and recieve instructions on how to prepare your environment.'
    help_msg += (
        '\n\tYou must run the "scout init" at least once after BuiScout is set up.'
    )
    help_msg += "\n\tFollow the instructions printed by this command before running any other commands."
    help_msg += (
        '\n\tYou can run "scout init"  at any time to view the instructions again.'
    )
    help_msg += (
        "\n\nAfter a successful initialization, you can use the the following options:"
    )
    help_msg += '\n2. "scout test" to run a series of tests on the ET-Legacy project.'
    help_msg += '\n3. "scout run" to run BuiScout on your specified subject project based on your config.json file.'
    help_msg += f'\n{"*"*25}'

    print(help_msg)
    print_instructions(mountpoint)


if __name__ == "__main__":
    mountpoint = get_mountpoint()
    if len(sys.argv) != 2:
        print_help_msg(mountpoint)
    elif "help" in sys.argv:
        print_help_msg(mountpoint)
    elif "init" in sys.argv:
        mountpoint.mkdir(exist_ok=True, parents=True)
        print("Initialization successful!")
        print_instructions(mountpoint)
    elif set(["test", "run"]).intersection(set(sys.argv)):
        from execute import SAVE_PATH

        print(
            f"Analysis successful!\nIKG data is stored in {mountpoint}/{pathlib.Path(*SAVE_PATH.parts[len(mountpoint.parts):])}"
        )
    else:
        print("This option does not exist!")
        print(print_help_msg(mountpoint))
