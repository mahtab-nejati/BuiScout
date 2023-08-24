from datetime import datetime
from pathlib import Path
import subprocess, time, importlib
from collections import defaultdict
from utils.helpers import (
    file_is_target,
    get_file_dir,
    get_processed_path,
    write_source_code,
    read_dotdiff,
)
from diff_model import ASTDiff
from utils.configurations import DATA_FLOW_ANALYSIS_MODE
from utils.exceptions import DebugException


class SystemDiff(object):
    """
    Represents a pair of system-level ASTs with their corresponding diff.
    System-level ASTs are generated by replacing an "include" command
    with the root of the included file's AST.
    DATA_FLOW_ANALYSIS_MODE can be any of 'CHANGE_LOCATION', 'CHANGE_PROPAGATION', or 'GLOBAL'. Default is 'CHANGE_LOCATION'.
    """

    mode = DATA_FLOW_ANALYSIS_MODE.lower()

    def __init__(
        self,
        repository_path,
        repository,
        git_repository,
        branch,
        commit,
        root_file,
        language,
        patterns,
        root_path,
        save_path,
        *args,
        **kwargs,
    ):
        self.repository_path = repository_path
        self.repository = repository
        self.git_repository = git_repository
        self.branch = branch
        self.commit = commit

        self.root_file = root_file
        self.language = language
        self.patterns = patterns

        self.root_path = root_path
        self.save_path = save_path

        # Storing lists of du_chains
        self.source_du_chains = []
        self.destination_du_chains = []

        self.set_paths()

        self.file_data = {}.copy()
        self.populate_file_data()

        # Import language support tools but not saved as an attribute
        # for pickling reasons
        language_support_tools = importlib.import_module(
            f"language_supports.{self.language}"
        )
        self.DefUseChains = language_support_tools.DefUseChains

    def set_paths(self):
        self.commit_dir = self.save_path / "commits" / self.commit.hash
        self.code_dir = self.commit_dir / "code"

        # Build files before change
        self.before_dir = self.code_dir / "before"
        self.before_dir.mkdir(parents=True, exist_ok=True)

        # Build files after change
        self.after_dir = self.code_dir / "after"
        self.after_dir.mkdir(parents=True, exist_ok=True)

        # GumTree output setup
        self.gumtree_output_dir = self.commit_dir / "gumtree_output"
        self.gumtree_output_dir.mkdir(parents=True, exist_ok=True)

    def populate_file_data(self):
        self.git_repository.checkout(self.commit.hash)
        time.sleep(5)

        self.set_file_data()
        self.set_file_data_diffs()

        self.git_repository.checkout(self.branch)
        time.sleep(5)

    def set_file_data_modified_only(self):
        self.file_data = dict(
            map(
                lambda file_data: (
                    file_data["file_dir"] + file_data["file_name"],
                    file_data,
                ),
                map(
                    lambda modified_file: {
                        "commit_hash": self.commit.hash,
                        "file_dir": get_file_dir(modified_file),
                        "file_name": modified_file.filename,
                        "build_language": self.language,
                        "file_action": str(modified_file.change_type).split(".")[-1],
                        "before_path": modified_file.old_path,
                        # code_before will be removed once written to a file
                        "code_before": modified_file.source_code_before,
                        "after_path": modified_file.new_path,
                        # code_after will be removed once written to a file
                        "code_after": modified_file.source_code,
                        "saved_as": get_processed_path(modified_file),
                        "has_gumtree_error": False,
                        "data_flow_source_reach": False,
                        "data_flow_destination_reach": False,
                        "language_specific_info": defaultdict(list),
                    },
                    filter(
                        lambda modified_file: file_is_target(
                            modified_file, self.patterns
                        ),
                        self.commit.modified_files,
                    ),
                ),
            )
        )

    def set_file_data_non_modified_only(self):
        # Non-modified build files at the commit checkpoint
        other_build_files = filter(
            lambda file_path: file_is_target(file_path, self.patterns)
            and file_path not in self.file_data.keys(),
            map(
                lambda full_path: full_path.replace(self.repository_path + "/", ""),
                self.git_repository.files(),
            ),
        )

        self.file_data.update(
            dict(
                map(
                    lambda build_file_path: (
                        build_file_path,
                        {
                            "commit_hash": self.commit.hash,
                            "file_dir": "/".join(build_file_path.split("/")[:-1]) + "/",
                            "file_name": build_file_path.split("/")[-1],
                            "build_language": self.language,
                            "file_action": None,
                            "before_path": build_file_path,
                            "code_before": "",
                            "after_path": build_file_path,
                            "code_after": Path(
                                Path(self.repository_path) / build_file_path
                            ).read_text(),
                            "saved_as": build_file_path.replace("/", "__").strip(),
                            "has_gumtree_error": False,
                            "data_flow_source_reach": False,
                            "data_flow_destination_reach": False,
                            "language_specific_info": defaultdict(list),
                        },
                    ),
                    other_build_files,
                )
            )
        )

    def set_file_data(self):
        self.set_file_data_modified_only()
        if self.mode != "change_location":
            self.set_file_data_non_modified_only()

    def write_code_files(self, file_path):
        write_source_code(
            self.after_dir / self.file_data[file_path]["saved_as"],
            self.file_data[file_path]["code_after"],
        )
        del self.file_data[file_path]["code_after"]

        write_source_code(
            self.before_dir / self.file_data[file_path]["saved_as"],
            self.file_data[file_path]["code_before"],
        )
        del self.file_data[file_path]["code_before"]

    def run_gumtree_on_file(self, file_path):
        command = [
            str(self.root_path / "process.sh"),
            str(self.language),
            str(self.code_dir),
            str(self.file_data[file_path]["saved_as"]),
            str(self.gumtree_output_dir),
        ]
        process = subprocess.Popen(command, stdout=subprocess.PIPE)
        output, error = process.communicate()
        # with open(f"{self.gumtree_output_dir}/get_webdiff.txt", "a") as f:
        #     f.write(
        #         f"gumtree webdiff -g {self.language}-treesitter "
        #         + f'{self.commit_dir}/before/{self.file_data[file_path]["saved_as"]} '
        #         + f'{self.commit_dir}/after/{self.file_data[file_path]["saved_as"]}\n'
        #     )

    def read_gumtree_output(self, file_path):
        try:
            dotdiff_content = read_dotdiff(
                f'{self.gumtree_output_dir}/{self.file_data[file_path]["saved_as"]}_dotdiff.dot'
            )
            return True, dotdiff_content
        except:
            self.file_data[file_path]["has_gumtree_error"] = True
            return False, ""

    def get_file_diff(self, file_path):
        self.write_code_files(file_path)
        self.run_gumtree_on_file(file_path)
        gumtree_success, dotdiff_content = self.read_gumtree_output(file_path)

        if gumtree_success:
            return ASTDiff(
                *dotdiff_content,
                self.file_data[file_path]["file_action"],
                file_path,
                self.file_data[file_path]["saved_as"],
                self.commit.hash,
                self.language,
            )

        else:
            return None

    def set_file_data_diffs(self):
        for file_path, file_data in self.file_data.items():
            self.file_data[file_path]["diff"] = self.get_file_diff(file_path)

    def perform_data_flow_analysis(self):
        analysis_method = "analyze_" + self.mode
        analyzer = getattr(self, analysis_method, self.analyze_global)
        analyzer()

    def analyze_change_location(self):
        for file_path, file_data in self.file_data.items():
            if file_data["diff"]:
                print(f"{'#'*10} {file_path} {'#'*10}")

                self.source_du_chains.append(
                    self.DefUseChains(file_data["diff"].source)
                )
                print(f"{'#'*10} Analyzing source {'#'*10}")
                self.source_du_chains[-1].analyze()

                self.destination_du_chains.append(
                    self.DefUseChains(file_data["diff"].destination)
                )
                print(f"{'#'*10} Analyzing source {'#'*10}")
                self.destination_du_chains[-1].analyze()

    def analyze_global(self):
        # Skip if the self.root_file has GumTree error
        if self.file_data[self.root_file]["diff"] is None:
            return

        self.source_du_chains.append(
            self.DefUseChains(
                self.file_data[self.root_file]["diff"].source, sysdiff=self
            )
        )
        print(f"{'#'*10} Analyzing source {'#'*10}")
        self.source_du_chains[-1].analyze()

        self.destination_du_chains.append(
            self.DefUseChains(
                self.file_data[self.root_file]["diff"].destination, sysdiff=self
            )
        )
        print(f"{'#'*10} Analyzing destination {'#'*10}")
        self.destination_du_chains[-1].analyze()

    def get_file_directory(self, file_path):
        return self.file_data[file_path]["file_dir"]

    def set_data_flow_reach_file(self, file_path, cluster):
        self.file_data[file_path][f"data_flow_{cluster}_reach"] = True

    def export_json(self):
        save_path = self.commit_dir / "data_flow_output"
        Path(save_path).mkdir(parents=True, exist_ok=True)

        if self.source_du_chains:
            list(map(lambda chain: chain.export_json(save_path), self.source_du_chains))

        if self.destination_du_chains:
            list(
                map(
                    lambda chain: chain.export_json(save_path),
                    self.destination_du_chains,
                )
            )

        list(
            map(
                lambda file_data: file_data["diff"].export_json(save_path),
                filter(
                    lambda file_data: (file_data["diff"] is not None),
                    self.file_data.values(),
                ),
            )
        )

    def export_csv(self):
        save_path = self.commit_dir / "data_flow_output"
        Path(save_path).mkdir(parents=True, exist_ok=True)

        if self.source_du_chains:
            list(map(lambda chain: chain.export_csv(save_path), self.source_du_chains))

        if self.destination_du_chains:
            list(
                map(
                    lambda chain: chain.export_csv(save_path),
                    self.destination_du_chains,
                )
            )

        list(
            map(
                lambda file_data: file_data["diff"].export_csv(save_path),
                filter(
                    lambda file_data: (file_data["diff"] is not None),
                    self.file_data.values(),
                ),
            )
        )


