"""Hatch custom build hook -- builds the React frontend into the Python package."""

import os
import shutil
import subprocess
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    """Build the frontend with bun and place output in src/beanbay/static/."""

    def initialize(self, version: str, build_data: dict) -> None:
        """Build the frontend before the Python package is built.

        Parameters
        ----------
        version : str
            The build type ('standard' or 'editable'), not the package version.
        build_data : dict
            Mutable mapping of build metadata.

        Raises
        ------
        RuntimeError
            If the frontend directory or a package manager is not found.
        """
        frontend_dir = Path(self.root) / "frontend"
        static_dir = Path(self.root) / "src" / "beanbay" / "static"

        if not frontend_dir.is_dir():
            raise RuntimeError(
                f"Frontend directory not found: {frontend_dir}. "
                "Every build must include the frontend."
            )

        if shutil.which("bun"):
            install_cmd = ["bun", "install"]
            build_cmd = ["bun", "vite", "build"]
        elif shutil.which("npm"):
            install_cmd = ["npm", "install"]
            build_cmd = ["npx", "vite", "build"]
        else:
            raise RuntimeError("Neither bun nor npm found. Cannot build frontend.")

        pkg_version = self.metadata.version
        env = {
            **os.environ,
            "VITE_APP_VERSION": pkg_version,
        }

        subprocess.run(install_cmd, cwd=frontend_dir, check=True, env=env)  # noqa: S603
        subprocess.run(
            [
                *build_cmd,
                "--outDir",
                str(static_dir),
                "--emptyOutDir",
            ],
            cwd=frontend_dir,
            check=True,
            env=env,
        )
