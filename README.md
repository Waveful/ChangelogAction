# Changelog Action
Github Action to generate a `CHANGELOG.md` on new tags.

This action is split into two steps:
1. **Prepare** - Collects tag data, PRs, commits, and repository statistics.
2. **Generate** - Uses Claude Code AI to generate a human-readable changelog.

## Prepare Action

### Inputs

| Name | Description | Value Type | Required | Default Value |
|------|-------------|------------|----------|---------------|
| `target-branch` | Target branch | string | false | `master` |
| `github-token` | GitHub Token for Auth | string | true | - |

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
| `target-branch` | Target branch | string | true | `master` |
| `github-token` | GitHub Token for Auth | string | true | - |
| `github-username` | GitHub Username | string | false | `Dolful` |
| `github-email` | GitHub Email | string | false | `github-bot@waveful.app` |
| `claude-code-oauth-token` | Claude Code OAuth Token | string | true | - |
| `previous-tag` | Previous tag | string | true | - |
| `current-tag` | Current tag | string | true | - |
| `prs` | PR details (from prepare step) | string | true | - |
| `commits` | All commits (from prepare step) | string | true | - |

## Usage
```yaml
name: Changelog

on:
  push:
    tags:
      - '*'

jobs:
  changelog:
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - name: Checkout
        uses: actions/checkout@v5
        with:
          fetch-depth: 0 # important! fetches full history & tags

      - name: Prepare Data
        id: prepare
        uses: Waveful/ChangelogAction/prepare@0.1.1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}

      - name: Generate Changelog
        uses: Waveful/ChangelogAction/generate@0.1.1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          claude-code-oauth-token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
          previous-tag: ${{ steps.prepare.outputs.previous-tag }}
          current-tag: ${{ steps.prepare.outputs.current-tag }}
          prs: ${{ steps.prepare.outputs.prs }}
          commits: ${{ steps.prepare.outputs.commits }}
```

## Credits
_ChangelogAction_ is made with ♥ by [Waveful](https://github.com/Waveful).
