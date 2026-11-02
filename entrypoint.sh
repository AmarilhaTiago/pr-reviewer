#!/bin/sh
# Positional args come from action.yml, in this order:
# 1 provider  2 model  3 api-key  4 rules-path  5 min-severity  6 max-tokens-per-pr  7 github-token
set -e

if [ -z "$3" ]; then
  echo "::notice::pr-reviewer skipped: no API key (secrets are not available to PRs from forks)."
  exit 0
fi

export LLM_PROVIDER="$1"
export LLM_MODEL="$2"
export LLM_API_KEY="$3"
export GITHUB_TOKEN="$7"
[ -n "$6" ] && export MAX_TOKENS_PER_PR="$6"

if [ -n "$4" ]; then
  exec reviewer pr --min-severity "$5" --rules "$4"
fi
exec reviewer pr --min-severity "$5"
