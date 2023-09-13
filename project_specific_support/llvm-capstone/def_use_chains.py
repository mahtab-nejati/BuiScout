from pathlib import Path
import language_supports.cmake as cmake
from utils.configurations import ROOT_FILE, REPOSITORY
from utils.exceptions import DebugException


class ConditionalDefUseChains(cmake.ConditionalDefUseChains):
    """
    ##################################
    #### project-specific support ####
    ######### llvm-capstone ##########
    ##################################
    """

    def get_manually_resolved_path(self, file_path_node):
        file_path = self.ast.unparse(file_path_node)
        file_path = file_path.replace(" ", "")
        if file_path == "Platform/${CMAKE_HOST_SYSTEM_NAME}":
            current_path = "/".join(self.ast.file_path.split("/")[:-1])
            return True, list(
                set(
                    filter(
                        lambda f: f in self.sysdiff.file_data,
                        map(
                            lambda r: str(r).replace(REPOSITORY + "/", ""),
                            (Path(REPOSITORY) / current_path / "platforms").iterdir(),
                        ),
                    )
                )
            )
        return super().get_manually_resolved_path(file_path_node)
