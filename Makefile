D := $(HOME)/.local/share/thermal-printer
BIN := $(HOME)/.local/bin

.PHONY: help install run once uninstall

help:
	@echo "make install    install btprint and thermal-poller into ~/.local/bin"
	@echo "make run        poll every 30 s (asks for settings on first run)"
	@echo "make once       poll once"
	@echo "make uninstall  remove the install (keeps ~/.config/thermal-printer)"

install:
	mkdir -p $(D) $(BIN)
	[ -d $(D)/venv ] || python3 -m venv $(D)/venv
	$(D)/venv/bin/pip -q install bleak pillow
	cp config.py btprint.py poller.py $(D)/
	printf '#!/bin/sh\nexec "$(D)/venv/bin/python" "$(D)/btprint.py" "$$@"\n' > $(BIN)/btprint
	printf '#!/bin/sh\nexec "$(D)/venv/bin/python" "$(D)/poller.py" "$$@"\n' > $(BIN)/thermal-poller
	chmod +x $(BIN)/btprint $(BIN)/thermal-poller
	@echo "installed. Next: make run"

run: install
	$(BIN)/thermal-poller

once: install
	$(BIN)/thermal-poller --once

uninstall:
	rm -rf $(D) $(BIN)/btprint $(BIN)/thermal-poller
