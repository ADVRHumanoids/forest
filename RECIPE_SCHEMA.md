# Forest Recipe YAML Schema

A **forest recipe** is a YAML file whose name (without extension) is the package name. It tells forest how to fetch, build, and wire up the dependencies of a single package.

---

## Top-level structure

```yaml
clone:       # (optional) how to fetch the sources
  ...

build:       # (optional) how to build the package
  ...

depends:     # (optional) list of recipe-level dependencies
  - pkg_a
  - pkg_b

depends_if:  # (optional) conditional dependencies
  <condition>:
    - pkg_c

system_depends:   # (optional) OS packages (apt/dnf/brew/…)
  - libboost-dev

pip_depends:      # (optional) Python packages installed via pip
  - numpy

pre_build:         # (optional) commands run before build
  - cmake --version

pre_build_if:      # (optional) conditional pre-build commands
  <condition>:
    - rm -rf *.deb

post_build:        # (optional) commands run after build
  - echo done

post_build_if:     # (optional) conditional post-build commands
  <condition>:
    - make package
    - cp *.deb {config.binary_dir}
```

A recipe without `clone` and `build` sections acts as a **meta-package** (pure dependency aggregator).

---

## `clone` section

Specifies how to fetch the package source code. The `type` field selects the fetcher.

### `type: git`

Clones a git repository.

```yaml
clone:
  type: git
  server: github.com           # git server hostname
  repository: user/repo.git    # path on the server
  tag: main                    # branch, tag, or commit SHA
  tag_if:                      # conditional tag override (see Conditions)
    stable: v1.2.0
  proto: ssh                   # ssh (default) or https
  recursive: false             # clone submodules (default: false)
  ros_src: true                # create symlink under ros_src/ (bool or condition)
```

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `server` | string | yes | — | e.g. `github.com` |
| `repository` | string | yes | — | e.g. `myorg/myrepo.git` |
| `tag` | string | yes | — | branch/tag/SHA to check out |
| `tag_if` | dict | no | — | condition → tag; first matching condition wins |
| `proto` | string | no | `ssh` | `ssh` or `https`; overridden by `HHCM_FOREST_CLONE_DEFAULT_PROTO` env var or `--clone-protocol` CLI flag |
| `recursive` | bool | no | `false` | init and update git submodules |
| `ros_src` | bool/condition | no | — | symlink source into `ros_src/<pkgname>` for colcon/catkin builds |

### `type: deb`

Installs a Debian/Ubuntu package via `apt`.

```yaml
clone:
  type: deb
  debname: libboost-dev        # supports {ENV_VAR} expansion
```

`debname` supports `{VAR}` substitution from environment variables, e.g.
`ros-{ROS_DISTRO}-moveit-core`.

### `type: custom`

Runs arbitrary shell commands to create the source directory.

```yaml
clone:
  type: custom
  cmd:
    - wget -O {srcdir}/archive.zip https://example.com/archive.zip
    - unzip {srcdir}/archive.zip -d {srcdir}
```

Available substitutions in `cmd`: `{srcdir}`.

---

## `build` section

Specifies how to build the fetched sources. The `type` field selects the builder.

### `type: cmake`

Configures and builds using CMake.

```yaml
build:
  type: cmake
  args:                          # unconditional CMake flags
    - -DBUILD_TESTING=OFF
    - -DPYTHON_PREFIX={installdir}/lib/python3/dist-packages
  args_if:                       # conditional CMake flags (see Conditions)
    xeno:
      - -DXBOT2_ENABLE_XENO=ON
    test:
      - -DBUILD_TESTING=ON
  cmakelists: .                  # path to CMakeLists.txt dir, relative to srcdir
  target: install                # CMake target to build (default: install)
  skip_if: "False"               # condition; if true, skip this build entirely
  env_hooks:                     # lines appended to environment setup script
    - export MY_VAR=1
```

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `args` | list | no | `[]` | CMake `-D` flags; supports string interpolation |
| `args_if` | dict | no | `{}` | condition → list of flags; all matching conditions are merged |
| `cmakelists` | string or list | no | `.` | Path to `CMakeLists.txt` directory. Use a list of `{name: subdir}` entries for multi-project builds |
| `target` | string | no | `install` | CMake build target |
| `skip_if` | condition | no | `False` | Skip build when condition is truthy |
| `env_hooks` | list | no | `[]` | Shell lines written to `share/forest_env_hook/<pkgname>.bash` |

**Multi-project `cmakelists`** (list form):
```yaml
build:
  type: cmake
  cmakelists:
    - my_lib: lib_subdir
    - my_tools: tools_subdir
```
Each entry is a `{build_name: source_subdir}` mapping. Each sub-project is configured and built independently.

### `type: custom`

Runs arbitrary shell commands for the build step.

```yaml
build:
  type: custom
  cmd:
    - python -m pip install -e {srcdir}
    - touch {installdir}/share/custom_build/done.txt
  env_hooks:
    - eval "$(register-python-argcomplete mytool)"
```

Available substitutions in `cmd`: `{srcdir}`, `{installdir}`, `{builddir}`, `{jobs}`.

---

## Dependencies

### `depends`

A flat list of other recipe names that must be fetched and built before this package.

```yaml
depends:
  - pinocchio
  - osqp
  - pybind11
```

### `depends_if`

Conditional dependencies, added only when the given condition is satisfied.

```yaml
depends_if:
  xeno:
    - Xenomai
  xacro_gen:
    - capsule_generation
```

