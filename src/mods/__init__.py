import importlib
import sys
from pathlib import Path

__all__ = []

base_dir = Path(__file__).parent

for file in base_dir.iterdir():

    if file.name == "__init__.py":
        continue

    if file.suffix == ".py":

        module_name = file.stem

        globals()[module_name] = importlib.import_module(
            f".{module_name}",
            package=__name__
        )

        __all__.append(module_name)

    elif file.suffix == ".rcm":

        if str(file) not in sys.path:
            sys.path.insert(0, str(file))

        module_name = file.stem

        globals()[module_name] = importlib.import_module(f"{module_name}.main")

        __all__.append(module_name)

