# Security And Privacy Policy

## Scope

This policy applies to the repository, documentation, release artifacts,
container configuration, GitHub Actions workflows, and generated text or audio
files.

## Prohibited Public Data

Do not commit or publish:

- Personal names, GitHub account handles, email addresses, or account IDs.
- Windows user-profile paths, Unix home paths, or absolute local paths.
- Computer serial numbers, device IDs, host names, MAC addresses, private IP
  addresses, or unique hardware fingerprints.
- Exact personal hardware inventory when it is not required to reproduce a bug.
- Passwords, access tokens, cookies, private keys, `.env` files, or credential
  stores.
- Personal audio recordings, voice samples, conversation logs, or model outputs
  unless the owner explicitly approved publication.
- Private model weights, datasets, or generated data outside the documented
  model-download flow.

## Required Replacements

Use neutral placeholders in documentation and examples:

```text
<owner>
<repository>
<repository-url>
<workspace>
<model-directory>
<output-directory>
<gpu>
<cpu>
```

Prefer environment variables or runtime discovery over hard-coded account,
repository, drive, and device values.

## Repository Controls

- Keep `.env`, credential files, model weights, audio, logs, caches, PID files,
  and backup bundles in `.gitignore`.
- Keep model weights outside the image and mount them at runtime.
- Use GitHub Actions secrets and `GITHUB_TOKEN`; never write tokens to files.
- Derive GHCR owners and repository names at runtime instead of embedding them.
- Run a privacy scan before every release:

```powershell
git grep -n -I -E "([A-Za-z]:\\\\Users\\\\|/home/|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+|gh[pousr]_[A-Za-z0-9_]+)"
git log --all --format="%an <%ae>" | Sort-Object -Unique
```

- Review Git history, tags, releases, workflow logs, and generated artifacts,
  not only the current working tree.

## Credential Incident Response

If a credential is exposed:

1. Revoke and rotate it immediately.
2. Remove it from the current files and rewrite affected Git history.
3. Force-update the public branch and tags after verifying the sanitized repo.
4. Inspect GitHub Actions logs, releases, caches, forks, and package metadata.
5. Document the incident without repeating the secret.

## Audio And Voice Privacy

- Obtain permission before cloning or publishing another person's voice.
- Mark synthetic audio as AI-generated.
- Do not use generated voice for impersonation, fraud, harassment, identity
  verification bypass, or unauthorized commercial distribution.
- Keep personal recordings and unreleased reference audio outside the public
  repository.

## Review Checklist

Before publishing:

```text
No personal account names or emails
No local absolute paths
No hardware serial numbers or unique device identifiers
No credentials or private keys
No private audio or model weights
No personal repository or registry URLs
Git history and commit authors sanitized
GitHub Actions and release artifacts inspected
```

## Reporting

Report privacy or security issues privately through the repository's security
advisory feature. Do not open a public issue containing credentials, personal
data, private audio, or exploit details.
