#!/bin/zsh
# Young Bull Terminal nightly refresh: regenerate, commit, deploy to GitHub Pages.
# Run by launchd (com.youngbull.terminal-refresh). Safe to run by hand.
set -euo pipefail
cd "$(dirname "$0")"

LOG=refresh.log
echo "--- $(date -u '+%Y-%m-%d %H:%M UTC') refresh start" >> "$LOG"

if ! python3 generate.py >> "$LOG" 2>&1; then
  echo "generate FAILED, keeping previous site" >> "$LOG"
  exit 1
fi

if [ -d .git ] && git remote get-url origin > /dev/null 2>&1; then
  git add docs/
  if ! git diff --cached --quiet; then
    git commit -q -m "terminal: refresh $(date -u '+%Y-%m-%d %H:%M UTC')"
    git push -q origin main >> "$LOG" 2>&1 && echo "deployed" >> "$LOG"
  else
    echo "no changes" >> "$LOG"
  fi
else
  echo "no git remote yet, generated locally only" >> "$LOG"
fi
