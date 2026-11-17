"""Import Raincloud modules stored as marshalled bytecode in an .rcs archive."""

import importlib.abc
import importlib.util
import marshal
from pathlib import Path
import sys
import zipfile


class _ArchiveImporter(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def __init__(self, archive_path: Path):
        self.archive_path = archive_path
        self.archive = zipfile.ZipFile(archive_path)
        self.modules = set(self.archive.namelist())

    def find_spec(self, fullname, path=None, target=None):
        module_path = fullname.replace(".", "/")
        package_file = f"{module_path}/__init__.pyc"
        module_file = f"{module_path}.pyc"
        if package_file in self.modules:
            spec = importlib.util.spec_from_loader(fullname, self, is_package=True)
            if spec is not None:
                spec.origin = f"{self.archive_path}!/{package_file}"
            return spec
        if module_file in self.modules:
            spec = importlib.util.spec_from_loader(fullname, self)
            if spec is not None:
                spec.origin = f"{self.archive_path}!/{module_file}"
            return spec
        return None

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        module_path = module.__name__.replace(".", "/")
        package_file = f"{module_path}/__init__.pyc"
        module_file = f"{module_path}.pyc"
        archive_name = package_file if package_file in self.modules else module_file
        code = marshal.loads(self.archive.read(archive_name))
        module.__file__ = f"{self.archive_path}!/{archive_name}"
        exec(code, module.__dict__)


def load_archive(archive_path: str | Path) -> None:
    """Register an .rcs archive before importing modules that it contains."""
    resolved_path = Path(archive_path).resolve()
    for importer in sys.meta_path:
        if isinstance(importer, _ArchiveImporter) and importer.archive_path == resolved_path:
            return
    sys.meta_path.insert(0, _ArchiveImporter(resolved_path))