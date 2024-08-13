# Guide to setup config.json

>Note: `config_test.json` provides and example.

The json object in your config.json file must include the following configurations:

## [`OPTIONS`](#options)
  (`Dictionary(Boolean)`, Required)

  To enable any option, set its value to `true`, and to disable it, set its value to `false`. The options are:

  ### [`RESOURCE_CONTROL`](#resource_control)

  If enabled, assigns each commit to a process thread so that once the commit is processed, all resources are released before moving to the next commit. 
  
  >**Note:** No parallelization is provided, therefore this can be used together with [`COMMIT_SERIES`](#commit_series) (not mutually exclusive). 
  
  >**Note:** This is under test and is not compatible with `arm` architecures. 
  
  >**Hint:** Disable if maximum recursion errors encountered.

  ### [`COMMIT_SERIES`](#commit_series)

  If enabled, the commits listed in [`COMMITS`](#commits) are treated as a series of conscutive build commits and the source code and AST differencing information is cached from each previous commit for the next commit. In this case, only the modified files in the next commit are re-processed. 
  
  If disabled, computes AST differences for all files in each commit independently.
  
  >**Note:** This is mutually exclusive with [`AST_DIFFS_REUSE`](#ast_diffs_reuse) and overwrites this option if both are selected. 

  ### [`AST_DIFFS_REUSE`](#ast_diffs_reuse)

  If enabled, uses the the pre-existing GumTree output. Assumes that there was a GumTree error if data does not exist.

  >**Note:** This can only be used if BuiScout has previously analyzed a commit wihtout [`COMMIT_SERIES`](#commit_series) being enabled and [`STORE`](#store) is the same path for both runs.

  >**Note:** This is incompatible with [`COMMIT_SERIES`](#commit_series) and will be disabled if [`COMMIT_SERIES`](#commit_series) is enabled.

  ### [`PROGRESS_RESET`](#progress_reset)

  If enabled, clears the progress into the list [`COMMITS`](#commits) and re-processes all listed commits.

  ### [`VERBOSE`](#verbose)

  If enabled, the verbose logs will be printed to the terminal.

  ### [`CHANGE_LOCATION_ONLY`](#change_location_only)
  
  If enabled, instead of considering the build system globally, only the modified files get analyzed and the impact detected will be contained to the modified files.

  ### [`SNAPSHOT_MODE`](#snapshot_mode)

  If enabled, no differencing is applied and the build system in the updated version will be analyzed (data-flow and IKG construction, IKG in this mode is currently invalid).

  ### [`EXECUTE_CALLABLES`](#execute_callables)

  If enabled, the body of each user-defined callable entity will be imported to each call site.

  ### [`PROJECT_MODEL`](#project_model)

  If enabled, looks for a folder named [`PROJECT`](#project) in the `project_specific_support` folder where an extension of BuiScout is implemented to support specific features for the subject project.

  ### [`INITIALIZE_WITH_BUILD_COMMITS`](#INITIALIZE_WITH_BUILD_COMMITS)

  >Warning: Not recommended due to errors in underlying libraries.

  If enabled, only commits with build specifications are selected from the repository. This might throw an error as we access parent commits and they might be excluded.

## [`RELATIVE_RESULT_PATH`](#RELATIVE_RESULT_PATH) 
  (`String(Path)`, Required)

  The path to where the results must be stored. Must be inside the docker's mountpoint and relative to the mountpoint.

## [`PROJECT`](#project)
  (`String`, Required)

  The name of the subject project.

## [`REPOSITORY`](#repository) 
  (`String(Path)` or `String(URL)`, Required)

  The local path or url pointing to the subject repository.
  If a local path is provided, it must be inside the docker's mountpoint and relative to the mountpoint.

  >Note: A path to a local clone of the repository is recommended for faster analysis.

## [`BRANCH`](#branch) 
  (`String`, Required)

  The branch to consider the commits from. Use the keyword `ALL` to consider all branches.
  
  >Note: Use of the default branch is recommended.

## [`COMMITS`](#commits) 
  (`List[String(Commit Hash)]` or keyword `ALL`, Required)

  List of commit hashes to analyze. Use the keyword 'ALL' to analyze all commits.

## [`EXCLUDED_COMMITS`](#excluded_commits) 
  (`List[String(Commit Hash)]`, Required)

  List of commit hashes to analyze. Pass an empty list to exclude no commits.

## [`BUILD_TECHNOLOGY`](#build_technology)
  (`String`, Required)

  The build technology supporting the build system, e.g., `CMake` or `Maven`.

## [`ENTRY_FILES`](#entry_files)
  (`List[String(Path)]`, Required)
  
  The list of paths to the build system's entry point. Must be relative the the root directory of the subject project, and at least one path is required.

## [`PROJECT_SPECIFIC_INCLUDES`](#project_specific_includes)
  (`Dictionary(Dictionary(List[String]))`, Required)

  Use the following template and fill the lists as needed. Simply pass an empty dictionary to skip this configuration.

  ```json
  {"include": {
    "starts_with": [
        "List of the begining of the paths (relative to root
        directory in the subject project, no / at the beginning)
        to include (added to the default patterns for naming
        conventions in a given build technology) in the analysis."
      ],
    "ends_with": [
        "List of the ending of the paths (treated similar to a
        file extension) to include (added to the default patterns
        for naming conventions in a given build technology)
        in the analysis."
      ]
    }
  }
  ```

## [`PROJECT_SPECIFIC_EXCLUDES`](#project_specific_excludes)
  (`Dictionary(Dictionary(Dictionary(List[String])))`, Required)

  Use the following template and fill the lists as needed. Simply pass an empty dictionary to skip this configuration.

  ```json
  {<INSERT_LANGUAGE_LOWER_CASE>: {
      "exclude": {
        "starts_with": [
            "List of the begining of the paths (relative to root
            directory in the subject project, no / at the beginning)
            to exclude (even if the qualify based on default
            patterns for naming conventions in a given build
            technology) from the analysis."
          ],
        "ends_with": [
            "List of the ending of the paths (treated similar to a
            file extension) to exclude (even if the qualify
            based on default patterns for naming conventions
            in a given build technology) from the analysis."
          ]
        }
      }
  }
  ```

## [`PROJECT_SPECIFIC_PATH_RESOLUTION`](#project_specific_manual_path_resolution)
  (`List[Dictionary]`, Required)

  Use the following template and populate the list as needed. Simply pass an empty lists to skip this configuration.

  >Note: The specified resolutions overwrite the default file resolution techniques.

  ```json
  [
    {
      "caller_file_path": "Path to the file in which the caller
      command resides. Use '*' to apply the same resolutions for
      everywhere in code.",
      "callee_file_path": "Path specified in the caller command to
      refer to the callee file.",
      "callee_resolved_path": [
        "A list of relative paths to the callee file (relative to the
        root directory of the subject project). List can have >= 1
        path. Use keyword 'SKIP' (without list) to skip."
      ]
    }
  ]
  ```
