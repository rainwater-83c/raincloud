"""Create a Raincloud game project from the starter template."""

from pathlib import Path
import shutil


TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "init_template"


def initialize_project(destination: str | Path = ".") -> Path:
	"""Copy the starter project into an empty destination directory."""
	target = Path(destination).expanduser().resolve()
	if target.exists() and (not target.is_dir() or any(target.iterdir())):
		raise FileExistsError(f"Project destination is not empty: {target}")

	target.mkdir(parents=True, exist_ok=True)
	shutil.copytree(TEMPLATE_PATH, target, dirs_exist_ok=True)
	return target
