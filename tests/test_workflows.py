"""The GitHub workflows: pinned actions, no workflow input pasted into a shell script, no failing empty commit."""

import re
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")
WORKFLOWS = sorted((Path(__file__).resolve().parents[1] / ".github" / "workflows").glob("*.yml"))


def steps():
    for f in WORKFLOWS:
        for job in yaml.safe_load(f.read_text())["jobs"].values():
            for step in job.get("steps", []):
                yield f.name, step


def test_actions_are_pinned_to_a_commit():
    for name, step in steps():
        if "uses" in step:
            assert re.fullmatch(r"[\w.-]+/[\w.-]+@[0-9a-f]{40}", step["uses"]), (name, step["uses"])


def test_inputs_reach_scripts_only_through_the_environment():
    # ${{ inputs.x }} or a step output pasted into `run:` is shell code for whoever sets it
    for name, step in steps():
        run = step.get("run", "")
        assert not re.search(r"\$\{\{\s*(inputs\.|github\.event\.inputs|steps\.[^}]*outputs)", run), (name, run[:200])


def test_data_map_does_not_fail_when_nothing_changed():
    text = (WORKFLOWS[0].parent / "datamap.yml").read_text()
    assert "git diff --cached --quiet" in text.split("Keep the map", 1)[1]
