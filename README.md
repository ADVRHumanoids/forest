# forest [![Build Status](https://app.travis-ci.com/ADVRHumanoids/forest.svg?branch=master)](https://app.travis-ci.com/ADVRHumanoids/forest)
The forest project aims at automatizing the clone and build process for open source software. Differently from other systems such as [Conda](https://docs.conda.io/en/latest/), or [Conan](https://conan.io/), it is a non-intrusive system which does not aim at environment management. 

## Quickstart
Setup a new workspace and add new recipes. Optional arguments are surrounded by [square brackets].
 - `[sudo] pip3 install hhcm-forest`
 - `mkdir my_ws && cd my_ws` 
 - `forest init`
 - `source setup.bash`
 - `forest add-recipes git@github.com:advrhumanoids/multidof_recipes.git [--tag master]`

 Install the `xbot2_examples` recipe with its dependencies. 
 - `forest grow xbot2_examples [-j8] [--clone-protocol https]`
 
## Command line interface
Forest's CLI is divided into three main *verbs*, i.e. `init`, `add-recipes`, and `grow`.

### forest init
Initialize the current folder as a forest workspace, i.e. it creates
 - a `src` folder that will contain source code
 - a `recipes` folder that will contain forest's recipe files (more on this later)
 - a `build` folder to carry out compilation and store build artifacts 
 - an `install` folder 
 - a `setup.bash` file which makes installed items visible to the system
 
 ### forest add-recipes
 Adds recipes from a remote.

 ```bash
 usage: forest add-recipes [-h] [--tag TAG] [--verbose] url

positional arguments:
  url                   url of the remote (e.g.
                        git@github.com:<username>/<reponame>.git)

optional arguments:
  -h, --help            show this help message and exit
  --tag TAG, -t TAG
  --verbose, -v         print additional information

```

 ### forest grow
 Builds a project according to the given recipe name, alongside its dependencies.

 ```bash
 usage: forest grow [-h] [--jobs JOBS] [--mode MODE [MODE ...]]
                   [--config CONFIG [CONFIG ...]]
                   [--default-build-type {None,RelWithDebInfo,Release,Debug}]
                   [--force-reconfigure] [--list-eval-locals]
                   [--clone-protocol {ssh,https}] [--clone-depth CLONE_DEPTH]
                   [--cmake-args CMAKE_ARGS [CMAKE_ARGS ...]] [--no-deps]
                   [--uninstall] [--clean] [--pwd PWD] [--verbose]
                   [RECIPE]

positional arguments:
  RECIPE                name of recipe with fetch and build information

optional arguments:
  -h, --help            show this help message and exit
  --jobs JOBS, -j JOBS  parallel jobs for building
  --mode MODE [MODE ...], -m MODE [MODE ...]
                        specify modes that are used to set conditional
                        compilation flags (e.g., cmake args)
  --config CONFIG [CONFIG ...], -c CONFIG [CONFIG ...]
                        specify configuration variables that can be used
                        inside recipes
  --default-build-type {None,RelWithDebInfo,Release,Debug}, -t {None,RelWithDebInfo,Release,Debug}
                        build type for cmake, it is overridden by recipe
  --force-reconfigure   force calling cmake before building with args from the
                        recipe
  --list-eval-locals    print available attributes when using conditional
                        build args
  --clone-protocol {ssh,https}
                        override clone protocol
  --clone-depth CLONE_DEPTH
                        set maximum history depth to save bandwidth
  --cmake-args CMAKE_ARGS [CMAKE_ARGS ...]
                        specify additional cmake args to be appended to each
                        recipe (leading -D must be omitted)
  --no-deps, -n         skip dependency fetch and build step
  --uninstall           uninstall recipe
  --clean               uninstall recipe and remove build
  --pwd PWD, -p PWD     user password to be used when sudo permission is
                        required (if empty, user is prompted for password);
                        note: to be used with care, as exposing your password
                        might be harmful!
  --verbose, -v         print additional information
```
