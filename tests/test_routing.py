"""Exercise routing through the same CLI used by an installed skill."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
CATALOG = REPO / "skills/meta-h/scripts/catalog.py"


class RoutingTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.project = self.root / "project"
        self.library = self.root / "library"
        self.project.mkdir()
        shutil.copytree(REPO / "skills", self.library)
        self.env = dict(os.environ, HOME=str(self.root / "home"),
                        XDG_CACHE_HOME=str(self.root / "cache"),
                        CODEX_HOME=str(self.root / "home/.codex"),
                        CLAUDE_CONFIG_DIR=str(self.root / "home/.claude"))
        self.cli("sync", "--root", self.library)

    def cli(self, *args, project=None, success=True):
        proc = subprocess.run(
            [sys.executable, str(CATALOG), "--project", str(project or self.project), *map(str, args)],
            env=self.env, capture_output=True, text=True, check=False)
        if success:
            self.assertEqual(proc.returncode, 0, proc.stderr)
        else:
            self.assertNotEqual(proc.returncode, 0)
        return proc.stdout

    def test_real_routes_open_only_the_selected_instructions(self):
        eu = self.library / "voice-agent-eu/SKILL.md"
        eu.write_text(eu.read_text() + "\nPRIVATE_BODY_EU\n")
        self.cli("sync")
        cases = [
            ("Belgian warehouse needs a multilingual EU phone receptionist", "voice-agent-eu"),
            ("American HVAC receptionist on Retell", "voice-agent-us"),
            ("Check disk space on my slow Mac before a build", "mac-maintainer"),
        ]
        for query, skill in cases:
            with self.subTest(query=query):
                results = self.cli("search", query, "--limit", "1")
                self.assertEqual(results.split()[0], skill)
                self.assertNotIn("PRIVATE_BODY", results)
        self.assertIn("PRIVATE_BODY_EU", self.cli("show", "voice-agent-eu"))
        self.assertNotIn("PRIVATE_BODY_EU", self.cli("show", "voice-agent-us"))
        self.assertIn("No matching", self.cli("search", "quasiparticle spectroscopy"))

    def test_preferences_and_library_changes_stay_in_their_project(self):
        self.cli("alias", "add", "opening shift", "work-chief-of-staff")
        self.cli("sync")
        self.assertEqual(self.cli("search", "opening shift").split()[0], "work-chief-of-staff")
        other = self.root / "second-project"
        other.mkdir()
        self.cli("sync", "--root", self.library, project=other)
        self.assertNotIn("opening shift", self.cli("alias", "list", project=other))
        self.cli("alias", "remove", "opening shift")
        self.assertNotIn("opening shift", self.cli("alias", "list"))
        self.cli("sync", "--forget-root", self.library)
        self.cli("show", "voice-agent-us", success=False)
        self.assertIn("US", self.cli("show", "voice-agent-us", project=other))

    def test_deleted_skills_and_changed_symlinks_do_not_dispatch_stale_content(self):
        pkg = self.project / ".agents/skills"
        pkg.mkdir(parents=True)
        first = self.project / "first"
        second = self.project / "second"
        for directory in (first, second):
            directory.mkdir()
            (directory / "SKILL.md").write_text(
                "---\nname: test-local\ndescription: A local skill.\n---\n" + directory.name)
        link = pkg / "test-local"
        link.symlink_to(first, target_is_directory=True)
        self.cli("sync")
        self.assertIn("first", self.cli("show", "test-local"))
        link.unlink()
        link.symlink_to(second, target_is_directory=True)
        self.cli("show", "test-local", success=False)
        self.cli("sync")
        self.assertIn("second", self.cli("show", "test-local"))
        link.unlink()
        self.cli("sync")
        self.cli("show", "test-local", success=False)
