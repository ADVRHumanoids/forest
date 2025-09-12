#!/bin/bash
rm -rf dist
python3 -m build
twine upload -u __token__ -p $PYPI_TOKEN --verbose dist/*
