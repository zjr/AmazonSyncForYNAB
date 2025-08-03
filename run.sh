#!/usr/bin/env bash

eval "$(poetry env activate)"
poetry run python src/main.py "$@"
