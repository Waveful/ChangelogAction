# Changelog Action
Github Action to generate a `CHANGELOG.md` on new tags.

### Inputs

| Name | Description | Value Type | Required | Default Value |
|------|-------------|------------|----------|---------------|
| `target-branch` | Target branch | string | false | `master` |
| `github-token` | GitHub Token for Auth | string | true | - |
| `github-username` | GitHub Username | string | false | `Dolful` |
| `github-email` | GitHub Email | string | false | `github-bot@waveful.app` |

### Usage
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

      - name: Changelog
        uses: Waveful/ChangelogAction@0.1.1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

### Credits
_ChangelogAction_ is made with ♥ by [Waveful](https://github.com/Waveful).
