# GitHub Actions conventions

## Pinned action versions

Actions must be pinned to a full commit SHA for security. The comment after the
SHA must be the **full semver version** (e.g. `v4.1.0`), not a bare major-only
tag (e.g. `v4`). Look up the latest release tag in the
matching major version series and use its full semver string as the comment.

**Never guess or hallucinate a commit SHA.** Always resolve the SHA from the
upstream repository before writing or updating a `uses:` line.
