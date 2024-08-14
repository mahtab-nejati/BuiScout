# BuiScout

***BuiScout*** is an implementation of ***BCIA***, presented in our paper, ***Understanding the Implications of Changes to Build Systems*** *(ASE'24)*.
*BCIA* is an approach to detect the locations across a `CMake` build system that are affected by a change in the build specifications.

## Setup

*BuiScout* relies on 4 major components that need to be setup and configured with each other.
For ease of use, we have made a docker image of the working environment (at the version used for our *ASE'24* paper) available online.
Please refer to our [replication package](https://zenodo.org/doi/10.5281/zenodo.11505222) to find instrucitons on how to use this image.

If you need to clone this repository for extension and run it locally, you may choose to either [run BuiScout in a docker container (recommended)](#build-docker-image-to-run-in-container-recommended) or [run it in your local environment](#setup-local-environment-to-run-locally).

### [Build Docker Image to Run in Container (Recommended)](#build-docker-image-to-run-in-container-recommended)

>**Note:** If you intend to extend BuiScout and run it in a contaier, you must rebuild the image after you make changes to the code base.

>**Note:** If your changes lead to adding a new directory in the root directory of the project, you must add this directory to the list of the _Allowed files and directories_ in the `.dockerignore` file. To do so, simply add a line containing `!/[Name_of_the_directory]` to the list.

0. Make sure you have [Docker](https://docs.docker.com/engine/install/) installed.

    >**Note:** We used Docker version 27.1.1, build 6312585 in our _ASE`24_ submission version.

1. In your Bash command line, change your working directory to the root directory of the BuiScout project by running:
    ```shell
    # cd [Path_to_BuiScout_Location]/BuiScout
    ```

2. Make sure the files `BuiScout_build_image.sh`, `BuiScout_run_container.sh`, `process.sh`, and `convert.sh` have executable. To make these files executable, in your Bash command line and in the same working directory, run:
    ```shell
    # chmod +x ./*.sh
    ```

3. Run the `BuiScout_build_image.sh` script, located in the root directory of the project by running the following command in your Bash command line and in the same working directory.
    ```shell
    # ./BuiScout_build_image.sh
    ```
    >**Note:**  This script first builds the `buiscout` image and then runs it. Once the script is successfully run, you will be logged into the container.

    >**Note:** This script creates a directory named `_BuiScout_mountpoint` in the parent directory of the BuiScout project.
    You must place your [config.json file](#configuration-guide) in this direcotry and, if you choose to analyze a local subject repository, clone it into this directory.

    >**Note:** Runing this script from any working directory works fine, as long as you point to the script file. For example, if your peresent working is the parent directory of the BuiScout project, running the following will yield the same outcome:
    ```shell
    # ./BuiScout/BuiScout_build_image.sh
    ```

4. For future executions, rebuilding the image is not necessary unless changes are made to BuiScout. To run the docker container without rebuilding the image, run the `BuiScout_run_container.sh`, located in the root directory of the project by running the following command in your Bash command line and in the same working directory.
    ```shell
    # ./BuiScout_run_container.sh
    ```
    
    >**Note:** Once the script is successfully run, you will be logged into the container.
    
    >**Note:** Runing this script from any working directory works fine, as long as you point to the script file. For example, if your peresent working is the parent directory of the BuiScout project, running the following will yield the same outcome:
    ```shell
    # ./BuiScout/BuiScout_run_container.sh
    ```


### [Setup Local Environment to Run Locally](#setup-local-environment-to-run-locally)





# Installation

0. Make sure you have [Bash](<https://en.wikipedia.org/wiki/Bash_(Unix_shell)>) installed on your system.

1. Extract the files in the compressed file "Code Review of Build System Specifications.zip" and put them inside a folder in your machine.

2. Install [Docker](https://docs.docker.com/engine/install/). Note that we are using version 20.10.22, build 3a2c30b.

3. In your Bash command line, cd into the 

**0. Dockerized Quantitative Analysis** directory.

4. In your Bash command line and under the same directory when connected to the internet, run the following command to pull the [Docker image](https://hub.docker.com/repository/docker/mattienejati/cr4bss-pppp/general) from [DockerHub](https://hub.docker.com/) into your system.

   ```
   > docker pull mattienejati/cr4bss-pppp:latest
   ```

   > **_NOTE:_** The image is built for **arm64** and **amd64** architectures.

5. In your Bash command line, run the following command to verify that you have successfully loaded the cr4bss-pppp docker.
   The docker name must be listed in the output.

   ```
   > docker images
   ```

6. Your environment is ready to run the analyses.

## Evaluation of the artifacts

2. Install [Docker](https://docs.docker.com/engine/install/). Note that we are using version 20.10.22, build 3a2c30b.

3. In your Bash command line, cd into the **0. Dockerized Quantitative Analysis** directory.

4. In your Bash command line and under the same directory when connected to the internet, run the following command to pull the [Docker image](https://hub.docker.com/repository/docker/mattienejati/cr4bss-pppp/general) from [DockerHub](https://hub.docker.com/) into your system.

   ```
   > docker pull mattienejati/cr4bss-pppp:latest
   ```

   > **_NOTE:_** The image is built for **arm64** and **amd64** architectures.

5. In your Bash command line, run the following command to verify that you have successfully loaded the cr4bss-pppp docker.
   The docker name must be listed in the output.

   ```
   > docker images
   ```

6. Your environment is ready to run the analyses.

## Replication of the study in subsequent research

> **_NOTE:_** This is not required for artifact evaluation. It is provided to facilitate future reuse and repurposing of the replication package and is equivalent to running the same analysis in the evaluation of the artifacts in users' customized environments.

> **_NOTE:_** You may choose to open the _.ipynb_ notebooks using your preferred IDE that supports _.ipynb_ files.

2. Install [Python3](https://www.python.org/downloads/). Note that we are using version 3.8.10.

3. Install [JupyterLab](https://jupyter.org/). Note that we are using the version 3.3.3.

4. In your Bash command line, cd to the root directory of the extracted replication package and run the following command:

   ```
   > jupyter lab
   ```

5. In your browser, connect to the jupyter local server (the default will be [http://localhost:8888/](http://localhost:8888/)) and navigate the directory structure to find your desired notebook and open it.

6. To run the R scripts, install [R](https://www.r-project.org/). Note that we are using version 4.2.1.

7. To verify that you have successfully install R, run the following command in your command line:

   ```
   > R --version
   ```


## [Configuration Guide](#configuration-guide)

This section is a manual to setup your config.json file.

>Note: `config_test.json` provides and example.

The json object in your config.json file must include the following configurations:

### [`OPTIONS`](#options)
  (`Dictionary(Boolean)`, Required)

  To enable any option, set its value to `true`, and to disable it, set its value to `false`. The options are:

  #### [O1: `RESOURCE_CONTROL`](#resource_control)

  If enabled, assigns each commit to a process thread so that once the commit is processed, all resources are released before moving to the next commit. 
  
  >**Note:** No parallelization is provided, therefore this can be used together with [`COMMIT_SERIES`](#commit_series) (not mutually exclusive). 
  
  >**Note:** This is under test and is not compatible with `arm` architecures. 
  
  >**Hint:** Disable if maximum recursion errors encountered.

  #### [O2: `COMMIT_SERIES`](#commit_series)

  If enabled, the commits listed in [`COMMITS`](#commits) are treated as a series of conscutive build commits and the source code and AST differencing information is cached from each previous commit for the next commit. In this case, only the modified files in the next commit are re-processed. 
  
  If disabled, computes AST differences for all files in each commit independently.
  
  >**Note:** This is mutually exclusive with [`AST_DIFFS_REUSE`](#ast_diffs_reuse) and overwrites this option if both are selected. 

  #### [Opt3: `AST_DIFFS_REUSE`](#ast_diffs_reuse)

  If enabled, uses the the pre-existing GumTree output. Assumes that there was a GumTree error if data does not exist.

  >**Note:** This can only be used if BuiScout has previously analyzed a commit wihtout [`COMMIT_SERIES`](#commit_series) being enabled and [`STORE`](#store) is the same path for both runs.

  >**Note:** This is incompatible with [`COMMIT_SERIES`](#commit_series) and will be disabled if [`COMMIT_SERIES`](#commit_series) is enabled.

  #### [Opt4: `PROGRESS_RESET`](#progress_reset)

  If enabled, clears the progress into the list [`COMMITS`](#commits) and re-processes all listed commits.

  #### [Opt5: `VERBOSE`](#verbose)

  If enabled, the verbose logs will be printed to the terminal.

  #### [Opt6: `CHANGE_LOCATION_ONLY`](#change_location_only)
  
  If enabled, instead of considering the build system globally, only the modified files get analyzed and the impact detected will be contained to the modified files.

  #### [Opt7: `SNAPSHOT_MODE`](#snapshot_mode)

  If enabled, no differencing is applied and the build system in the updated version will be analyzed (data-flow and IKG construction, IKG in this mode is currently invalid).

  #### [Opt8: `EXECUTE_CALLABLES`](#execute_callables)

  If enabled, the body of each user-defined callable entity will be imported to each call site.

  #### [Opt9: `PROJECT_MODEL`](#project_model)

  If enabled, looks for a folder named [`PROJECT`](#project) in the `project_specific_support` folder where an extension of BuiScout is implemented to support specific features for the subject project.

  #### [Opt10: `INITIALIZE_WITH_BUILD_COMMITS`](#INITIALIZE_WITH_BUILD_COMMITS)

  >Warning: Not recommended due to errors in underlying libraries.

  If enabled, only commits with build specifications are selected from the repository. This might throw an error as we access parent commits and they might be excluded.

### [`RELATIVE_RESULT_PATH`](#RELATIVE_RESULT_PATH) 
  (`String(Path)`, Required)

  The path to where the results must be stored. Must be inside the docker's mountpoint and relative to the mountpoint.

### [`PROJECT`](#project)
  (`String`, Required)

  The name of the subject project.

### [`REPOSITORY`](#repository) 
  (`String(Path)` or `String(URL)`, Required)

  The local path or url pointing to the subject repository.
  If a local path is provided, it must be inside the docker's mountpoint and relative to the mountpoint.

  >Note: A path to a local clone of the repository is recommended for faster analysis.

### [`BRANCH`](#branch) 
  (`String`, Required)

  The branch to consider the commits from. Use the keyword `ALL` to consider all branches.
  
  >Note: Use of the default branch is recommended.

### [`COMMITS`](#commits) 
  (`List[String(Commit Hash)]` or keyword `ALL`, Required)

  List of commit hashes to analyze. Use the keyword 'ALL' to analyze all commits.

### [`EXCLUDED_COMMITS`](#excluded_commits) 
  (`List[String(Commit Hash)]`, Required)

  List of commit hashes to analyze. Pass an empty list to exclude no commits.

### [`BUILD_TECHNOLOGY`](#build_technology)
  (`String`, Required)

  The build technology supporting the build system, e.g., `CMake` or `Maven`.

### [`ENTRY_FILES`](#entry_files)
  (`List[String(Path)]`, Required)
  
  The list of paths to the build system's entry point. Must be relative the the root directory of the subject project, and at least one path is required.

### [`PROJECT_SPECIFIC_INCLUDES`](#project_specific_includes)
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

### [`PROJECT_SPECIFIC_EXCLUDES`](#project_specific_excludes)
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

### [`PROJECT_SPECIFIC_PATH_RESOLUTION`](#project_specific_manual_path_resolution)
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
