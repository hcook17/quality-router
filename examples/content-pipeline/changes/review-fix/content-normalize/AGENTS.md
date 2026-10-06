# content-normalize

Turns raw ingested packages (SCORM, xAPI, video, PDF) into `ContentItem`s.

- Build and test: `mvn -B verify` (JaCoCo report in `target/site/jacoco/jacoco.xml`).
- Code: `src/main/java/edu/acme/normalize`. Entry point: `edu.acme.normalize.Normalizer`.
- Licence parsing: `src/main/java/edu/acme/normalize/LicenseParser.java`.
- Contracts we publish: `contracts/content-item.schema.json` (store and delivery vendor it).
  Keep `legacyCode` until delivery stops reading it; `qr contracts check` enforces this.
- Never log learner PII.
- Tag every test with the acceptance criterion it checks: `@Tag("AC-n")`.
