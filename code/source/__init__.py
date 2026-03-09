"""Compatibility package that maps historical ``source.*`` imports onto ``zpe_multimodal.*``."""

from __future__ import annotations

import importlib
import importlib.abc
import importlib.util
import sys
from types import ModuleType

import zpe_multimodal as _zpe_multimodal

_ALIAS_PREFIX = "source"
_CANONICAL_PREFIX = "zpe_multimodal"


def _canonical_name(fullname: str) -> str:
    if fullname == _ALIAS_PREFIX:
        return _CANONICAL_PREFIX
    if fullname.startswith(f"{_ALIAS_PREFIX}."):
        suffix = fullname[len(_ALIAS_PREFIX) :]
        return f"{_CANONICAL_PREFIX}{suffix}"
    raise ValueError(f"unsupported compatibility alias: {fullname}")


def _load_canonical(alias_name: str) -> ModuleType:
    module = importlib.import_module(_canonical_name(alias_name))
    sys.modules[alias_name] = module
    return module


class _SourceAliasLoader(importlib.abc.Loader):
    def __init__(self, alias_name: str) -> None:
        self.alias_name = alias_name

    def create_module(self, spec):  # type: ignore[override]
        return _load_canonical(self.alias_name)

    def exec_module(self, module: ModuleType) -> None:  # type: ignore[override]
        sys.modules[self.alias_name] = module


class _SourceAliasFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname: str, path=None, target=None):  # type: ignore[override]
        if not fullname.startswith(f"{_ALIAS_PREFIX}."):
            return None

        canonical_name = _canonical_name(fullname)
        canonical_spec = importlib.util.find_spec(canonical_name)
        if canonical_spec is None:
            return None

        is_package = canonical_spec.submodule_search_locations is not None
        spec = importlib.util.spec_from_loader(
            fullname,
            _SourceAliasLoader(fullname),
            origin=canonical_spec.origin,
            is_package=is_package,
        )
        if spec is None:
            return None
        if is_package and canonical_spec.submodule_search_locations is not None:
            spec.submodule_search_locations = list(canonical_spec.submodule_search_locations)
        return spec


def _install_alias_finder() -> None:
    if any(isinstance(finder, _SourceAliasFinder) for finder in sys.meta_path):
        return
    sys.meta_path.insert(0, _SourceAliasFinder())


_install_alias_finder()

# Mirror the canonical package surface for ``import source`` and
# ``from source import ...`` callers.
__path__ = _zpe_multimodal.__path__
__all__ = list(getattr(_zpe_multimodal, "__all__", ()))
for _name in __all__:
    globals()[_name] = getattr(_zpe_multimodal, _name)
