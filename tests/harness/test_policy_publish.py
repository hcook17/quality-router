"""Default policy: Gradle/Maven publish and release tasks named in camelCase are artifact
publishing too (found on a Spring Boot 2.7 service whose Jenkins job runs `release` and
`artifactoryDockerPublish`)."""

from __future__ import annotations

from pathlib import Path

import pytest

from quality_router.harness.policy import DEFAULT_POLICY, Policy


@pytest.mark.parametrize("command,denied", [
    ("./gradlew -x test -Drepo=v2 artifactoryDockerPublish --stacktrace", True),
    ("./gradlew artifactoryPublish", True),
    ("gradle publishToMavenLocal", True),
    ("./gradlew --refresh-dependencies clean -x test release", True),
    ("mvn -B release:perform", True),
    ("./mvnw deploy:deploy-file -Dfile=x.jar", True),
    ("./gradlew test --tests '*PublishingServiceTest'", False),
    ("./gradlew build", False),
    ("mvn -B -q verify", False),
])
def test_publish_tasks(tmp_path: Path, command: str, denied: bool) -> None:
    decision = Policy.from_dict(DEFAULT_POLICY).check_command(command, tmp_path)
    assert (not decision.allow) is denied, decision.reason
