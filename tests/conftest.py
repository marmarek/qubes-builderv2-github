import os
import shutil
import subprocess
from pathlib import Path

import pytest

PROJECT_PATH = Path(__file__).resolve().parents[1]
DEFAULT_BUILDER_CONF = PROJECT_PATH / "tests/builder.yml"


@pytest.fixture(scope="session")
def workdir(tmpdir_factory):
    tmpdir = tmpdir_factory.mktemp("github-")

    # Better copy testing keyring into a separate directory to prevent locks inside
    # local sources (when executed locally).
    gnupghome = f"{tmpdir}/.gnupg"
    shutil.copytree(PROJECT_PATH / "tests/gnupg", gnupghome)
    os.chmod(gnupghome, 0o700)

    # Copy builder.yml
    shutil.copy2(DEFAULT_BUILDER_CONF, tmpdir)

    with open(f"{tmpdir}/builder.yml", "a") as f:
        f.write(
            f"""
artifacts-dir: {tmpdir}/artifacts

repository-upload-remote-host:
  rpm: {tmpdir}/repo/rpm/r4.2
  deb: {tmpdir}/repo/deb/r4.2

executor:
  type: qubes
  options:
    dispvm: "qubes-builder-dvm"
"""
        )

    # Clone qubes-builderv2
    subprocess.run(
        [
            "git",
            "-C",
            str(tmpdir),
            "clone",
            "-b",
            "main",
            "https://github.com/QubesOS/qubes-builderv2",
        ]
    )

    shutil.copytree(PROJECT_PATH, tmpdir / "qubes-builder-github")

    env = os.environ.copy()
    # Enforce keyring location
    env["GNUPGHOME"] = tmpdir / ".gnupg"
    # We prevent rpm to find ~/.rpmmacros and put logs into workdir
    env["HOME"] = tmpdir
    # Set PYTHONPATH with cloned qubes-builderv2
    env[
        "PYTHONPATH"
    ] = f"{tmpdir / 'qubes-builderv2'!s}:{os.environ.get('PYTHONPATH','')}"

    yield tmpdir, env
    # shutil.rmtree(tmpdir)
