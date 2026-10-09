# Execution Guide

## Accounts and Secrets

### Anthropic API key

1. Create or sign in at [console.anthropic.com](https://console.anthropic.com/).
2. Complete any account verification requested by the Console.
3. Open the API keys area, create a key, and copy it once into a password manager or directly into GitHub Actions secrets.
4. Check the Console's billing, usage, and credits pages before calling the API. Trial credits and whether a payment method is required vary by account, location, and current terms; do not assume API use is free.
5. Set usage limits or alerts where available. Revoke and replace an exposed key.

### Slack incoming webhook

1. Create a workspace at [slack.com/get-started/create](https://slack.com/get-started/create), or use an existing workspace where you can manage apps.
2. Visit [api.slack.com/apps](https://api.slack.com/apps), choose **Create New App**, and create an app for the workspace.
3. Select **Incoming Webhooks**, turn the feature on, and choose **Add New Webhook to Workspace**.
4. Select the destination channel and authorize the app. Copy the generated webhook URL; treat it like a password.
5. Test the URL without putting it in a committed file. In an interactive shell, enter the URL when prompted:

```sh
printf 'Webhook URL: '
read -s SLACK_WEBHOOK_URL
printf '\n'
export SLACK_WEBHOOK_URL
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Test message from the PR review bot"}' \
  "$SLACK_WEBHOOK_URL"
unset SLACK_WEBHOOK_URL
```

Slack normally responds with `ok`. If the URL was exposed, revoke it in Slack app settings and create a replacement.

### GitHub repository secrets

In the repository, open **Settings -> Secrets and variables -> Actions -> New repository secret**. Create `ANTHROPIC_API_KEY` and `SLACK_WEBHOOK_URL`, then paste each matching value. GitHub masks secrets in logs, but masking is not a substitute for avoiding prints, untrusted workflow code, or shell interpolation. Never put secrets in source, PR descriptions, or screenshots.

## GitHub Actions and Event Payload

A workflow is a YAML file under `.github/workflows/`. Its `on` block selects events and event types. Here, `pull_request` with `opened` and `synchronize` runs when a PR opens and when new commits are pushed to its branch. A workflow run contains jobs; jobs run on runners and may run in parallel. Each job contains ordered steps, which invoke actions or shell commands. A failed step normally fails the job and prevents later steps from running.

The `pull_request` event payload is JSON. Useful fields include:

- `action`: `opened` or `synchronize`.
- `number`: the PR number.
- `repository.full_name`: repository in `OWNER/REPOSITORY` form.
- `pull_request.diff_url`: unified diff URL; `pull_request.patch_url` is also available.
- `pull_request.title`, `body`, `user.login`, `html_url`, `base.ref`, `head.ref`, `head.sha`, and `base.sha`: common PR metadata.

In Actions, equivalent contexts are available through `github.event` and `github.repository`. The complete payload file path is exposed in `GITHUB_EVENT_PATH`. Prefer event data over scraping HTML pages.

### Secrets in Python

Actions maps secrets into environment variables explicitly in a step:

```yaml
env:
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

Python reads required values with `os.environ["ANTHROPIC_API_KEY"]` and `os.environ["SLACK_WEBHOOK_URL"]`; a missing key raises `KeyError`. Use `os.environ.get(...)` for optional values. Never print credentials. GitHub does not provide repository secrets to fork PR workflows, which this example skips.

## System Flow and Review Contract

```text
Contributor opens or updates PR
          |
          v
GitHub pull_request event (opened | synchronize)
          |
          v
Actions checks out trusted PR base-branch bot code
          |
          v
review.py downloads pull_request.diff_url
          |
          v
Claude reviews the diff as untrusted data and returns JSON
          |
          v
Python validates the schema and posts Slack Block Kit payload
```

The system instruction in `review.py` requests exactly `summary`, `issues`, and `complexity`. `issues` is limited to three objects containing `file`, `line`, `title`, and `details`. `complexity.rating` must be `Low`, `Medium`, or `High`, with short `reasoning`. The prompt asks for changed-code locations and an empty issue list when no actionable issue is found. The script validates the result before sending Slack.

The script limits a diff download to 1 MB and sends at most 80,000 characters to Claude. When capped, it marks the text as truncated. This protects a demo from unbounded requests, but large PRs need chunking for complete coverage.

## End-to-End Test

1. Put the workflow and `review.py` on the repository's default branch, configure both secrets, and confirm Actions is enabled.
2. Create a branch such as `demo/review-bot`; add a buggy Python file or modify one of the `sample_issues/` fixtures.
3. Commit and push, then open a PR targeting the branch that contains the workflow. Use a same-repository PR for this demo; fork PRs do not receive these secrets.
4. Open **Actions** and select **AI pull request review**. Verify a run starts on `opened`; push another commit and verify another run for `synchronize`.
5. Confirm the run checks out the base branch, completes the review step, and posts a summary, findings, and complexity to Slack.
6. For failures, check secret names, webhook/channel access, Anthropic billing/model access, and diff fetch permissions. Never add credentials to logs while debugging.

### Suggested test PRs

1. **Bug/security PR:** add SQL built by interpolating untrusted input, omit a context manager for a resource, and add a missing-data path that raises. Expect an actionable security or correctness finding with a location, a concise summary, and complexity reflecting the changed behavior.
2. **Clean PR:** add a small typed helper with input validation, a resource context manager, and a focused test. Expect a positive summary, an empty `issues` array rather than invented nitpicks, and Low complexity with brief reasoning.

Model output is probabilistic. Verify findings against the diff; this is not a substitute for tests or human review.

## Five-Minute Interview Demo

1. **0:00-0:40 — Frame the problem.** Describe the bot as a fast, advisory pass. It does not approve or merge code.
2. **0:40-1:30 — Open a live PR.** Push a small known issue and open a same-repository PR. Point out `opened`; explain that later pushes emit `synchronize`.
3. **1:30-2:15 — Show Actions.** Trace trusted base-branch checkout, Python setup, dependency installation, and script execution. Call out read-only permissions and no PR-head code execution.
4. **2:15-3:10 — Read Slack.** Show the summary, a finding with file and line, and complexity. Compare the output with the actual diff and mention the clean-PR expectation.
5. **3:10-4:10 — Explain the prompt.** It limits the review to actionable changed-code issues, constrains output to a small schema, requests evidence-backed locations, and asks for no findings when none exist. Schema validation blocks malformed output from reaching Slack.
6. **4:10-5:00 — Discuss tradeoffs.** Explain fork-secret restrictions, model cost, diff truncation, and human verification. Close with chunking, caching, and metrics as production improvements.

## Scaling Answers

### Large diffs and context limits

Do not silently treat a truncated diff as fully reviewed. This starter marks truncation and bounds input. For production, parse unified diffs by file and hunk, skip generated/vendor/lock files according to repository policy, and group hunks into token-budgeted batches with overlap where context matters. Review batches separately, then synthesize and deduplicate findings and assign final complexity. Preserve file and new-line coordinates through chunking. For unusually large PRs, report partial coverage or fail clearly instead of implying full coverage. Changed-file retrieval with surrounding base/head context is another option, subject to the same budget.

### Lower API cost at scale

- Filter generated files and low-value changes before making model calls; set per-review token budgets.
- Cache by diff/blob hash, prompt version, and model version. Make Slack delivery idempotent per PR head SHA.
- Route small or low-risk diffs to a lower-cost model and reserve stronger models for security-sensitive or ambiguous changes; measure review quality first.
- Batch files within bounded requests where supported, and summarize chunks before synthesis instead of repeatedly sending the whole diff.
- Limit concurrency, retry only transient failures with backoff, avoid duplicate runs for identical commits, and track per-PR token/cost metrics with budget alerts.

Track false positives, missed issues, latency, and cost; optimize for reviewed quality, not finding volume.