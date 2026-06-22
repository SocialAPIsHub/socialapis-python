# Security Policy

## Supported versions

We patch security issues on the **latest minor release line** only.

| Version | Supported |
|---|---|
| 0.1.x | ✅ |
| < 0.1 | ❌ |

If you're on an older version, update to the latest `socialapis-sdk` and
re-test before reporting — the issue may already be fixed.

## Reporting a vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**
Public issues are indexed instantly and attackers watch for them.

Instead, email **support@socialapis.io** with:

- A description of the issue
- Steps to reproduce (or a minimal proof of concept)
- The version(s) affected
- Your assessment of the impact (which endpoints / users are at risk)

If the issue affects the hosted API at `api.socialapis.io` (rather than
this Python SDK specifically), the same address routes correctly — we'll
triage it on our backend.

## What we promise

- **Acknowledgement within 72 hours** that we've received the report
- **Initial assessment within 7 days** — whether we've reproduced it and
  what severity we're treating it as
- **A patched release** as soon as a fix is ready, typically within a
  week for critical issues
- **Credit in the CHANGELOG** if you'd like (let us know)

## Out of scope

These aren't security issues for this SDK:

- API rate limits / quota enforcement — those are billing / API behaviour
- Wrong / outdated data returned by the API — that's a backend issue
- Username enumeration via public endpoints — Instagram / Facebook
  already expose that publicly; the SDK just reflects it
- Anything requiring physical access to a machine running the SDK