class SystemDiffShortcut(SystemDiff):
    def set_file_data_modified_only(self):
        self.file_data = dict(
            map(
                lambda file_data: (
                    file_data["file_dir"] + file_data["file_name"],
                    file_data,
                ),
                map(
                    lambda modified_file: {
                        "commit_hash": self.commit.hash,
                        "file_dir": get_file_dir(modified_file),
                        "file_name": modified_file.filename,
                        "build_language": self.language,
                        "file_action": str(modified_file.change_type).split(".")[-1],
                        "before_path": modified_file.old_path,
                        "after_path": modified_file.new_path,
                        "saved_as": get_processed_path(modified_file),
                        "has_gumtree_error": False,
                        "data_flow_source_reach": False,
                        "data_flow_destination_reach": False,
                        "language_specific_info": defaultdict(list),
                    },
                    filter(
                        lambda modified_file: file_is_target(
                            modified_file, self.patterns
                        ),
                        self.commit.modified_files,
                    ),
                ),
            )
        )

    def set_file_data_non_modified_only(self):
        # Non-modified build files at the commit checkpoint
        other_build_files = filter(
            lambda file_path: file_is_target(file_path, self.patterns)
            and file_path not in self.file_data.keys(),
            map(
                lambda full_path: full_path.replace(self.repository_path + "/", ""),
                self.git_repository.files(),
            ),
        )

        self.file_data.update(
            dict(
                map(
                    lambda build_file_path: (
                        build_file_path,
                        {
                            "commit_hash": self.commit.hash,
                            "file_dir": "/".join(build_file_path.split("/")[:-1]) + "/",
                            "file_name": build_file_path.split("/")[-1],
                            "build_language": self.language,
                            "file_action": None,
                            "before_path": build_file_path,
                            "after_path": build_file_path,
                            "saved_as": build_file_path.replace("/", "__").strip(),
                            "has_gumtree_error": False,
                            "data_flow_source_reach": False,
                            "data_flow_destination_reach": False,
                            "language_specific_info": defaultdict(list),
                        },
                    ),
                    other_build_files,
                )
            )
        )

    def get_file_diff(self, file_path):
        gumtree_success, dotdiff_content = self.read_gumtree_output(file_path)

        if gumtree_success:
            return ASTDiff(
                *dotdiff_content,
                self.file_data[file_path]["file_action"],
                file_path,
                self.file_data[file_path]["saved_as"],
                self.commit.hash,
                self.language,
            )

        else:
            return None


