from pathlib import Path
import pandas as pd
import subprocess, time, importlib, json, itertools
from collections import defaultdict
from functools import reduce
from utils.helpers import (
    file_is_target,
    get_file_dir,
    get_processed_path,
    write_source_code,
    read_dotdiff,
)
from diff_model import ASTDiff
from utils.configurations import DATA_FLOW_ANALYSIS_MODE


class SystemDiff(object):
    """
    Represents a pair of system-level ASTs with their corresponding diff.
    System-level ASTs are generated by replacing an "include" command
    with the root of the included file's AST.
    DATA_FLOW_ANALYSIS_MODE can be any of 'CHANGE_LOCATION', 'CHANGE_PROPAGATION', or 'GLOBAL'. Default is 'CHANGE_LOCATION'.
    """

    analysis_mode = DATA_FLOW_ANALYSIS_MODE.lower()

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

        # Storing lists of cdu_chains
        self.source_cdu_chains = []
        self.destination_cdu_chains = []

        """
        Each propagation slice is a list of dictionaries representing the 
        propagation relationships in the form of a Knowledge Graph (KD). 
        Each entry of the list is one relationship stored as a dictionary. 
        The dictionaries have the following structure:
            {
                'subject': some_object (Def,Use,Actor,CondtionalDefUseChains),
                'subject_id': 'str_id',
                'subject_type': the_class,
                'propagation_rule': 'str_rule',
                'object': some_object (Def,Use,Actor,CondtionalDefUseChains),
                'object_id': 'str_id',
                'object_type': the_class,
            }
        """
        # Storing merged propagation slices
        self.source_propagetion_slice = []
        self.destination_propagetion_slice = []

        self.set_paths()

        self.file_data = {}.copy()
        self.populate_file_data()

        # Import language support tools but not saved as an attribute
        # for pickling reasons
        language_support_tools = importlib.import_module(
            f"language_supports.{self.language}"
        )

        self.ConditionalDefUseChains = language_support_tools.ConditionalDefUseChains
        # To reset Actor/Def/Use point ids for each commit
        self.ConditionalDefUseChains.Actor.id_generator = itertools.count(start=1)
        self.ConditionalDefUseChains.Def.id_generator = itertools.count(start=1)
        self.ConditionalDefUseChains.Use.id_generator = itertools.count(start=1)

        # Flag to ensure ConditionalDefUseChains are produced
        self.cdus_extracted = False
        # Flag to ensure PropagationSlice are produced
        self.ps_extracted = False
        # Flag to ensure Diff of PropagationSlice are produced
        self.diff_ps_extracted = False

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

        ## Moved to the end of all commits analysis
        ## in run_* scripts for performance improvement.
        # self.git_repository.checkout(self.branch)
        # time.sleep(10)

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
        if self.analysis_mode != "change_location":
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
            self.file_data[file_path]["has_gumtree_error"] = False
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
        if self.cdus_extracted:
            return
        analysis_method = "analyze_" + self.analysis_mode
        analyzer = getattr(self, analysis_method, self.analyze_global)
        analyzer()
        self.cdus_extracted = True

    def analyze_change_location(self):
        for file_path, file_data in self.file_data.items():
            if file_data["diff"]:
                print(f"{'#'*10} {file_path} {'#'*10}")

                self.source_cdu_chains.append(
                    self.ConditionalDefUseChains(file_data["diff"].source, self)
                )
                print(f"{'#'*10} Analyzing source {'#'*10}")
                self.source_cdu_chains[-1].analyze()

                self.destination_cdu_chains.append(
                    self.ConditionalDefUseChains(file_data["diff"].destination, self)
                )
                print(f"{'#'*10} Analyzing source {'#'*10}")
                self.destination_cdu_chains[-1].analyze()

    def analyze_global(self):
        # Skip if the self.root_file has GumTree error
        try:
            if self.file_data[self.root_file]["diff"] is None:
                print("Selected entry file failed due to parser error.")
                return
        except KeyError:
            print("Selected entry file doeas not exist.")
            return

        self.source_cdu_chains.append(
            self.ConditionalDefUseChains(
                self.file_data[self.root_file]["diff"].source, self
            )
        )
        print(f"{'#'*10} Analyzing source {'#'*10}")
        self.source_cdu_chains[-1].analyze()

        self.destination_cdu_chains.append(
            self.ConditionalDefUseChains(
                self.file_data[self.root_file]["diff"].destination, self
            )
        )
        print(f"{'#'*10} Analyzing destination {'#'*10}")
        self.destination_cdu_chains[-1].analyze()

    def get_file_directory(self, file_path):
        return self.file_data[file_path]["file_dir"]

    def set_data_flow_reach_file(self, file_path, cluster):
        self.file_data[file_path][f"data_flow_{cluster}_reach"] = True

    def append_to_chains(self, cdu_chains):
        chain = getattr(
            self,
            f"{cdu_chains.ast.name}_cdu_chains",
        )
        chain.append(cdu_chains)

    def export_cdu_json(self):
        self.perform_data_flow_analysis()
        save_path = self.commit_dir / "data_flow_output"
        Path(save_path).mkdir(parents=True, exist_ok=True)

        if self.source_cdu_chains:
            src_cdus = list(map(lambda chain: chain.to_json(), self.source_cdu_chains))
            with open(save_path / f"source_cdu_output.json", "w") as f:
                json.dump(src_cdus, f)

        if self.destination_cdu_chains:
            dst_cdus = list(
                map(
                    lambda chain: chain.to_json(),
                    self.destination_cdu_chains,
                )
            )
            with open(save_path / f"destination_cdu_output.json", "w") as f:
                json.dump(dst_cdus, f)

        list(
            map(
                lambda file_data: file_data["diff"].export_json(save_path),
                filter(
                    lambda file_data: (file_data["diff"] is not None),
                    self.file_data.values(),
                ),
            )
        )

    def compute_propagation_slices(self):
        self.perform_data_flow_analysis()

        source_propagetion_slice = [
            chain.get_propagation_slices() for chain in self.source_cdu_chains
        ]
        self.source_propagetion_slice = reduce(
            lambda a, b: [*a, *b], source_propagetion_slice, []
        )
        contaminated_source_nodes = list(
            map(
                lambda point: point.node_data["id"],
                reduce(
                    lambda a, b: [*a, *b],
                    map(
                        lambda chain: chain.get_contaminated_points(),
                        self.source_cdu_chains,
                    ),
                    [],
                ),
            )
        )

        destination_propagetion_slice = [
            chain.get_propagation_slices() for chain in self.destination_cdu_chains
        ]
        self.destination_propagetion_slice = reduce(
            lambda a, b: [*a, *b], destination_propagetion_slice, []
        )
        contaminated_destination_nodes = list(
            map(
                lambda point: point.node_data["id"],
                reduce(
                    lambda a, b: [*a, *b],
                    map(
                        lambda chain: chain.get_contaminated_points(),
                        self.destination_cdu_chains,
                    ),
                    [],
                ),
            )
        )

        matches = reduce(
            lambda a, b: ([*a[0], *b[0]], [*a[1], *b[1]]),
            map(
                lambda file_data: (
                    list(
                        filter(
                            lambda match: match[0] in contaminated_source_nodes,
                            file_data["diff"].source_match.items(),
                        )
                    ),
                    list(
                        filter(
                            lambda match: match[0] in contaminated_destination_nodes,
                            file_data["diff"].destination_match.items(),
                        )
                    ),
                ),
                filter(
                    lambda file_data: not (file_data["diff"] is None),
                    self.file_data.values(),
                ),
            ),
            ([], []),
        )
        self.source_propagetion_slice_matches = dict(matches[0])
        self.destination_propagetion_slice_matches = dict(matches[1])

        self.ps_extracted = True

    def export_csv(self, propagation_slice_mode=True):
        if propagation_slice_mode:
            self.compute_propagation_slices()
            save_path = self.commit_dir / "change_propagation_output"
            Path(save_path).mkdir(parents=True, exist_ok=True)

            source_propagation_rules_df = pd.DataFrame(self.source_propagetion_slice)
            if len(source_propagation_rules_df):
                source_propagation_rules_df.drop(
                    columns=["subject", "object"], inplace=True
                )
            source_propagation_rules_df.to_csv(
                save_path / f"source_propagation_rules.csv", index=False
            )

            destination_propagation_rules_df = pd.DataFrame(
                self.destination_propagetion_slice
            )
            if len(destination_propagation_rules_df):
                destination_propagation_rules_df.drop(
                    columns=["subject", "object"], inplace=True
                )
            destination_propagation_rules_df.to_csv(
                save_path / f"destination_propagation_rules.csv", index=False
            )

        else:
            self.perform_data_flow_analysis()
            save_path = self.commit_dir / "data_flow_output"
            Path(save_path).mkdir(parents=True, exist_ok=True)

        if self.source_cdu_chains:
            src_cdus = list(
                map(
                    lambda chain: chain.to_csv(propagation_slice_mode),
                    self.source_cdu_chains,
                )
            )

            def_points_df = pd.concat(list(map(lambda row: row[0], src_cdus)))
            use_points_df = pd.concat(list(map(lambda row: row[1], src_cdus)))
            actor_points_df = pd.concat(list(map(lambda row: row[2], src_cdus)))
            if propagation_slice_mode:
                undefined_names_df = None
            else:
                undefined_names_df = pd.concat(list(map(lambda row: row[3], src_cdus)))

            def_points_df.to_csv(save_path / f"source_def_points.csv", index=False)
            use_points_df.to_csv(save_path / f"source_use_points.csv", index=False)
            actor_points_df.to_csv(save_path / f"source_actor_points.csv", index=False)
            if undefined_names_df:
                undefined_names_df.to_csv(
                    save_path / f"source_undefined_names.csv", index=False
                )

        if self.destination_cdu_chains:
            dst_cdus = list(
                map(
                    lambda chain: chain.to_csv(propagation_slice_mode),
                    self.destination_cdu_chains,
                )
            )

            def_points_df = pd.concat(list(map(lambda row: row[0], dst_cdus)))
            use_points_df = pd.concat(list(map(lambda row: row[1], dst_cdus)))
            actor_points_df = pd.concat(list(map(lambda row: row[2], dst_cdus)))
            if propagation_slice_mode:
                undefined_names_df = None
            else:
                undefined_names_df = pd.concat(list(map(lambda row: row[3], dst_cdus)))

            def_points_df.to_csv(save_path / f"destination_def_points.csv", index=False)
            use_points_df.to_csv(save_path / f"destination_use_points.csv", index=False)
            actor_points_df.to_csv(
                save_path / f"destination_actor_points.csv", index=False
            )
            if undefined_names_df:
                undefined_names_df.to_csv(
                    save_path / f"destination_undefined_names.csv", index=False
                )

        if propagation_slice_mode:
            source_matches_df = pd.DataFrame(
                list(
                    map(
                        lambda pair: {"source": pair[0], "destination": pair[1]},
                        self.source_propagetion_slice_matches.items(),
                    )
                )
            )
            destination_matches_df = pd.DataFrame(
                list(
                    map(
                        lambda pair: {"source": pair[1], "destination": pair[0]},
                        self.destination_propagetion_slice_matches.items(),
                    )
                )
            )
            matches_df = pd.concat([source_matches_df, destination_matches_df])
            matches_df.drop_duplicates(inplace=True)
            matches_df.to_csv(
                save_path / f"node_matches.csv",
                index=False,
            )
        else:
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
