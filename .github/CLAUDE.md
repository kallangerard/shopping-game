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
