D := $(HOME)/.local/share/thermal-printer
BIN := $(HOME)/.local/bin

.PHONY: help install test run once uninstall launchd-install launchd-uninstall

LABEL := com.thermal-printer.poller
PLIST := $(HOME)/Library/LaunchAgents/$(LABEL).plist
LOG := $(HOME)/Library/Logs/thermal-poller.log

help:
	@echo "make install    install btprint and thermal-poller into ~/.local/bin"
	@echo "make test       run the unit tests"
	@echo "make run        poll every 30 s (asks for settings on first run)"
	@echo "make once       poll once"
	@echo "make launchd-install    poll every 60 s in the background (launchd user agent)"
	@echo "make launchd-uninstall  stop and remove the agent"
	@echo "make uninstall  remove the install (keeps ~/.config/thermal-printer)"

install:
	mkdir -p $(D) $(BIN)
	[ -d $(D)/venv ] || python3 -m venv $(D)/venv
	$(D)/venv/bin/pip -q install bleak pillow pyusb
	cp config.py btprint.py poller.py $(D)/
	printf '#!/bin/sh\nexec "$(D)/venv/bin/python" "$(D)/btprint.py" "$$@"\n' > $(BIN)/btprint
	printf '#!/bin/sh\nexec "$(D)/venv/bin/python" "$(D)/poller.py" "$$@"\n' > $(BIN)/thermal-poller
	chmod +x $(BIN)/btprint $(BIN)/thermal-poller
	@echo "installed. Next: make run"

test: install
	cd $(CURDIR) && PYTHONPATH=. $(D)/venv/bin/python -m unittest discover -s tests

run: install
	$(BIN)/thermal-poller

once: install
	$(BIN)/thermal-poller --once

uninstall:
	rm -rf $(D) $(BIN)/btprint $(BIN)/thermal-poller

# One-shot every 60 s: launchd restarts nothing, so a crash or a sleeping Mac costs one poll.
launchd-install: install
	mkdir -p $(dir $(PLIST)) $(dir $(LOG))
	printf '%s\n' '<?xml version="1.0" encoding="UTF-8"?>' \
	  '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">' \
	  '<plist version="1.0"><dict>' \
	  '<key>Label</key><string>$(LABEL)</string>' \
	  '<key>ProgramArguments</key><array><string>$(BIN)/thermal-poller</string><string>--once</string></array>' \
	  '<key>StartInterval</key><integer>60</integer>' \
	  '<key>RunAtLoad</key><true/>' \
	  '<key>StandardOutPath</key><string>$(LOG)</string>' \
	  '<key>StandardErrorPath</key><string>$(LOG)</string>' \
	  '</dict></plist>' > $(PLIST)
	@if [ -f $(HOME)/.config/thermal-printer/config.json ] && grep -q '"token"' $(HOME)/.config/thermal-printer/config.json; then \
	  launchctl bootout gui/$$(id -u) $(PLIST) 2>/dev/null; launchctl bootstrap gui/$$(id -u) $(PLIST) && echo "agent loaded; log: $(LOG)"; \
	else echo "plist written, NOT loaded: no config yet. Run 'thermal-poller' once in a terminal, then 'make launchd-install' again."; fi

launchd-uninstall:
	-launchctl bootout gui/$$(id -u) $(PLIST)
	rm -f $(PLIST)
