from utils.helpers import indent_text


def build_process_msg():
    bold = "\033[1m"
    red = "\033[31m"
    green = "\033[32m"
    reset = "\033[0m"

    msg = f"{bold}{red}To successfully run BuiScout, follow these steps:{reset}\n"
    msg += f"1. Run the 'init' command.\n"
    msg += (
        indent_text(
            f"This will creat a directory named {bold}_BuiScout_mountpoint{reset} in the {bold}parent directory of '[BuiScout_ROOT_DIR]'{reset}."
        )
        + "\n"
    )
    msg += (
        indent_text(
            f"{bold}{green}If you are running this on a docker container, this directory is equivalent to the volume you have mounted on the container.{reset}"
        )
        + "\n"
    )
    msg += f'2. Follow the {bold}{red}"Prepare config.json"{reset} in the README to create your config.json file in the {bold}_BuiScout_mountpoint{reset} from step 1.\n'
    msg += f"3. If you are running BuiScout on a local subject repository, place this repository in the {bold}_BuiScout_mountpoint{reset} from step 1.\n"
    msg += (
        "4. Run the 'run' command to execute analysis based on your configurations.\n"
    )

    return msg


def build_msg():
    bold = "\033[1m"
    blue = "\033[34m"
    reset = "\033[0m"

    msg = (
        f"{bold}{blue}Welcome to BuiScout! BuiScout scouts impact of your changes on build specifications.{reset}"
        + "\n" * 2
    )
    msg += (
        f"So far, BuiScout supports CMake build systems. Don't hesitate to reach out if you want to contribute to support other technologies."
        + "\n" * 2
    )
    msg += build_process_msg()
    msg += f"\nAdditionally, you can run the 'test' command.\n"
    msg += (
        indent_text(
            f"This will run a test on 7 commits (2 skipped, 5 analyzed) from the ET-Legacy project. Running the test requires internet connection to access the ET-Legacy project. The config.json file for this test is located at '[BuiScout_ROOT_DIR]/test'.",
        )
        + "\n"
    )

    return msg


def how_to_setup_BuiScout():
    print(build_msg())
