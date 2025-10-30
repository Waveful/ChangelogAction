# Changelog Action
Github Action to generate a `CHANGELOG.md` on new tags.

This action is split into three steps:
1. [Prepare](#prepare-action) - Collects tag data, PRs, commits, and repository statistics.
2. [Generate](#generate-action) - Uses Claude Code AI to generate a human-readable changelog.
3. [Notify](#notify-action) - Reformats the changelog with Claude Code AI and sends it via Telegram.

## Prepare Action

### Inputs

| Name | Description | Value Type | Required | Default Value |
|------|-------------|------------|----------|---------------|
| `github-token` | GitHub Token for Auth | string | Yes | - |

### Outputs

| Name | Description |
|------|-------------|
| `previous-tag` | Previous tag |
| `current-tag` | Current tag |
| `pr-count` | Number of PRs merged |
| `commit-count` | Number of commits |
| `author-count` | Number of unique authors |
| `files-changed` | Number of files changed |
| `additions` | Number of lines added |
| `deletions` | Number of lines deleted |
| `prs` | PR details with commits and AI summaries (base64 encoded) |
| `commits` | All commits including those not in PRs (base64 encoded) |

## Generate Action

### Inputs

| Name | Description | Value Type | Required | Default Value |
|------|-------------|------------|----------|---------------|
| `target-branch` | Target branch | string | No | `master` |
| `github-token` | GitHub Token for Auth | string | Yes | - |
| `github-username` | GitHub Username | string | No | `Dolful` |
| `github-email` | GitHub Email | string | No | `github-bot@waveful.app` |
| `claude-code-oauth-token` | Claude Code OAuth Token | string | Yes | - |
| `previous-tag` | Previous tag | string | Yes | - |
| `current-tag` | Current tag | string | Yes | - |
| `prs` | PR details (base64 encoded, from prepare step) | string | Yes | - |
| `commits` | All commits (base64 encoded, from prepare step) | string | Yes | - |

### Outputs

| Name | Description |
|------|-------------|
| `changelog` | Changelog (base64 encoded) |

## Notify Action

### Inputs

| Name | Description | Value Type | Required | Default Value |
|------|-------------|------------|----------|---------------|
| `changelog` | Changelog (base64 encoded, from generate step) | string | Yes | - |
| `claude-code-oauth-token` | Claude Code OAuth Token | string | Yes | - |
| `telegram-bot-token` | Telegram Bot Token | string | Yes | - |
| `telegram-chat-id` | Telegram Chat ID for notification | string | Yes | - |

### Outputs

This action does not produce any outputs. It sends a notification to Telegram with the changelog summary.

## Usage
###### prepare.yml
```yaml
name: Prepare

on:
  push:
    tags:
      - '*'

permissions:
  contents: read
  pull-requests: read
  actions: write

jobs:
  prepare-data:
    runs-on: ubuntu-latest
    name: Prepare PRs, Commits and Statistics
    steps:
      
      - name: Checkout
        uses: actions/checkout@v5
        with:
          fetch-depth: 0 # important! fetches full history & tags
      
      - name: Prepare Data
        id: prepare
        uses: Waveful/ChangelogAction/prepare@1.1.2
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Print Statistics
        id: statistics
        run: |
          echo "Authors: ${{ steps.prepare.outputs.author-count }}"
          echo "PRs: ${{ steps.prepare.outputs.pr-count }}"
          echo "Commits: ${{ steps.prepare.outputs.commit-count }}"
          echo "File changed: ${{ steps.prepare.outputs.files-changed }}"
          echo "Additions / Deletions: ${{ steps.prepare.outputs.additions }} / ${{ steps.prepare.outputs.deletions }}"
      
      - name: Trigger Changelog
        id: trigger-changelog
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh workflow run changelog.yml \
            -f from-ref="${{ steps.prepare.outputs.previous-tag }}" \
            -f to-ref="${{ steps.prepare.outputs.current-tag }}" \
            -f commits="${{ steps.prepare.outputs.commits }}" \
            -f prs="${{ steps.prepare.outputs.prs }}"
```

###### changelog.yml
```yaml
name: Changelog

on:
  workflow_dispatch:
    inputs:
      from-ref:
        required: true
        type: string
      to-ref:
        required: true
        type: string
      commits:
        required: true
        type: string
      prs:
        required: true
        type: string

permissions:
  contents: write
  id-token: write

jobs:
  changelog:
    runs-on: ubuntu-latest
    name: Generate changelog
    steps:
      
      - name: Checkout
        uses: actions/checkout@v5

      - name: Changelog
        id: changelog
        uses: Waveful/ChangelogAction/generate@1.1.2
        with:
          target-branch: master
          claude-code-oauth-token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
          previous-tag: ${{ inputs.from-ref }}
          current-tag: ${{ inputs.to-ref }}
          commits: ${{ inputs.commits }}
          prs: ${{ inputs.prs }}

      - name: Notify
        uses: Waveful/ChangelogAction/notify@1.1.2
        with:
          changelog: ${{ steps.changelog.outputs.changelog }}
          claude-code-oauth-token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
          telegram-bot-token: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          telegram-chat-id: ${{ secrets.TELEGRAM_CHAT_ID }}
```

## Credits
_ChangelogAction_ is made with ♥ by [Waveful](https://github.com/Waveful) and it's released under the [Apache License 2.0](./LICENSE).
