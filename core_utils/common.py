from importlib import import_module
from typing import _GenericAlias, Any, Tuple, Optional, Type, _type_repr, TypeVar  # type: ignore


def type_name(t: type, keep_main: bool = True) -> str:
    """Complete name, module & specific type name, for the given type.
    Does not supply the module in the returned complete name for built-in types.

    When possible, also adds generic type arguments (w/ their at-runtime values)
    in the returned full type name.
    """
    # TODO: Replace function with `typing._type_repr` ???
    mod = t.__module__
    if mod == "builtins":
        return t.__name__

    if str(t).startswith("typing.Union"):
        try:
            args = t.__args__  # type: ignore
            if len(args) == 2 and args[1] == type(None):  # noqa: E721
                # an Optional type is equivalent to Union[T, None]
                return f"typing.Optional[{type_name(args[0])}]"
        except Exception:
            pass
        return str(t)

    if issubclass(type(t), _GenericAlias):
        return str(t)

    if isinstance(t, TypeVar):
        return str(t)

    full_name = f"{mod}.{t.__name__}"
    try:
        # generic parameters ?
        args = tuple(map(type_name, t.__args__))  # type: ignore
        a = ", ".join(args)
        complete_type_name = f"{full_name}[{a}]"
    except Exception:
        complete_type_name = full_name

    if not keep_main:
        complete_type_name = complete_type_name.replace("__main__.", "")
    return complete_type_name


def import_by_name(full_name: str, validate: bool = True) -> Any:
    """Dynamically load a Python value by it's fully-qualified name.

    Supports loading a module, class, function, or any other type of Python
    object by its complete name. To load builtins (e.g. `"dict"`), the
    module should be left blank.

    E.g. For a class `Foo` in the module `bar.baz.qux`, supplying
         `"bar.baz.qux.Foo"` will yield a reference to the Python class.
         Notably, with such a reference, we could construct a class instance
         by calling it's `__init__` method. So, the following would be valid:
         ```
            foo_init = import_by_name("bar.baz.qux.Foo")
            foo_instance = foo_init()
         ```

    :raises ValueError If :param:`validate` and :param:`full_name` is empty.
    :raises ModuleNotFoundError If :param:`full_name` is not a valid complete name.
    """
    if validate:
        full_name = _strip_non_empty(full_name, "Complete path name")

    try:
        try:
            module_name, value_name = split_module_value(full_name, validate=False)
            return dynamic_load(module_name, value_name, validate=False)
        except ValueError:
            # no '.' separator
            return import_module(full_name)
    except ModuleNotFoundError as e:
        try:
            return import_by_name(f"builtins.{full_name}")
        except:  # type: ignore
            raise e


def _strip_non_empty(s: str, name_for_error: str) -> str:
    """Trims whitespace from :param:`s`.

    :raises ValueError If :param:`s` is empty after white-space trimming.
    """
    s = s.strip()
    if len(s) == 0:
        raise ValueError(f"{name_for_error} cannot be empty")
    return s


def split_module_value(full_name: str, validate: bool = True) -> Tuple[str, str]:
    """Split a fully-qualified Python value's name into its complete module name and the value name.

    :raises ValueError If :param`validate` and :param:`full_name` is empty.
    :raises ValueError If the supplied value consists only of a module name.
    """
    if validate:
        full_name = _strip_non_empty(full_name, "Complete path name")
    m, v = full_name.rsplit(".", maxsplit=1)
    return m, v


def dynamic_load(
    module_name: str, value_name: Optional[str], validate: bool = True
) -> Any:
    """Dynamically load a Python module, class, function, or object from its module and specific name.

    Loads the module :param:`module_name`. If :param:`value_name` is not None,
    then this function also loads the :param:`value_name` defined in the loaded module.

    :raises ValueError If :param:`validiate`:
                       - and :param:`module_name` is empty
                       - and :param:`value_name` is not `None` and it is empty.
    :raises ImportError If :param:`module_name` is not a valid module.
    :raises AttributeError If :param:`value_name` is not None and it is not present
                           in the :param:`module_name` module.
    """
    if validate:
        module_name = _strip_non_empty(module_name, "Module name")
    module = import_module(module_name)
    if value_name:
        if validate:
            value_name = _strip_non_empty(value_name, "Value name")
        return getattr(module, value_name)
    else:
        return module


def checkable_type(type_value: Type) -> Type:
    """Produces a type that is always suitable for `issubclass` checks.

    If :param:`type_value` is generic, i.e. it is parameterized by other types,
    then an erased version of it is returned. The specific, parameterized types
    are removed and the base type is returned. Otherwise the :param:`type_value`
    is returned as-is.
    """
    if type(type_value) == _GenericAlias:
        maybe_name = getattr(type_value, "_name", None)
        if maybe_name is not None:
            erased_type_name = f"typing.{maybe_name}"
            checking_type_value: Type = import_by_name(erased_type_name)
        else:
            checking_type_value = type_value.__origin__  # type: ignore
    else:
        checking_type_value = type_value
    return checking_type_value
