# GitHub Actions conventions

## Pinned action versions

Actions must be pinned to a full commit SHA for security. The comment after the
SHA must be the **full semver version** (e.g. `v4.1.0`), not a bare major-only
tag (e.g. `v4`).

```yaml
# ✅ correct
uses: docker/login-action@4907a6ddec9925e35a0a9e82d7399ccc52663121 # v4.1.0

# ❌ incorrect – comment is not full semver
uses: docker/login-action@4907a6ddec9925e35a0a9e82d7399ccc52663121 # v4
```

When adding or updating an action, look up the latest release tag in the
matching major version series and use its full semver string as the comment.

## Looking up action hashes

**Never guess or hallucinate a commit SHA.** Always resolve the SHA from the
upstream repository before writing or updating a `uses:` line:

1. Use the GitHub API (or `gh release list`) to find the latest release tag.
2. Resolve that tag to its commit SHA — e.g. via the GitHub API refs endpoint or
   `git ls-remote https://github.com/<owner>/<repo> refs/tags/<tag>`.
3. Use the resolved SHA in the `uses:` line and the release tag as the comment.

```yaml
# How to resolve a SHA for docker/login-action v4.1.0:
# gh api repos/docker/login-action/git/ref/tags/v4.1.0 --jq '.object.sha'
# (follow any tag object to its commit SHA if the object type is "tag")
```
