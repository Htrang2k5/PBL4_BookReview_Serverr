import importlib
import pkgutil
import sys
import warnings
from types import ModuleType

__all__ = []


def auto_import_submodules(
    package: ModuleType | None = None,
    expose_in_globals: bool = True,
    quiet: bool = True,
) -> dict[str, ModuleType]:
    if package is None:
        package = sys.modules[__name__]

    # Not a package (no __path__), nothing to import
    if not hasattr(package, '__path__'):
        return {}

    imported: dict[str, ModuleType] = {}

    for _finder, full_name, _is_pkg in pkgutil.walk_packages(
        package.__path__, prefix=package.__name__ + '.'
    ):
        try:
            mod = importlib.import_module(full_name)
        except Exception as exc:
            if not quiet:
                warnings.warn(
                    f'Failed to import {full_name}: {exc}', stacklevel=2
                )

            continue

        imported[full_name] = mod

        if expose_in_globals:
            short_name = full_name.rsplit('.', 1)[-1]
            if short_name not in globals():
                globals()[short_name] = mod
            if short_name not in __all__:
                __all__.append(short_name)

    return imported


auto_import_submodules()
