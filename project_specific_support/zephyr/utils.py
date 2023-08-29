from pathlib import Path
from functools import reduce
from itertools import product
from utils.configurations import REPOSITORY


def get_settings():
    archs = list(
        set(
            map(
                lambda r: str(r).split("/")[-1],
                filter(
                    lambda p: (
                        p.is_dir() and not str(p).endswith(("/.DS_Store", "/common"))
                    ),
                    (Path(REPOSITORY) / "arch").iterdir(),
                ),
            )
        )
    )

    grid = {"arch": archs}
    grid["boards"] = list(
        set(
            reduce(
                lambda a, b: [*a, *b],
                map(
                    lambda arch: list(
                        map(
                            lambda r: f"boards/{arch}/" + str(r).split("/")[-1],
                            filter(
                                lambda p: (
                                    p.is_dir()
                                    and not str(p).endswith(
                                        ("/.DS_Store", "/common", "/shields")
                                    )
                                ),
                                (Path(REPOSITORY) / "boards" / arch).iterdir(),
                            ),
                        )
                    ),
                    archs,
                ),
                [],
            )
        )
    )
    grid["soc_family"] = list(
        set(
            reduce(
                lambda a, b: [*a, *b],
                map(
                    lambda arch: list(
                        map(
                            lambda r: f"soc/{arch}/" + str(r).split("/")[-1],
                            filter(
                                lambda p: (
                                    p.is_dir()
                                    and not str(p).endswith(("/.DS_Store", "/common"))
                                ),
                                (Path(REPOSITORY) / "soc" / arch).iterdir(),
                            ),
                        )
                    ),
                    archs,
                ),
                [],
            )
        )
    )
    grid["soc_series"] = list(
        set(
            reduce(
                lambda a, b: [*a, *b],
                map(
                    lambda soc_family: list(
                        map(
                            lambda r: f"{soc_family}/" + str(r).split("/")[-1],
                            filter(
                                lambda p: (
                                    p.is_dir()
                                    and not str(p).endswith(("/.DS_Store", "/common"))
                                ),
                                (Path(REPOSITORY) / soc_family).iterdir(),
                            ),
                        )
                    ),
                    grid["soc_family"],
                ),
                [],
            )
        )
    )

    return grid
