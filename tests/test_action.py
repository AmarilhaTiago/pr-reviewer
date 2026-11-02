from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
ACTION = yaml.safe_load((ROOT / "action.yml").read_text(encoding="utf-8"))


def test_action_inputs_match_the_spec():  # AC1
    inputs = ACTION["inputs"]
    for name in ("provider", "model", "api-key", "rules-path", "min-severity", "max-tokens-per-pr"):
        assert name in inputs
    assert inputs["provider"]["default"] == "gemini"
    assert inputs["api-key"]["required"] and inputs["model"]["required"]


def test_action_is_docker_and_args_follow_entrypoint_order():  # AC1
    runs = ACTION["runs"]
    assert runs["using"] == "docker" and runs["image"] == "Dockerfile"
    names = [a.removeprefix("${{ inputs.").removesuffix(" }}") for a in runs["args"]]
    assert names == [
        "provider",
        "model",
        "api-key",
        "rules-path",
        "min-severity",
        "max-tokens-per-pr",
        "github-token",
    ]
    entrypoint = (ROOT / "entrypoint.sh").read_text(encoding="utf-8")
    assert "1 provider  2 model  3 api-key  4 rules-path  5 min-severity" in entrypoint


def test_entrypoint_skips_without_api_key():  # AC4
    entrypoint = (ROOT / "entrypoint.sh").read_text(encoding="utf-8")
    assert 'if [ -z "$3" ]' in entrypoint and "exit 0" in entrypoint
    assert "\r" not in entrypoint


def test_self_review_workflow_permissions_and_dogfooding():  # AC3
    wf = yaml.safe_load((ROOT / ".github/workflows/self-review.yml").read_text(encoding="utf-8"))
    assert wf["permissions"] == {"contents": "read", "pull-requests": "write"}
    steps = wf["jobs"]["review"]["steps"]
    assert any(step.get("uses") == "./" for step in steps)
