with import <nixpkgs> {};
let
  my-python-packages = python-packages: [
    python-packages.pip
    python-packages.setuptools
    python-packages.wheel
    python-packages.virtualenv
  ];
  my-python = python39.withPackages my-python-packages;
in
  pkgs.mkShell {
    buildInputs = [
      ncurses
      postgresql_12
      bashInteractive
      my-python
    ];
    shellHook = ''
      export PIP_PREFIX="$(pwd)/.pyenv/pip_packages"
      export PYTHONPATH="$PIP_PREFIX/lib/python3.9/site-packages:$PYTHONPATH"
      export PATH="$PIP_PREFIX/bin:$PATH"
      unset SOURCE_DATE_EPOCH
    '';
  }
