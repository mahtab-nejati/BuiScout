# BuiScout

***BuiScout*** is an implementation of ***BCIA***, presented in our paper, ***Understanding the Implications of Changes to Build Systems*** *(ASE'24)*.
*BCIA* is an approach to detect the locations across a `CMake` build system that are affected by a change in the build specifications.

## [README Content](#content)

- [Setup](#setup)

  - [Build Docker Image to Run in Container (Recommended)](#build-docker-image-to-run-in-container-recommended)

    - [Preparations](#docker-setup-prep)
    - [Building the Image and Running the Container](#docker-build-run)
  
  - [Setup Local Environment to Run Locally](#setup-local-environment-to-run-locally)

    - [Preparations](#local-setup-prep)
    - [Seting up Local Environment for BuiScout](#local-setup-prep)

- [Usage](#usage)

  - [Supported Options](#supported-options)
  - [Prepare config.json](#prepare-configjson)

## [Setup](#setup)

*BuiScout* relies on 3 components that need to be setup and configured with each other.
For ease of use, we have made a docker image of the working environment (at the version used for our *ASE'24* paper) available online.
Please refer to our [replication package](https://zenodo.org/doi/10.5281/zenodo.11505222) to find instrucitons on how to use this image.

If you need to clone this repository for extension and run it locally, you may choose to either [run BuiScout in a docker container (recommended)](#build-docker-image-to-run-in-container-recommended) or [run it in your local environment](#setup-local-environment-to-run-locally).

### [Build Docker Image to Run in Container (Recommended)](#build-docker-image-to-run-in-container-recommended)

>**Note:** If you intend to extend BuiScout and run it in a contaier, you must rebuild the image after you make changes to the code base.

>**Note:** If your changes lead to adding a new directory in the root directory of the project, you must add this directory to the list of the _Allowed files and directories_ in the `.dockerignore` file. To do so, simply add a line containing `!/[Name_of_the_directory]` to the list.

#### [Preparations](#docker-setup-prep)

Because this project relies on other repositories, you must take the following steps before you start setting up BuiScout:

  1. Create a directory which will be the top-level directory of the setup. You can run the following command in your Bash command line at your prefered working directory to create this directory with the name `BCIA`:
      ```shell
      $ mkdir BCIA/
      ```

  2. Download the `gumtree-ASE2024.zip` file from [this version of this repository](https://github.com/mahtab-nejati/gumtree/releases/tag/ASE2024) and unzip it into the `BCIA` folder.
      
      >**Note:** Do **_NOT_** use the upstream repository. The changes made in this version, although minor, are essential for BuiScout's successful execution.

      >**Note:** Alternatively, you can clone [the latest version of this repository](https://github.com/mahtab-nejati/gumtree) in the `BCIA` directory to use the latest versoin. But note that you will have to [build this project from source code](https://github.com/GumTreeDiff/gumtree/wiki/Getting-Started#install-from-the-sources) and unzip the built project in the same directory as the zip file.

  3. Download the `tree-sitter-parser-ASE2024.zip` file from [this version of this repository](https://github.com/mahtab-nejati/tree-sitter-parser/releases/tag/ASE2024) and unzip it into the `BCIA` folder.
      
      >**Note:** Do **_NOT_** use the upstream repository. This version uses an improved and more robust CMake Tree-Sitter parser.

      >**Note:** Alternatively, you can clone [the latest version of this repository](https://github.com/mahtab-nejati/tree-sitter-parser) in the `BCIA` directory to use the latest versoin. But note that you will have to clone this recursively and then [setup the `tree-sitter-cmake` submodule](https://github.com/mahtab-nejati/tree-sitter-cmake/tree/a637364077c9555b74b058042aa2f1ba2cff576b) accordingly.

#### [Building the Image and Running the Container](#docker-build-run)

  0. Make sure you have [Docker](https://docs.docker.com/engine/install/) installed and running.

      >**Note:** We used Docker version 27.1.1, build 6312585 in our _ASE`24_ submission version.

  1. In your Bash command line, change your working directory to the root directory of the BuiScout project by running:
      ```shell
      $ cd [Path_to_BuiScout_Location]/BuiScout
      ```

  2. Make sure the files `BuiScout_build_image.sh`, `BuiScout_run_container.sh`, `process.sh`, and `convert.sh` are executable. To make these files executable, in your Bash command line and in the same working directory, run:
      ```shell
      $ chmod +x ./*.sh
      ```

  3. Run the `BuiScout_build_image.sh` script, located in the root directory of the project by running the following command in your Bash command line and in the same working directory.
      ```shell
      $ ./BuiScout_build_image.sh [tag]
      ```

      >**Note:** You can pass an optional argument to this script to select a specific **tag** for the docker image to be build. If tag is passed, the image `buiscout:tag` is built. By default, it uses the `latest` tag.

      >**Note:**  This script first builds the `buiscout` image and then runs it. Once the script is successfully run, you will be logged into the container.

      >**Note:** This script creates a directory named `_BuiScout_mountpoint` in the parent directory of the BuiScout project, if it does not already exist.
      You must place your [config.json file](#configuration-guide) in this direcotry and, if you choose to analyze a local subject repository, clone it into this directory.

      >**Note:** Runing this script from any working directory works fine, as long as you point to the script file. For example, if your peresent working is the parent directory of the BuiScout project, running the following will yield the same outcome:
      ```shell
      $ ./BuiScout/BuiScout_build_image.sh
      ```

  4. For future executions, rebuilding the image is not necessary unless changes are made to BuiScout. To run the docker container without rebuilding the image, run the `BuiScout_run_container.sh`, located in the root directory of the project by running the following command in your Bash command line and in the same working directory.
      ```shell
      $ ./BuiScout_run_container.sh [tag]
      ```

      >**Note:** You can pass an optional argument to this script to select a specific **tag** for the docker image to be rin. If tag is passed, the image `buiscout:tag` is run. By default, it uses the `latest` tag.
      
      >**Note:** Once the script is successfully run, you will be logged into the container.

      >**Note:** This script creates a directory named `_BuiScout_mountpoint` in the parent directory of the BuiScout project, if it does not already exist.
      You must place your [config.json file](#configuration-guide) in this direcotry and, if you choose to analyze a local subject repository, clone it into this directory.
      
      >**Note:** Runing this script from any working directory works fine, as long as you point to the script file. For example, if your peresent working is the parent directory of the BuiScout project, running the following will yield the same outcome:
      ```shell
      $ ./BuiScout/BuiScout_run_container.sh
      ```

  >**Note:** When using the scripts `BuiScout_build_image.sh` and `BuiScout_run_container.sh`, you can keep your `config.json` file in the root directory of the BuiScout project for ease of modifications.
  The scripts first attemt to copy a `config.json` file from this directory into `../_BuiScout_mountpoint/` directory, which will be mounted as a volume to the container.
  The scripts will print appropriate messages to remind you of this point.


### [Setup Local Environment to Run Locally](#setup-local-environment-to-run-locally)

>**Note:** This options is not recommended. You must setup your local environment for all underlying projects.

#### [Preparations](#local-setup-prep)

> **Note:** The commands on this page were tested on `Ubuntu 22.04`. You will need to follow different instructions on different operating systems/architectures.

  0. Make sure you have [`python3`](https://www.python.org/downloads/) and [`pip`](https://pip.pypa.io/en/stable/installation/) installed.
  It is recommended to create a python environment for the project.
  
  1. Run the following commands to install `openjdk-11-jre` and `graphviz`.

      - System updates:
        ```shell
        $ apt update -y
        $ apt upgrade -y
        ```

      - Installations:
        ```shell
        $ apt install -y openjdk-11-jre graphviz graphviz-dev
        ```

  2. Download the `gumtree-ASE2024.zip` file from [this version of this repository](https://github.com/mahtab-nejati/gumtree/releases/tag/ASE2024) and follow the instructions on the page to install gumtree.
      
      >**Note:** Do **_NOT_** use the upstream repository. The changes made in this version, although minor, are essential for BuiScout's successful execution.

      >**Note:** Alternatively, you can clone [the latest version of this repository](https://github.com/mahtab-nejati/gumtree) to use the latest versoin. But note that you will have to [build this project from source code](https://github.com/GumTreeDiff/gumtree/wiki/Getting-Started#install-from-the-sources), unzip the built project, and add the `/bin` directory in the unzipped directory to your path.

      >**Note:** The location of GumTree on your system does not matter for a local run.

  3. Run the following commands to install `Node.js` and `NPM`.

      - Preparing your system:
          ```shell
          $ apt install -y curl
          $ curl -fsSL https://deb.nodesource.com/setup_16.x
          ```
      - Intallation:
          ```shell
          $ apt install -y nodejs
          $ apt install -y npm
            ```

  4. Download the `tree-sitter-parser-ASE2024.zip` file from [this version of this repository](https://github.com/mahtab-nejati/tree-sitter-parser/releases/tag/ASE2024) and follow the instructions on the page to install prepare the parser.
      
      >**Note:** Do **_NOT_** use the upstream repository. This version uses an improved and more robust CMake Tree-Sitter parser.

      >**Note:** Alternatively, you can clone [the latest version of this repository](https://github.com/mahtab-nejati/tree-sitter-parser) in the `BCIA` directory to use the latest versoin. But note that you will have to clone this **_recursively_** and then install this tool **_AND_** [the `tree-sitter-cmake` submodule](https://github.com/mahtab-nejati/tree-sitter-cmake/tree/a637364077c9555b74b058042aa2f1ba2cff576b) accordingly.


#### [Seting up Local Environment for BuiScout](#local-setup-install)

  1. Download [this version of BuiScout](https://github.com/mahtab-nejati/BuiScout/releases/tag/ASE2024) or [clone its latest version](https://github.com/mahtab-nejati/BuiScout).

  2. In your Bash command line at the root directory of BuiScout, run the following command:
      ```shell
      $ pip install -r requirements.txt
      ````
  
  3. Make sure the files `process.sh`, and `convert.sh` are executable. To make these files executable, in your Bash command line and in the same working directory, run:
      ```shell
      $ chmod +x ./*.sh
      ```

  4. [Optional] Run the following command to create a persistent alias for BuiScout:
      ```shell
      $ echo 'alias scout="python3 <absolute path to the directory BuiScout is cloned into>/BuiScout/scout.py"' >> $HOME/.bashrc
      $ source $HOME/.bashrc
      ````

      >**Note:** By running this command, you will be to run BuiScout from any working directory by simply running the command `scout` in your terminal. If you choose to skip this step, you can run BuiScout by running the following command in your terminal instead of `scout`:
      ```shell
      $ python3 <absolute or relative path to the directory BuiScout is cloned into>/BuiScout/scout.py
      ````

## [Usage](#usage)

>**Note:** If you skipped [_Setup > Setup Local Environment to Run Locally > Setin Up Local Environment for BuiScout > step 4._ ](#local-setup-install), you must replace `scout` command with `python3 <path to BuiScout/scout.py>.

Once you have the you complete the [setup](#setup) of your choice, you will be in a command line where you can access BuiScout using the `scout` command.
Running `sout how-to` will print out detailed instructions on initializing, testing, and running BuiScout.

### [Supported Options](#supported-options)

The `scout` command supports the following options:

- `scout --help`: Prints supported options.

- `scout how-to`: Prints instructions to successfully run/test BuiScout.

- `scout init`: Initializes the environment by creating the `<BuiScout_ROOT_DIR_PARENT>/_BuiScout_mountpoint/` directory.

- `scout test`: Runs BuiScout on the configurations in the `<BuiScout_ROOT_DIR/test/>` directory.

- `scout run`: Runs BuiScout on the [configurations](#prepare-configjson) and repositories available to it in the `<BuiScout_ROOT_DIR_PARENT/_BuiScout_mountpoint>` directory. This will be the volume you mount on the container if you are running BuiScout in a Docker container.


### [Prepare config.json](#prepare-configjson)

This section is a manual to setup your config.json file.

>Note: `<BuiScout_ROOT_DIR>/test/config.json` provides and example.

The json object in your config.json file must include the following configurations:

- [`OPTIONS`](#options)
  (`Dictionary(Boolean)`, Required)

  To enable any option, set its value to `true`, and to disable it, set its value to `false`. The options are:

  - [O1: `RESOURCE_CONTROL`](#resource_control)

    If enabled, assigns each commit to a process thread so that once the commit is processed, all resources are released before moving to the next commit. 
    
    >**Note:** No parallelization is provided, therefore this can be used together with [`COMMIT_SERIES`](#commit_series) (not mutually exclusive). 
    
    >**Note:** This is under test and is not compatible with `arm` architecures. 
  
    >**Hint:** Disable if maximum recursion errors encountered.

  - [O2: `COMMIT_SERIES`](#commit_series)

    If enabled, the commits listed in [`COMMITS`](#commits) are treated as a series of conscutive build commits and the source code and AST differencing information is cached from each previous commit for the next commit. In this case, only the modified files in the next commit are re-processed. 
    
    If disabled, computes AST differences for all files in each commit independently.
    
    >**Note:** This is mutually exclusive with [`AST_DIFFS_REUSE`](#ast_diffs_reuse) and overwrites this option if both are selected. 

  - [Opt3: `AST_DIFFS_REUSE`](#ast_diffs_reuse)

    If enabled, uses the the pre-existing GumTree output. Assumes that there was a GumTree error if data does not exist.

    >**Note:** This can only be used if BuiScout has previously analyzed a commit wihtout [`COMMIT_SERIES`](#commit_series) being enabled and [`STORE`](#store) is the same path for both runs.

    >**Note:** This is incompatible with [`COMMIT_SERIES`](#commit_series) and will be disabled if [`COMMIT_SERIES`](#commit_series) is enabled.

  - [Opt4: `PROGRESS_RESET`](#progress_reset)

    If enabled, clears the progress into the list [`COMMITS`](#commits) and re-processes all listed commits.

  - [Opt5: `VERBOSE`](#verbose)

    If enabled, the verbose logs will be printed to the terminal.

  - [Opt6: `CHANGE_LOCATION_ONLY`](#change_location_only)
  
    If enabled, instead of considering the build system globally, only the modified files get analyzed and the impact detected will be contained to the modified files.

  - [Opt7: `SNAPSHOT_MODE`](#snapshot_mode)

    If enabled, no differencing is applied and the build system in the updated version will be analyzed (data-flow and IKG construction, IKG in this mode is currently invalid).

  - [Opt8: `EXECUTE_CALLABLES`](#execute_callables)

    If enabled, the body of each user-defined callable entity will be imported to each call site.

  - [Opt9: `PROJECT_MODEL`](#project_model)

    If enabled, looks for a folder named [`PROJECT`](#project) in the `project_specific_support` folder where an extension of BuiScout is implemented to support specific features for the subject project.

  - [Opt10: `INITIALIZE_WITH_BUILD_COMMITS`](#INITIALIZE_WITH_BUILD_COMMITS)

    >Warning: Not recommended due to errors in underlying libraries.

    If enabled, only commits with build specifications are selected from the repository. 
    This might throw an error as we access parent commits and they might be excluded.

- [`RELATIVE_RESULT_PATH`](#RELATIVE_RESULT_PATH) 
  (`String(Path)`, Required)

  The path to where the results must be stored. Must be inside the docker's mountpoint and relative to the mountpoint.

- [`PROJECT`](#project)
  (`String`, Required)

  The name of the subject project.

- [`REPOSITORY`](#repository) 
  (`String(Path)` or `String(URL)`, Required)

  The local path or url pointing to the subject repository.
  If a local path is provided, it must be inside the docker's mountpoint and relative to the mountpoint.

  >Note: A path to a local clone of the repository is recommended for faster analysis.

- [`BRANCH`](#branch) 
  (`String`, Required)

  The branch to consider the commits from. Use the keyword `ALL` to consider all branches.
  
  >Note: Use of the default branch is recommended.

- [`COMMITS`](#commits) 
  (`List[String(Commit Hash)]` or keyword `ALL`, Required)

  List of commit hashes to analyze. Use the keyword 'ALL' to analyze all commits.

- [`EXCLUDED_COMMITS`](#excluded_commits) 
  (`List[String(Commit Hash)]`, Required)

  List of commit hashes to analyze. Pass an empty list to exclude no commits.

- [`BUILD_TECHNOLOGY`](#build_technology)
  (`String`, Required)

  The build technology supporting the build system, e.g., `CMake` or `Maven`.

- [`ENTRY_FILES`](#entry_files)
  (`List[String(Path)]`, Required)
  
  The list of paths to the build system's entry point. Must be relative the the root directory of the subject project, and at least one path is required.

- [`PROJECT_SPECIFIC_INCLUDES`](#project_specific_includes)
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

- [`PROJECT_SPECIFIC_EXCLUDES`](#project_specific_excludes)
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

- [`PROJECT_SPECIFIC_PATH_RESOLUTION`](#project_specific_manual_path_resolution)
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