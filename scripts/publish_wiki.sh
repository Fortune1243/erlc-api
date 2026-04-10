#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR="docs/wiki"
WIKI_DIR=".wiki-worktree"
PUSH_CHANGES="false"
REPO_URL=""
COMMIT_MESSAGE="${WIKI_COMMIT_MESSAGE:-docs(wiki): sync from docs/wiki}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source-dir)
      SOURCE_DIR="$2"
      shift 2
      ;;
    --wiki-dir)
      WIKI_DIR="$2"
      shift 2
      ;;
    --repo-url)
      REPO_URL="$2"
      shift 2
      ;;
    --push)
      PUSH_CHANGES="true"
      shift
      ;;
    --commit-message)
      COMMIT_MESSAGE="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

if [[ ! -d "$SOURCE_DIR" ]]; then
  echo "Source directory does not exist: $SOURCE_DIR" >&2
  exit 1
fi

if [[ -z "$REPO_URL" ]]; then
  REPO_URL="$(git remote get-url origin)"
fi

BASE_REPO_URL="${REPO_URL%.git}"
WIKI_REPO_URL="${BASE_REPO_URL}.wiki.git"

echo "Using wiki repo: $WIKI_REPO_URL"

if [[ -d "$WIKI_DIR/.git" ]]; then
  git -C "$WIKI_DIR" fetch origin
else
  rm -rf "$WIKI_DIR"
  git clone "$WIKI_REPO_URL" "$WIKI_DIR"
fi

if git -C "$WIKI_DIR" show-ref --verify --quiet refs/heads/master; then
  git -C "$WIKI_DIR" checkout master
else
  git -C "$WIKI_DIR" checkout -B master
fi

if git -C "$WIKI_DIR" rev-parse --verify origin/master >/dev/null 2>&1; then
  git -C "$WIKI_DIR" reset --hard origin/master
fi

find "$WIKI_DIR" -mindepth 1 -maxdepth 1 ! -name ".git" -exec rm -rf {} +
cp -R "${SOURCE_DIR}/." "$WIKI_DIR/"

if git -C "$WIKI_DIR" diff --quiet --exit-code && git -C "$WIKI_DIR" diff --cached --quiet --exit-code; then
  echo "No wiki changes detected."
  exit 0
fi

git -C "$WIKI_DIR" add -A
git -C "$WIKI_DIR" commit -m "$COMMIT_MESSAGE"

if [[ "$PUSH_CHANGES" == "true" ]]; then
  git -C "$WIKI_DIR" push origin master
  echo "Wiki changes pushed."
else
  echo "Wiki changes committed locally in $WIKI_DIR. Re-run with --push to publish."
fi
