# Privacy And Consent Guide

This document is the deployment-facing version of the consent rules in `docs/11-privacy-consent.md`.

## Consent Types

- Service consent: required for clinic service records and operational processing.
- Research consent: optional and independently withdrawable.

## Withdrawal

Research consent withdrawal:

- Sets `research_consent=false`.
- Records `research_withdrawn_at`.
- Records `withdrawn_by`.
- Appends withdrawal notes.
- Writes an audit log entry.

## Operational Rules

- Explain consent in plain language before recording it.
- Do not deny service because research consent is declined.
- Do not place unnecessary sensitive details in free-text notes.
- Use anonymized exports for reporting and teaching.
- Confirm withdrawal requests in the audit log.
