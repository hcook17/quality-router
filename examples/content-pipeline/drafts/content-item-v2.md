# Spec: content item v2 (licensing) — prose draft

Frame: front ends must stop showing course content whose licence is unknown.
Owner: content platform. Repos: content-normalize, content-store, content-delivery.

## Acceptance criteria

- AC-1 Normalized titles are trimmed of surrounding whitespace.
- AC-2 Every normalized item carries a `licenseId` taken from the package manifest.
- AC-3 A manifest without a parseable licence is handled gracefully; normalization never fails on it.
- AC-4 Delivery MUST NOT return items whose `licenseId` is missing.

## Constraints

- `legacyCode` SHALL stay in the contract until delivery stops reading it. [check: contracts check]
- Licence writes MUST go through the repository layer in a single transaction.
- Logs MUST NOT contain learner names or emails.
- Default licence for legacy SCORM packages: TBD.
