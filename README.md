# AI-Powered PR Review Bot

An educational GitHub Actions example that sends a pull-request diff to Claude and posts a concise review summary to Slack. The bot reports a PR summary, up to three actionable findings with file and line references, and a Low/Medium/High complexity rating.

## Architecture

```text
PR opened or updated
        |
        v
GitHub Actions checks out trusted base-branch bot code
        |
        v
review.py fetches the PR diff (does not execute PR code)
        |
        v
Claude returns a validated JSON review
        |
        v
Slack incoming webhook posts Block Kit sections
```

## Setup

1. Create an Anthropic account at [console.anthropic.com](https://console.anthropic.com/), create an API key, and check the Console's billing/credits page. Trial credits and payment requirements vary by account and region.
2. Create a Slack incoming webhook for the channel where reviews should appear. See [docs/EXECUTION_GUIDE.md](docs/EXECUTION_GUIDE.md) for the full setup and a `curl` test.
3. In the GitHub repository, add `ANTHROPIC_API_KEY` and `SLACK_WEBHOOK_URL` under **Settings -> Secrets and variables -> Actions -> New repository secret**.
4. Add this project to the repository's default branch. Enable GitHub Actions if required by repository policy.
5. Open a PR from a branch in the same repository. The workflow runs for `opened` and `synchronize` events.

Install and run locally with Python 3.10 or newer:

```sh
python -m pip install -r requirements.txt
export ANTHROPIC_API_KEY="..."
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
export PR_DIFF_URL="https://github.com/OWNER/REPOSITORY/pull/1.diff"
export GITHUB_TOKEN="..." # Optional; useful for private repositories
python review.py
```

Never commit API keys or webhook URLs. Rotate any credential that is accidentally exposed. `CLAUDE_MODEL` optionally overrides the default model configured in the workflow.

## Security Notes

- The workflow uses `pull_request`, read-only `GITHUB_TOKEN` permissions, and checks out the PR base branch. It does not run code from the PR head.
- GitHub withholds repository secrets from workflows triggered by fork PRs. This example skips the review when secrets are unavailable; fork PR reviews need a separately designed trusted service or maintainer-triggered workflow.
- The diff is untrusted input. The download is capped at 1 MB, and model input is capped at 80,000 characters. Larger diffs are truncated, not comprehensively reviewed.
- This is an educational reviewer, not a security boundary or merge approval. Require human review and test findings before using it for production decisions.

## Example Slack Notification

> **Screenshot placeholder:** Add a screenshot of the Slack notification here after running a test PR.

The message contains the PR summary, issue locations and details, and complexity rating. A clean diff produces an explicit "No actionable issues found" message.

## HTML Demo

Open [`index.html`](index.html) directly in a browser to explore the sample review dashboard. It is a static front-end demo with example PR data; live reviews still run through `review.py` in GitHub Actions and are delivered to Slack. No API credentials are used in the HTML page.

## Test Fixtures

The scripts in [`sample_issues/`](sample_issues/) include intentionally unsafe SQL interpolation and missing resource/error handling; `fragile_parser.py` shows defensive input validation. They are fixtures for a separate test repository; do not use the intentionally flawed examples in application code.

For account setup, payload field names, an end-to-end test, test PR scenarios, a five-minute demo, and scaling answers, see [docs/EXECUTION_GUIDE.md](docs/EXECUTION_GUIDE.md).