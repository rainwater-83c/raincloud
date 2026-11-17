"""Build a Raincloud distribution with a one-file game executable."""

import importlib.util
from importlib import metadata
import marshal
import os
from pathlib import Path
import shutil
import subprocess
import sys
import sysconfig
import tempfile
import zipfile


ENGINE_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_FILES = ("__init__.py", "_archive.py")
def _copy_project_data(project_root: Path, distribution: Path) -> None:
	shutil.copy2(project_root / "config.py", distribution / "config.py")
	for directory in ("assets", "mods"):
		source = project_root / directory
		if source.is_dir():
			shutil.copytree(
				source,
				distribution / directory,
				ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
			)


def _write_scripts_archive(archive_path: Path) -> None:
	scripts_root = ENGINE_ROOT / "scripts"
	with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
		for source_path in sorted(scripts_root.rglob("*.py")):
			relative_path = source_path.relative_to(ENGINE_ROOT.parent)
			archive_name = relative_path.with_suffix(".pyc").as_posix()
			code = compile(
				source_path.read_bytes(),
				str(source_path),
				"exec",
				dont_inherit=True,
				optimize=2,
			)
			archive.writestr(archive_name, marshal.dumps(code))


def build_project(
	project: str | Path = ".",
	output: str | Path | None = None,
) -> Path:
	"""Build a distributable directory containing a compiled game executable."""
	project_root = Path(project).expanduser().resolve()
	main_path = project_root / "main.py"
	config_path = project_root / "config.py"
	if not main_path.is_file():
		raise FileNotFoundError(f"Game entry point does not exist: {main_path}")
	if not config_path.is_file():
		raise FileNotFoundError(f"Game config does not exist: {config_path}")
	if importlib.util.find_spec("nuitka") is None:
		raise RuntimeError(
			"Nuitka is required to build a distributable executable. "
			f"Install it with '{sys.executable} -m pip install nuitka'."
		)
	if importlib.util.find_spec("pygame") is None:
		raise RuntimeError(
			"Pygame must be installed in the build environment so Nuitka can include it. "
			f"Install it with '{sys.executable} -m pip install pygame'."
		)

	output_path = (
		Path(output).expanduser().resolve()
		if output is not None
		else project_root / "dist"
	)
	if output_path == project_root or output_path in project_root.parents:
		raise ValueError("Build output must not overwrite the project or its parent")

	output_path.parent.mkdir(parents=True, exist_ok=True)
	with tempfile.TemporaryDirectory(
		prefix=f".{output_path.name}-", dir=output_path.parent
	) as temporary_directory:
		stage = Path(temporary_directory) / "compile"
		distribution = Path(temporary_directory) / "distribution"
		stage.mkdir()
		distribution.mkdir()
		_copy_project_data(project_root, distribution)

		runtime_package = stage / "raincloud"
		runtime_package.mkdir(exist_ok=True)
		for filename in RUNTIME_FILES:
			shutil.copy2(ENGINE_ROOT / filename, runtime_package / filename)

		_write_scripts_archive(distribution / "scripts.rcs")
		bootstrap = (
			"import sys as _sys\n"
			"from pathlib import Path as _Path\n"
			"from raincloud._archive import load_archive as _load_archive\n"
			"_load_archive(_Path(_sys.argv[0]).resolve().with_name('scripts.rcs'))\n\n"
		)
		(stage / "main.py").write_text(
			bootstrap + main_path.read_text(encoding="utf-8"),
			encoding="utf-8",
		)
		command = [
			sys.executable,
			"-m",
			"nuitka",
			"--app",
			"--include-package=pygame",
			f"--output-dir={stage}",
			f"--output-filename={project_root.name}",
			str(stage / "main.py"),
		]
		environment = os.environ.copy()
		scripts_directory = sysconfig.get_path("scripts")
		environment["PATH"] = os.pathsep.join(
			path
			for path in (scripts_directory, environment.get("PATH", ""))
			if path
		)
		if shutil.which("patchelf", path=environment["PATH"]) is None:
			try:
				patchelf_distribution = metadata.distribution("patchelf")
			except metadata.PackageNotFoundError:
				pass
			else:
				for installed_file in patchelf_distribution.files or ():
					patchelf_path = Path(
						patchelf_distribution.locate_file(installed_file)
					)
					if patchelf_path.name == "patchelf" and patchelf_path.is_file():
						environment["PATH"] = (
							str(patchelf_path.parent)
							+ os.pathsep
							+ environment["PATH"]
						)
						break
		try:
			subprocess.run(command, cwd=stage, check=True, env=environment)
		except subprocess.CalledProcessError as error:
			raise RuntimeError(
				f"Nuitka failed to build the game executable (exit code {error.returncode})."
			) from error

		executable_name = project_root.name + (".exe" if sys.platform == "win32" else "")
		executable_path = stage / executable_name
		if not executable_path.is_file():
			raise RuntimeError(f"Nuitka completed without producing {executable_name}.")
		shutil.move(str(executable_path), distribution / executable_name)

		if output_path.exists():
			if output_path.is_dir():
				shutil.rmtree(output_path)
			else:
				output_path.unlink()
		shutil.move(str(distribution), output_path)

	return output_path