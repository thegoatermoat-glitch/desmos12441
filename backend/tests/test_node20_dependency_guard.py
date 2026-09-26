import hashlib
import json
from pathlib import Path


# Node20 compatibility guard: dependency pins, lockfile signatures, fonts sync, and calculator math API usage.
class TestNode20DependencyGuard:
    def test_frontend_dependency_versions_are_node20_safe(self):
        package_json = Path("/app/frontend/package.json")
        pkg = json.loads(package_json.read_text())
        deps = pkg.get("dependencies", {})

        assert deps.get("@cortex-js/compute-engine") == "0.27.0"
        assert deps.get("mathlive") == "0.103.0"
        assert deps.get("katex") == "0.18.4"

    def test_lockfile_contains_expected_problematic_dependency_resolutions(self):
        lockfile = Path("/app/frontend/yarn.lock").read_text()

        assert '"@cortex-js/compute-engine@0.27.0"' in lockfile
        assert '"@cortex-js/compute-engine@0.24.1"' in lockfile
        assert 'mathlive@0.103.0' in lockfile
        assert 'katex@0.18.4' in lockfile
        assert 'commander@^8.3.0' in lockfile
        assert 'version "8.3.0"' in lockfile

        assert '"@cortex-js/compute-engine@0.135.0"' not in lockfile
        assert 'mathlive@0.110.0' not in lockfile
        assert 'katex@0.18.9' not in lockfile

    def test_mathlive_public_fonts_are_synced_with_dist_fonts(self):
        src_dir = Path("/app/frontend/node_modules/mathlive/dist/fonts")
        public_dir = Path("/app/frontend/public/mathlive/fonts")

        assert public_dir.is_dir()
        public_files = sorted([p for p in public_dir.iterdir() if p.is_file()])
        assert len(public_files) == 20

        # If node_modules is available in workspace, verify exact byte/hash parity.
        if src_dir.is_dir():
            src_files = sorted([p for p in src_dir.iterdir() if p.is_file()])
            assert len(src_files) == 20

            src_map = {
                p.name: (p.stat().st_size, hashlib.sha256(p.read_bytes()).hexdigest())
                for p in src_files
            }
            public_map = {
                p.name: (p.stat().st_size, hashlib.sha256(p.read_bytes()).hexdigest())
                for p in public_files
            }
            assert src_map == public_map

    def test_calculator_uses_compute_engine_n_and_angular_unit(self):
        calculator_lib = Path("/app/frontend/src/lib/calculator.js").read_text()

        assert "engine.angularUnit = mode.toLowerCase();" in calculator_lib
        assert "const result = expr.N();" in calculator_lib
        assert "const value = result.valueOf();" in calculator_lib

    def test_scramjet_npm_dependency_is_removed_but_vendored_runtime_assets_remain(self):
        package_json = Path("/app/frontend/package.json")
        pkg = json.loads(package_json.read_text())
        deps = pkg.get("dependencies", {})

        assert "@mercuryworkshop/scramjet" not in deps

        lockfile = Path("/app/frontend/yarn.lock").read_text()
        assert "@mercuryworkshop/scramjet" not in lockfile

        scramjet_dir = Path("/app/frontend/public/scramjet")
        assert (scramjet_dir / "scramjet.all.js").is_file()
        assert (scramjet_dir / "scramjet.bundle.js").is_file()
        assert (scramjet_dir / "scramjet.sync.js").is_file()
        assert (scramjet_dir / "scramjet.wasm.wasm").is_file()

    def test_workspace_frame_uses_vendored_scramjet_assets(self):
        frame_html = Path("/app/frontend/public/workspace/frame.html").read_text()
        frame_mjs = Path("/app/frontend/public/workspace/frame.mjs").read_text()

        assert "/scramjet/scramjet.all.js" in frame_html
        assert "wasm: '/scramjet/scramjet.wasm.wasm'" in frame_mjs
        assert "all: '/scramjet/scramjet.all.js'" in frame_mjs
        assert "sync: '/scramjet/scramjet.sync.js'" in frame_mjs