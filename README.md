# forest
The forest project aims at automatizing the clone and build process for open source software.

## Usage (for developers)

1) clone the repo somewhere, cd to the main folder
2) install in editable mode with `pip3 install --user -e .`
3) somewhere else, create a workspace folder such as `mkdir test_forest && cd test_forest`
4) initialize the workspace with `forest --init`
5) download recipes from a remote repository (e.g. `forest --add-recipes git@github.com:advrhumanoids/multidof_recipes.git master`, or manually download then into the `recipes` folder)
6) `forest --list` lists available recipes
7) `forest <recipe-name> [-j 8] [--clone-protocol https]`
8) run `forest --help` for usage information

## Usage (for early adopters)

Do `pip3 install hhcm-forest` instead of steps 1)-2)
