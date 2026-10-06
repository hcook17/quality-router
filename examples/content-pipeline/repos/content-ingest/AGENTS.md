# content-ingest

Receives course packages from authoring tools and publishes `RawPackage` events.

- Build and test: `mvn -B verify`.
- Contract we publish: `contracts/raw-package.schema.json` (content-normalize vendors it).