### `system_depends`

System packages installed by the native package manager (apt, dnf, brew, conda, pacman — auto-detected or set via `--pkg-manager`).

```yaml
system_depends:
  - libboost-all-dev
  - python3-numpy
```

### `pip_depends`

Python packages installed via `pip`.

```yaml
pip_depends:
  - meme
  - scipy
```

---

## Pre/post build hooks

Commands run in the **build directory** before or after the main build step. String interpolation is available: `{builddir}`, `{srcdir}`, `{installdir}`.

```yaml
pre_build:
  - rm -rf stale_artifacts/

pre_build_if:
  binary_gen:
    - rm -rf *.deb

post_build:
  - echo "build finished"

post_build_if:
  binary_gen:
    - make package
    - cp *.deb {config.binary_dir}
```

---

## Conditions and expression evaluation

Conditions appear as keys in `*_if` dictionaries (`args_if`, `depends_if`, `tag_if`, `pre_build_if`, `post_build_if`, `ros_src`). A condition can be:

### Mode names

A bare string that matches a mode activated with `forest grow -m <mode>`.

```yaml
args_if:
  xeno:          # active when: forest grow -m xeno ...
    - -DUSE_XENO=ON
  test:          # active when: forest grow -m test ...
    - -DBUILD_TESTING=ON
```

### Python expressions

Any Python expression evaluated against built-in locals:

| Local | Type | Description |
|-------|------|-------------|
| `ubuntu_release` | float | Ubuntu release number, e.g. `20.04`, `22.04` |
| `mode(name)` | function | Returns `True` if `name` is an active mode |
| `shell(cmd)` | function | Runs `cmd` in a shell, returns stdout |
| `env(key)` | function | Returns the value of environment variable `key` |
| `config` | object | Configuration variables set with `--config key:=value` |

```yaml
args_if:
  "ubuntu_release >= 22.0":
    - -DUSE_FEATURE_X=ON
  "env('ROS_DISTRO') == 'humble'":
    - -DROS2_BUILD=ON
  "shell('pkg-config --exists libfoo && echo yes') == 'yes'":
    - -DWITH_LIBFOO=ON
```

### Inline expressions in string values

Strings of the form `${<python_expr>}` are evaluated and replaced:

```yaml
build:
  type: cmake
  args:
    - -DPYTHON_EXECUTABLE=${shell('which python3')}
```

Regular strings (not `${…}`) are first echoed through the shell (expanding env vars, globs, etc.) then formatted with Python `str.format()`:

```yaml
build:
  type: cmake
  args:
    - -DINSTALL_PYTHON_PATH={installdir}/lib/python3/dist-packages
```

---

## Configuration variables

Configuration variables are passed on the command line with `--config` (or `-c`):

```bash
forest grow my_package -c binary_dir:=/tmp/debs
```

Inside a recipe, they are accessible as `config.<name>`:

```yaml
post_build_if:
  binary_gen:
    - cp *.deb {config.binary_dir}
```

---

## Tag overrides

The `--tag-override FILE` CLI flag accepts a YAML file mapping package names to git refs. This overrides `tag` / `tag_if` in every affected recipe:

```yaml
# forest.lock (generated by `forest freeze`)
my_package: 4a7f3c1d2e8b0a9f6c5d3e2b1a0f9e8d7c6b5a4f
other_package: 1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c
```

```bash
forest grow my_package --tag-override forest.lock
```

---

## Complete examples

### Minimal – system package

```yaml
clone:
  type: deb
  debname: gfortran
```

### Git clone only (no build)

```yaml
clone:
  type: git
  server: github.com
  repository: advrhumanoids/kyon_config.git
  tag: master
```

### CMake package with conditional flags

```yaml
clone:
  type: git
  server: github.com
  repository: advrhumanoids/cartesianinterface.git
  tag: ros2
  tag_if:
    stable: ros2-stable

build:
  type: cmake
  args:
    - -DCARTESIO_COMPILE_EXAMPLES=TRUE
  args_if:
    test:
      - -DCARTESIO_BUILD_TESTS=ON

pre_build_if:
  binary_gen:
    - rm -rf *.deb

post_build_if:
  binary_gen:
    - make package
    - cp *.deb {config.binary_dir}

depends:
  - pybind11
  - OpenSoT

depends_if:
  xacro_gen:
    - capsule_generation
```

### Multi-project CMake (multiple CMakeLists.txt)

```yaml
clone:
  type: git
  server: github.com
  repository: advrhumanoids/iit-kyon-ros-pkg.git
  tag: ros2
  ros_src: true

build:
  type: cmake
  cmakelists:
    - kyon_urdf: kyon_urdf
    - kyon_srdf: kyon_srdf
    - kyon_gazebo: kyon_gazebo

depends:
  - xbot2_ros
```

### Custom fetch and build

```yaml
clone:
  type: custom
  cmd:
    - wget -O {srcdir}/archive.zip https://example.com/v1.0.zip
    - unzip {srcdir}/archive.zip -d {srcdir}

build:
  type: custom
  cmd:
    - python -m pip install -e {srcdir}
  env_hooks:
    - eval "$(register-python-argcomplete mytool)"
```

### Meta-package (dependency bundle)

```yaml
depends:
  - xbot2
  - cartesian_interface
  - iit-centauro-ros-pkg

depends_if:
  binary_gen:
    - xbot_env
    - xbot2_desktop_full
```