class SystemDiffSeries(SystemDiff):
    def set_paths(self):
        self.commit_dir = self.save_path / "commits" / self.commit.hash
        self.code_dir = self.save_path / "code"

        # Build files before change
        self.before_dir = self.code_dir / "before"
        self.before_dir.mkdir(parents=True, exist_ok=True)

        # Build files after change
        self.after_dir = self.code_dir / "after"
        self.after_dir.mkdir(parents=True, exist_ok=True)

        # GumTree output setup
        self.gumtree_output_dir = self.save_path / "gumtree_output"
        self.gumtree_output_dir.mkdir(parents=True, exist_ok=True)

    def set_file_data_non_modified_only(self):
        # Non-modified build files at the commit checkpoint
        other_build_files = filter(
            lambda file_path: file_is_target(file_path, self.patterns)
            and file_path not in self.file_data.keys(),
            map(
                lambda full_path: full_path.replace(self.repository_path + "/", ""),
                self.git_repository.files(),
            ),
        )

        self.file_data.update(
            dict(
                map(
                    lambda build_file_path: (
                        build_file_path,
                        {
                            "commit_hash": self.commit.hash,
                            "file_dir": "/".join(build_file_path.split("/")[:-1]) + "/",
                            "file_name": build_file_path.split("/")[-1],
                            "build_language": self.language,
                            "file_action": None,
                            "before_path": build_file_path,
                            "after_path": build_file_path,
                            "saved_as": build_file_path.replace("/", "__").strip(),
                            "has_gumtree_error": False,
                            "data_flow_source_reach": False,
                            "data_flow_destination_reach": False,
                            "language_specific_info": defaultdict(list),
                        },
                    ),
                    other_build_files,
                )
            )
        )

    def get_modified_file_diff(self, file_path):
        self.write_code_files(file_path)
        self.run_gumtree_on_file(file_path)
        gumtree_success, dotdiff_content = self.read_gumtree_output(file_path)

        if gumtree_success:
            return ASTDiff(
                *dotdiff_content,
                self.file_data[file_path]["file_action"],
                file_path,
                self.file_data[file_path]["saved_as"],
                self.commit.hash,
                self.language,
            )

        else:
            write_source_code(
                self.before_dir / self.file_data[file_path]["saved_as"],
                "",
            )
            self.run_gumtree_on_file(file_path)
            gumtree_success, dotdiff_content = self.read_gumtree_output(file_path)

            if gumtree_success:
                return ASTDiff(
                    *dotdiff_content,
                    self.file_data[file_path]["file_action"],
                    file_path,
                    self.file_data[file_path]["saved_as"],
                    self.commit.hash,
                    self.language,
                )

        return None

    def get_non_modified_file_diff(self, file_path):
        gumtree_success, dotdiff_content = self.read_gumtree_output(file_path)

        if (not gumtree_success) or (
            not Path(self.after_dir / self.file_data[file_path]["saved_as"]).exists()
        ):
            self.write_non_modified_code_files(file_path)
            self.run_gumtree_on_file(file_path)
            gumtree_success, dotdiff_content = self.read_gumtree_output(file_path)

        if gumtree_success:
            return ASTDiff(
                *dotdiff_content,
                self.file_data[file_path]["file_action"],
                file_path,
                self.file_data[file_path]["saved_as"],
                self.commit.hash,
                self.language,
            )

        else:
            return None

    def write_non_modified_code_files(self, file_path):
        write_source_code(
            self.after_dir / self.file_data[file_path]["saved_as"],
            Path(
                Path(self.repository_path) / self.file_data[file_path]["after_path"]
            ).read_text(),
        )

        write_source_code(
            self.before_dir / self.file_data[file_path]["saved_as"],
            "",
        )

    def get_file_diff(self, file_path):
        if self.file_data[file_path]["file_action"] is None:
            return self.get_non_modified_file_diff(file_path)

        return self.get_modified_file_diff(file_path)
