# forest
The forest project aims at automatizing the clone and build process for open source software.

## Usage (for developers)

1) clone the repo somewhere, cd to the main folder
2) install in editable mode with `pip3 install --user -e .`
3) somewhere else, create a workspace folder such as `mkdir test_forest && cd test_forest`
4) run forest with `forest all`, or `forest matlogger2`, or `forest xbot2_examples`; notice that the argument must match a file inside the `recipes/` folder; TODO: think of a way to expand the set of valid names
5) run `forest --help` for usage information

## Usage (for early adopters)

Do `pip3 install hhcm-forest` instead of steps 1)-3)