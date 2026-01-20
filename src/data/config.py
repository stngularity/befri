"""Interface for working with configuration

:copyright: (c) 2026-present stngularity
:license: MIT, see LICENSE for more details."""

from typing import Any, Iterator, Mapping, Optional, Type, TypeVar, Union, overload

from ruamel.yaml import YAML

__all__ = ("YamlMapping", "Configuration")

T = TypeVar('T')


class _JoinTag:
    """A tag to join strings in a list"""

    yaml_tag = u"!join"

    @classmethod
    def from_yaml(cls, constructor, node):
        """From YAML to object"""
        seq = constructor.construct_sequence(node)
        return "".join(str(el) for el in seq)

    @classmethod
    def to_yaml(cls, dumper, data):
        """From object to YAML"""
        return dumper.represent_sequence(cls.yaml_tag, data)

class YamlMapping:
    """The class for YAML mappings
    
    Parameters
    ----------
    data: `Mapping`[`str`, `Any`]
        The original data of the map"""

    def __init__(self, data: Mapping[str, Any]) -> None:
        self._data = dict(data)

    def __repr__(self) -> str:
        return f"<YAML mapping with {len(self._data.keys())} keys>"
    
    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __getattr__(self, name: str) -> Any:
        output = self._data.get(name.lstrip("b_").rstrip("_f"))
        if name.startswith("b_") and not isinstance(output, bool):
            return False
        
        if isinstance(output, dict):
            return YamlMapping(output)
        
        if output is None and not name.endswith("_f"):
            return YamlMapping({})

        return output

    def __iter__(self) -> Iterator:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value

    @overload
    def get(self, key: str, default: T, *, type: Type[T]) -> T:
        """T: Searches the data for the specified key in this map.
        
        Parameters
        ----------
        key: `str`
            The dot-separated key.
        
        type: `Optional`[`Type`[T]]
            The type that the data for the specified :param:`key` should match. If `None` is
            specified, this check is skipped. By default, `None`.
        
        default: `Optional`[T]
            The value to be returned by the function if no data was found for the specified
            :param:`key` or if it does not match the specified :param:`type`. By default,
            `None`.
        
        Returns
        -------
        This function returns the found data or the value of the :param:`default` parameter."""
    
    @overload
    def get(self, key: str, *, type: Type[T]) -> Optional[T]:
        """`Optional`[T]: Searches the data for the specified key in this map.
        
        Parameters
        ----------
        key: `str`
            The dot-separated key.
        
        type: `Optional`[`Type`[T]]
            The type that the data for the specified :param:`key` should match. If `None` is
            specified, this check is skipped. By default, `None`.
        
        Returns
        -------
        This function returns the found data or `None`."""

    @overload
    def get(self, key: str, default: T) -> T:
        """Searches the data for the specified key in this map.
        
        Parameters
        ----------
        key: `str`
            The dot-separated key.
        
        default: `Optional`[T]
            The value to be returned by the function if no data was found for the specified
            :param:`key` or if it does not match the specified :param:`type`. By default,
            `None`.
        
        Returns
        -------
        This function returns the found data or the value of the :param:`default` parameter."""

    @overload
    def get(self, key: str) -> Optional[Union[Any, "YamlMapping"]]:
        """`Optional`[`Union`[`Any`, :class:`YamlMapping`]]: Searches the
        data for the specified key in this map.
        
        Parameters
        ----------
        key: `str`
            The dot-separated key.
        
        Returns
        -------
        This function returns the found data or `None`."""

    def get(
        self,
        key: str,
        default: Optional[T] = None,
        *,
        type: Optional[Type[T]] = None
    ) -> Optional[Union[T, "YamlMapping"]]:
        """`Optional`[`Union`[T, :class:`YamlMapping`]]: Searches the data for
        the specified key in this map.
        
        Parameters
        ----------
        key: `str`
            The dot-separated key.
        
        default: `Optional`[T]
            The value to be returned by the function if no data was found for the specified
            :param:`key` or if it does not match the specified :param:`type`. By default,
            `None`.
        
        type: `Optional`[`Type`[T]]
            The type that the data for the specified :param:`key` should match. If `None` is
            specified, this check is skipped. By default, `None`.
        
        Returns
        -------
        This function returns the found data or the value of the :param:`default` parameter."""
        output = self._data
        for part in key.split("."):
            output = output.get(part)
            if output is None:
                return default

        if (type is not None) and not isinstance(output, type):
            return default

        return YamlMapping(output) if isinstance(output, dict) else output

    def contains(self, *keys: str) -> bool:
        """`bool`: Whether the map contains specified :param:`keys`"""
        return [k in self._data.keys() for k in keys].count(False) == 0

class Configuration(YamlMapping):
    """The class for configurations
    
    Parameters
    ----------
    path: `str`
        The path to the configuration

    data: `Mapping`[`str`, `Any`]
        The original data of the map"""

    yaml = YAML(typ="safe")
    yaml.register_class(_JoinTag)

    def __init__(self, path: str, data: Mapping[str, Any]) -> None:
        super().__init__(data)
        self._path = path

    def reload(self) -> None:
        """Reloads the configuration"""
        with open(self._path, "r", encoding="utf-8") as reader:
            self._data = Configuration.yaml.load(reader.read())

    @classmethod
    def load(cls: Type["Configuration"], path: str) -> "Configuration":
        """:class:`Configuration`: Loads specified configuration
        
        Parameters
        ----------
        path: `str`
            The path to the configuration"""
        self = cls.__new__(cls)
        self._path = path
        with open(path, "r", encoding="utf-8") as reader:
            self._data = Configuration.yaml.load(reader.read())

        return self
