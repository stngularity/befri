"""The extensions loader

Perhaps it could have been simpler, but then again, this whole bot is just an
experiment

:copyright: (c) 2026-present stngularity
:license: MIT, see LICENSE for more details."""

import os
import importlib
from datetime import datetime, timedelta
from dataclasses import dataclass
from types import ModuleType
from typing import TYPE_CHECKING, Any, Callable, Coroutine, Final, Sequence

import discord
from discord.ext import commands
from discord.app_commands import locale_str

from utils import from_root
from .logger import Logger

if TYPE_CHECKING:
    from .client import Befri

__all__ = ("Extension", "ExtensionLoader")

MISSING: Any = discord.utils.MISSING


@dataclass
class CommandsGroup:
    """Date class for commands groups."""

    id: str
    module: ModuleType
    commands: dict[str, ModuleType]

    def get(self, name: str) -> Any | None:
        """`Optional`[`Any`]: Returns the attribute with the specified :param:`name`
        if it exists in this group, otherwise `None`"""
        try:
            return getattr(self.module, name)
        except AttributeError:
            return None

@dataclass
class Extension:
    """Date class of the bot's extension (functionality category)"""

    id: str
    module: ModuleType
    disabled: bool
    loaded: bool
    groups: dict[str, CommandsGroup]
    commands: dict[str, ModuleType]
    listeners: dict[str, ModuleType]
    tasks: dict[str, ModuleType]

    def get(self, name: str) -> Any | None:
        """`Optional`[`Any`]: Returns the attribute with the specified :param:`name`
        if it exists in this extension, otherwise `None`"""
        try:
            return getattr(self.module, name)
        except AttributeError:
            return None

@dataclass
class Task:
    """The date class of the scheduled task"""

    id: str
    callback: Callable[["Befri"], Coroutine[None, None, Any]]
    time_every: timedelta | None = None
    time_at: datetime | list[datetime] | None = None
    count: int | None = None

    _last_run: datetime | None = None

    def can_run(self, time: datetime) -> bool:
        """`bool`: Checks whether the task can be started at the specified time"""
        if self.count is not None and self.count <= 0:
            return False
        
        if self.count is not None:
            self.count -= 1

        if isinstance(self.time_at, datetime) and time == self.time_at:
            return True
        
        if isinstance(self.time_at, list) and time in self.time_at:
            return True
        
        if self.time_every is not None and self._last_run is None:
            self._last_run = time
            return True
        
        if self.time_every is None or self._last_run is None:
            return False
        
        if (self._last_run + self.time_every) <= time:
            self._last_run = time
            return True
        
        return False

