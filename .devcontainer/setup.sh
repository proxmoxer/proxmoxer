#!/bin/bash

# hide the mass-formatting commits from git blames
git config blame.ignorerevsfile .git-blame-ignore-revs

# install the git hook for pre-commit
pre-commit install

# run pre-commit on a simple file to ensure it downloads all needed tools
pre-commit run --files .pre-commit-config.yaml
