from hashlib import sha256
from pathlib import Path


# Render Docker packaging regressions: lockfile COPY/install flow and dockerignore safety.
class TestRenderDockerLockflow:
    def test_dockerfile_copies_full_frontend_not_direct_lockfile(self):
        dockerfile = Path("/app/Dockerfile").read_text()

        assert "COPY frontend/ ./" in dockerfile
        assert "COPY frontend/yarn.lock" not in dockerfile

    def test_dockerfile_has_conditional_lock_install_with_required_flags(self):
        dockerfile = Path("/app/Dockerfile").read_text()

        assert "if [ -f yarn.lock ]; then" in dockerfile
        assert "yarn install --frozen-lockfile --ignore-engines --network-timeout 120000" in dockerfile
        assert "yarn install --ignore-engines --network-timeout 120000" in dockerfile

    def test_dockerfile_build_env_matches_production_expectation(self):
        dockerfile = Path("/app/Dockerfile").read_text()

        assert "ENV REACT_APP_BACKEND_URL=/" in dockerfile
        assert "ENV GENERATE_SOURCEMAP=false" in dockerfile
        assert "ENV DISABLE_EMERGENT_OVERLAY=true" in dockerfile
        assert "ENV ENABLE_HEALTH_CHECK=false" in dockerfile
        assert "RUN yarn build" in dockerfile

    def test_with_lock_fixture_preserves_source_lockfile_checksum(self):
        source_lock = Path("/app/frontend/yarn.lock")
        with_lock = Path("/root/render-lock-check/with-lock/yarn.lock")

        assert source_lock.is_file()
        assert with_lock.is_file()
        assert sha256(source_lock.read_bytes()).hexdigest() == sha256(with_lock.read_bytes()).hexdigest()

    def test_no_lock_fixture_generates_new_lockfile(self):
        no_lock = Path("/root/render-lock-check/no-lock/yarn.lock")
        assert no_lock.is_file()
        assert no_lock.stat().st_size > 0

    def test_branch_execution_logs_exist(self):
        with_log = Path("/app/test_reports/with_lock_install.log")
        no_log = Path("/app/test_reports/no_lock_install.log")

        assert with_log.is_file()
        assert no_log.is_file()

        with_log_text = with_log.read_text()
        no_log_text = no_log.read_text()

        assert "=== with-lock branch start ===" in with_log_text
        assert "Done in" in with_log_text
        assert "=== no-lock branch start ===" in no_log_text
        assert "info No lockfile found." in no_log_text
        assert "success Saved lockfile." in no_log_text

    def test_dockerignore_excludes_env_node_modules_and_build(self):
        dockerignore = Path("/app/.dockerignore").read_text().splitlines()
        rules = {line.strip() for line in dockerignore if line.strip() and not line.strip().startswith("#")}

        assert "**/node_modules" in rules
        assert "**/build" in rules
        assert "**/.env" in rules
        assert "**/.env.*" in rules

    def test_dockerignore_does_not_exclude_required_frontend_source(self):
        dockerignore_text = Path("/app/.dockerignore").read_text()

        assert "frontend/package.json" not in dockerignore_text
        assert "frontend/src" not in dockerignore_text
        assert "frontend/public" not in dockerignore_text
        assert "frontend/craco.config.js" not in dockerignore_text
        assert "frontend/tailwind.config.js" not in dockerignore_text
        assert "frontend/postcss.config.js" not in dockerignore_text