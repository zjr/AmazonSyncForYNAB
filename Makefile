SHELL := /opt/homebrew/bin/bash

POETRY := $(shell command -v poetry 2> /dev/null)
INSTALL_STAMP := .install.stamp

.PHONY: env run dev default help

default: help

help:
	@printf 'Runs a python program which uses Selenium WebDriver with Chromium to read\n'\
	'through your Amazon purchases and update matching transactions in YNAB.\n\n'
	@printf 'The Makefile runs `help` by default. You may want:\n'
	@printf '\t%s\n\t\t%s\n' 'make run' 'standard run, executes script somewhat quietly'
	@printf '\t%s\n\t\t%s\n' 'make dev' 'runs in debug mode, opening up a browser window'
	@printf '\n'
	@printf 'Having trouble with dependencies? Try:\n'
	@printf '\t%s\n\t\t%s\n' 'asdf install' 'should install python & poetry from .tool-versions'
	@printf '\t%s\n\t\t%s\n' 'rm $(INSTALL_STAMP)' 'should ask poetry to install deps'

install: $(INSTALL_STAMP)
$(INSTALL_STAMP): pyproject.toml poetry.lock
	@if [ -z $(POETRY) ]; then \
		echo "Poetry could not be found"; \
		exit 2; \
	fi
	$(POETRY) install
	touch $(INSTALL_STAMP)

run: $(INSTALL_STAMP)
	@$(POETRY) env activate && $(POETRY) run python src/main.py

dev: $(INSTALL_STAMP)
	$(POETRY) run python src/main.py --debug

