# stdlib
from importlib.abc import Loader
import glob
import importlib.util
from os.path import basename, dirname, isfile, join
from typing import Any, Dict, Generator, List, Type

# adjutorium absolute
import adjutorium.logger as log
from adjutorium.plugins.prediction.classifiers.base import (  # noqa: F401,E402
    ClassifierPlugin,
)

plugins = glob.glob(join(dirname(__file__), "plugin*.py"))


class Classifiers:
    def __init__(self) -> None:
        self._plugins: Dict[str, Type] = {}

        self._load_default_plugins()

    def _load_default_plugins(self) -> None:

        for plugin in plugins:
            name = basename(plugin)
            spec = importlib.util.spec_from_file_location(name, plugin)
            if not isinstance(spec.loader, Loader):
                raise RuntimeError("Invalid classification plugin")

            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            try:
                cls = mod.plugin  # type: ignore
            except BaseException as e:
                log.critical(f"module {name} load failed {e}")
                continue

            log.debug(f"Loaded plugin {cls.type()} - {cls.name()}")
            self.add(cls.name(), cls)

    def list(self) -> List[str]:
        return list(self._plugins.keys())

    def types(self) -> List[Type]:
        return list(self._plugins.values())

    def add(self, name: str, cls: Type) -> "Classifiers":
        if name in self._plugins:
            raise ValueError(f"Plugin {name} already exists.")

        if not issubclass(cls, ClassifierPlugin):
            raise ValueError(
                f"Plugin {name} must derive the ClassifierPlugin interface."
            )

        self._plugins[name] = cls

        return self

    def get(self, name: str, *args: Any, **kwargs: Any) -> ClassifierPlugin:
        if name not in self._plugins:
            raise ValueError(f"Plugin {name} doesn't exist.")

        return self._plugins[name](*args, **kwargs)

    def get_type(self, name: str) -> Type:
        if name not in self._plugins:
            raise ValueError(f"Plugin {name} doesn't exist.")

        return self._plugins[name]

    def __iter__(self) -> Generator:
        for x in self._plugins:
            yield x

    def __len__(self) -> int:
        return len(self.list())

    def __getitem__(self, key: str) -> ClassifierPlugin:
        return self.get(key)

    def reload(self) -> "Classifiers":
        self._plugins = {}
        self._load_default_plugins()
        return self


__all__ = [basename(f)[:-3] for f in plugins if isfile(f)] + [
    "Classifiers",
    "ClassifierPlugin",
]
