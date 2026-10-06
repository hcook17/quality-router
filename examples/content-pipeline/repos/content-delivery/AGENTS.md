# content-delivery

Serves licensed `ContentItem`s to the learner web and mobile front ends.

- Build and test: `mvn -B verify`.
- Published API: `contracts/delivery-api.openapi.json` (front ends generate clients from it).
- Vendored contract: `contracts/content-item.schema.json` (provider: content-normalize).