class ExtensionLoader:
    """Bot extension loader"""

    EXTENSIONS_FOLDER: Final[str] = from_root("src", "extensions")

    def __init__(self, client: commands.Bot, logger: Logger) -> None:
        self._client = client
        self._logger = logger
        self._registred: dict[str, Extension] = dict()
        self._tasks: dict[str, Task] = dict()

    @property
    def extensions(self) -> dict[str, Extension]:
        """A dictionary of extensions, where the key is the extension ID and the value is its object"""
        return self._registred
    
    @property
    def tasks(self) -> dict[str, Task]:
        """A dictionary of scheduled tasks, where the key is the task ID and the value is the task object"""
        return self._tasks

    def _get_attribute(self, module: ModuleType, name: str) -> Any | None:
        try:
            return getattr(module, name)
        except AttributeError:
            return None

    def _get_modules(
        self,
        path: str,
        module_path: str,
        field: str,
        *,
        before_name: str = "",
        exclude: str | None = None
    ) -> dict[str, ModuleType]:
        output = dict()
        for name in os.listdir(path):
            file = os.path.join(path, name)
            if not (os.path.isfile(file) and file.endswith(".py")) or\
                (exclude is not None and file.startswith(exclude)):
                continue

            module = importlib.import_module(module_path + f".{name[:-3]}")
            func_name = self._get_attribute(module, field) or name[:-3]
            if (before_name + func_name) not in module.__dict__:
                continue

            output[func_name] = module
        
        return output

    def _scan_for(self, id: str, *, for_: str, before_name: str = "") -> dict[str, ModuleType]:
        path = os.path.join(self.EXTENSIONS_FOLDER, id, for_)
        if not os.path.exists(path):
            return dict()

        return self._get_modules(path, f"extensions.{id}.{for_}", f"{for_[:-1]}_name", before_name=before_name)

    def _scan_for_groups(self, id: str) -> dict[str, CommandsGroup]:
        groups = dict()
        path = os.path.join(self.EXTENSIONS_FOLDER, id, "commands")
        if not os.path.exists(path):
            return groups
        
        for name in os.listdir(path):
            folder = os.path.join(path, name)
            if not (os.path.isdir(folder) and os.path.exists(os.path.join(folder, f"{name}.py"))):
                continue

            module = importlib.import_module(f"extensions.{id}.commands.{name}.{name}")
            commands = self._get_modules(folder, f"extensions.{id}.commands.{name}", "command_name", exclude=name)
            groups[name] = CommandsGroup(id=name, module=module, commands=commands)
        
        return groups

    def scan_for_extensions(self) -> None:
        """Scans the bot's extensions folder and registers everything"""
        for folder in os.listdir(self.EXTENSIONS_FOLDER):
            extension_root = os.path.join(self.EXTENSIONS_FOLDER, folder)
            file = os.path.join(extension_root, f"{folder}.py")
            if not os.path.exists(file) or not os.path.isfile(file):
                continue

            module = importlib.import_module(f"extensions.{folder}.{folder}")
            self._registred[folder] = Extension(
                id=folder,
                module=module,
                disabled=os.path.exists(os.path.join(extension_root, ".disabled")),
                loaded=False,
                groups=self._scan_for_groups(folder),
                commands=self._scan_for(folder, for_="commands"),
                listeners=self._scan_for(folder, for_="listeners", before_name="on_"),
                tasks=self._scan_for(folder, for_="tasks")
            )

    def load(
        self,
        extension: Extension,
        *,
        localizer: Callable[[commands.HybridCommand, str], str | Sequence[str] | None] | None = None
    ) -> None:
        """Loads specified :param:`extension`"""
        if extension.loaded:
            raise ValueError(f"The specified extension ({extension.id}) has already been loaded")
        
        for id, group in extension.groups.items():
            name = group.get("name")
            if name is None:
                raise Exception(f"`{id}` isn't a group") 

            if not isinstance(name, (str, locale_str)):
                self._logger.error(f"The field `name` in the group `{id}` has an incorrect data type")
                continue

            description = group.get("description")
            if description is not None and not isinstance(description, (str, locale_str)):
                self._logger.error(f"The field `description` in the group `{id}` has an incorrect data type")
                continue

            group_obj = commands.HybridGroup(name=name, description=description or MISSING)

            func = self._get_attribute(group.module, f"{id}_fallback")
            if func is not None and isinstance(func, commands.HybridCommand):
                group_obj = commands.HybridGroup(func, name=name, description=description or MISSING,
                                                 fallback=func._locale_name or func.name)
            
            for c_name, command in group.commands.items():
                func = self._get_attribute(command, c_name)
                if func is None:
                    raise Exception(f"`{command}` isn't a command") 

                group_obj.add_command(func)
                self._logger.debug(f"Loaded `{name}` command from group `{id}` (ext {extension.id})")
            
            self._client.add_command(group_obj)
            self._logger.debug(f"Loaded `{id}` group from extension `{extension.id}`")

        for name, command in extension.commands.items():
            func = self._get_attribute(command, name)
            if func is None or not isinstance(func, commands.HybridCommand):
                raise Exception(f"`{command}` isn't a command") 

            if not (localizer is None or (aliases := localizer(func, "aliases")) is None):
                func.aliases = list(func.aliases)
                func.aliases.extend(aliases)
            
            self._client.add_command(func)
            self._logger.debug(f"Loaded `{name}` command from extension `{extension.id}`")
        
        for name, listener in extension.listeners.items():
            func = self._get_attribute(listener, f"on_{name}")
            if func is None:
                raise Exception(f"`{listener}` isn't a listener") 
            
            self._client.add_listener(func)
            self._logger.debug(f"Loaded `{name}` listener from extension `{extension.id}`")
        
        for name, task in extension.tasks.items():
            func = self._get_attribute(task, name)
            if func is None:
                raise Exception(f"`{task}` isn't a task") 
            
            time_every = self._get_attribute(task, "every")
            if time_every is not None and not isinstance(time_every, timedelta):
                time_every = None
                self._logger.warning(f"The field `every` in the task `{name}` has an incorrect data type")
            
            time_at = self._get_attribute(task, "at")
            if not isinstance(time_at, (datetime, list)):
                time_at = None
                self._logger.warning(f"The field `at` in the task `{name}` has an incorrect data type")
            
            run_count = self._get_attribute(task, "count")
            if not isinstance(run_count, int):
                run_count = None
                self._logger.warning(f"The field `count` in the task `{name}` has an incorrect data type")

            self._tasks[name] = Task(
                id=name,
                callback=func,
                time_every=time_every,
                time_at=time_at,
                count=run_count
            )
        
        extension.loaded = True

    def load_all(
        self,
        *,
        localizer: Callable[[commands.HybridCommand, str], str | Sequence[str] | None] | None = None
    ) -> None:
        """Loads all registered extensions except those that are disabled"""
        for extension in self._registred.values():
            if extension.disabled:
                continue

            self.load(extension, localizer=localizer)

    def unload(self, id: str) -> None:
        """Unloads an extension with the specified :param:`id`"""
        extension = self._registred.get(id)
        if extension is None:
            raise Exception(f"There is no extension with the `{id}` identifier")
        
        for command_name in extension.commands.keys():
            self._client.tree.remove_command(command_name)

        for name, listener in extension.listeners.items():
            func = self._get_attribute(listener, name)
            self._client.remove_listener(func)  # type: ignore
        
        for name in extension.tasks.keys():
            self._tasks.pop(name)
    
    def remove_task(self, id: str) -> None:
        """Deletes the task with the specified :param:`id`"""
        self._tasks.pop(id)
