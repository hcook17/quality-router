# Spec: content item v2 (licensing)

Frame: front ends must stop showing course content whose licence is unknown.
Owner: content platform. Repos: content-normalize, content-store, content-delivery.
Contract: `content-normalize/contracts/content-item.schema.json`

### AC-1 Normalized titles are trimmed

| title | expected title |
| --- | --- |
| `  Intro to Sterile Technique ` | Intro to Sterile Technique |
| `Hand Hygiene` | Hand Hygiene |
| (null) | `` |

### AC-2 The licence comes from the package manifest

| manifest | expected licenseId |
| --- | --- |
| `license=CC-BY-4.0` | CC-BY-4.0 |
| `lang=en; license=CC-BY-SA` | CC-BY-SA |
| `license= CC0 ` | CC0 |

### AC-3 A manifest without a parseable licence maps to UNLICENSED

Normalization never fails on it.

| manifest | expected licenseId |
| --- | --- |
| `lang=en` | UNLICENSED |
| `license=` | UNLICENSED |
| `license=  ` | UNLICENSED |
| (null) | UNLICENSED |

### AC-4 Delivery hides items without a licence

| licenseId | expected visible |
| --- | --- |
| CC-BY-4.0 | true |
| (null) | false |

## Constraints

- `legacyCode` SHALL stay in the contract until delivery stops reading it. [check: contracts check]
- Logs MUST NOT contain learner names or emails.
