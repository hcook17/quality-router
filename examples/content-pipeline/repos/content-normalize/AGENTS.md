# content-normalize

Turns raw ingested packages (SCORM, xAPI, video, PDF) into `ContentItem`s.

- Build and test: `mvn -B verify` (JaCoCo report in `target/site/jacoco/jacoco.xml`).
- Code: `src/main/java/edu/acme/normalize`. Entry point: `edu.acme.normalize.Normalizer`.
- Legacy code mapping lives in `src/main/java/edu/acme/normalize/LegacyMapper.java`.
- Contracts we publish: `contracts/content-item.schema.json` (store and delivery vendor it).
- Never log learner PII.
- Tag every test with the acceptance criterion it checks: `@Tag("AC-n")`.
