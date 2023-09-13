import time
from .def_use_chains import ConditionalDefUseChains as ProjectConditionalDefUseChains
from .utils import get_settings
import system_commit_model as scm


class SystemDiff(scm.SystemDiff):
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
        super().__init__(
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
        )
        self.ConditionalDefUseChains = ProjectConditionalDefUseChains

    def populate_file_data(self):
        self.git_repository.checkout(self.commit.hash)
        time.sleep(5)

        self.set_file_data()
        self.set_file_data_diffs()
        self.configs = get_settings()

        self.git_repository.checkout(self.branch)
        time.sleep(5)


class SystemDiffShortcut(SystemDiff, scm.SystemDiffShortcut):
    def set_file_data_modified_only(self):
        return scm.SystemDiffShortcut.set_file_data_modified_only(self)

    def set_file_data_non_modified_only(self):
        return scm.SystemDiffShortcut.set_file_data_non_modified_only(self)

    def get_file_diff(self, file_path):
        return scm.SystemDiffShortcut.get_file_diff(self, file_path)


class SystemDiffSeries(SystemDiff, scm.SystemDiffSeries):
    def set_paths(self):
        return scm.SystemDiffSeries.set_paths(self)

    def set_file_data_non_modified_only(self):
        return scm.SystemDiffSeries.set_file_data_non_modified_only(self)

    def get_modified_file_diff(self, file_path):
        return scm.SystemDiffSeries.get_modified_file_diff(self, file_path)

    def get_non_modified_file_diff(self, file_path):
        return scm.SystemDiffSeries.get_non_modified_file_diff(self, file_path)

    def write_non_modified_code_files(self, file_path):
        return scm.SystemDiffSeries.write_non_modified_code_files(self, file_path)

    def get_file_diff(self, file_path):
        return scm.SystemDiffSeries.get_file_diff(self, file_path)
