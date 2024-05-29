import os
from typing import ContextManager, Dict, Optional, Sequence, Union

__all__: Sequence[str] = ("Environment",)


EnvValues = Union[str, int, None, bool, float, bytes]
"""The set of valid environment variable values and all values from coercible types.

The `EnvValues` type works with the `Environment` context manger.

Value types of `EnvValues`:  
    - `str`: valid, string environment variable 
    - `None`: represents deleted environment variable from `os.environ`

Coercible types of `EnvValues`. The docstring for the `to_environment_value` function describes the conversion.
"""

Env = Optional[str]
"""Set of value environment variable values: can be directly mapped into `os.environ` context manipulation.

NOTE: For `bytes` conversion, any decode error will result in an exception being raised.
"""


def to_environment_value(value: EnvValues) -> Env:
    """Converts environment variable settings into acceptable values for the `Environment` context manager.

    Coercible types of `EnvValues` are converted according to these rules:
      - `int`: converted to a string by effectively surrounding with quotes: using the builtin `str` function
      - `bool`: convert to an `int` via `True` --> `"1"`, `False` --> `"0"`; then converted to `str` using `int` rules
      - `float`: converted to string by using the builtin `str` function
      - `bytes`: converted to `str` by assuming UTF-8 and decoding

    Raises `ValueError` if a value of a type that is not described above is supplied for `value`.

    NOTE: Raises an exception on UTF-8 decoding failure for `bytes` to `str` conversion.
    """

    if value is None or isinstance(value, str):
        new_val: Optional[str] = value
    elif isinstance(value, bool):
        new_val = str(int(value))
    elif isinstance(value, (int, float)):
        new_val = str(value)
    elif isinstance(value, bytes):
        new_val = value.decode("utf8")
    else:
        raise ValueError(
            f"Environment variable must be either None or a a string (str). "
            f"Limited coercion is available for values of {EnvValues}."
            f"Value is unacceptable {type(value)=}: {value}"
        )

    return new_val


def valid_environment_name(env_var: str) -> None:
    """Raises value error iff supplied with something that is not a valid environment variable name (string)."""
    if not isinstance(env_var, str) or len(env_var.strip()) == 0:
        raise ValueError(f"Need valid environment variable name, not ({type(env_var)}) '{env_var}'")


class Environment(ContextManager):
    """Temporary override environment variables.

    Use as a context manager for overriding arbitrary environment variables. Previous enviornment variable values
    before entering the context are restored on upon exit. EnvValues are restored regardless of normal or exceptional
    execution of code within the context.

    NOTE: This context manager directly modifies `os.environ`, the standard library's environment variable mapping.

    The common use case of `Environment` is to set a few well known variables. For example:
     >>> with Environment(USER='someone', HOME="/Users/someone"):
     >>> # do something that relies on these values, $USER and $HOME
     >>>     ...
     >>> # USER and HOME are reset

    Environment variables are passed by name as keyword arguments. For programantic use of `Environment` context
    creation, pass dictionaries by key-value with the `**` operator. For example:
    >>> overrides = {"USER": "different", "HOME": "/Users/someone", "SHELL": "/bin/zsh"}
    >>> with Environment(**overrides):
    >>> # context has new values as specified in overrides
    >>>   ...

    Any environment variable set to a value of `None` will be deleted within the context. As in:
    Similarily, any variable that did not exist in the environment before the context, but was set to a
    non-`None` value during the context will be deleted from the environment upon exit.

    Note that an `Envionment` instance is stateless itself. It can be reused to conditionally or repeatedly reset
    environment vairables via `os.environ` mutation. For example:
    >>> env_predconditions = Environment(**overrides)
    >>> do_work_dependent_env: callable = ...
    >>> for hip_hip in range(3):
    >>>   if hip_hip % 2 == 0:
    >>>     with env_predconditions:
    >>>       do_work_dependent_env()
    >>>   else:
    >>>     print("You are wonderful and beautiful! :)")

    """

    def __init__(self, **env_vars: EnvValues) -> None:
        """Initializes the context manager with new environment variable settings.

        All environment variables must be a string (`str`), an `int` (`int`), or `None`.

        There is support to automatically convert a limited set of other types into the allowable
        set of environment variable values. The `to_environment_value` function, used here,
        provides this conversion from the wider set, defined as `EnvValues`, to the set of
        allowable values, `Env`.

        Any other value for an environment variable will result in a `ValueError` being raised during
        initialization.
        """
        # record values of `os.environ` before and after the managed context
        # populated in `__enter__` and cleared in `__exit__`
        self.__prior_env_var_setting: Dict[str, Optional[str]] = dict()

        # the
        # we store the user's set of desired temporary values for Environment variables
        # we also validate these settings to a minimum bar of correctness
        self.__new_env_var_settings: Dict[str, Optional[str]] = {
            env_var: _check_env_var_setting(env_var, value) for env_var, value in env_vars.items()
        }

    def __enter__(self) -> "Environment":
        """Records current state of environment variables (`os.environ`) and sets all overrides.

        NOTE: Mutates the standard library's `environ` in the `os` package.
              State pre-call is restored via the `__exit__` method.
        """
        # get the existing values for all of the to-be-set env vars before setting them
        for env, val in self.__new_env_var_settings.items():
            # track prior value and set new for Environment variable
            prior: Optional[str] = os.environ.get(env)
            # note that we're using None to indicate that the env var should be unset on __exit__
            self.__prior_env_var_setting[env] = prior
            if val is not None:
                # we're setting a new value for the environment variable
                os.environ[env] = val
            elif env in os.environ:
                # otherwise, if env=None, then we want to remove this variable from the environment
                del os.environ[env]
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Restores the previous values of all overridden environment variables.

        NOTE: Values captured in a call to `__enter__` are restored into
              `os.environ` when calling this method.
        """
        # restore all env vars
        for env, prior in self.__prior_env_var_setting.items():
            # If there _was_ a prior value, we'll always set it here. This is the same if
            # we were setting it to some other string or if we wanted the env var
            # temporarily gone (env=None in the __init__).
            if prior is not None:
                # restore previous Environment variable value
                os.environ[env] = prior
            else:
                # If there was no prior value for the env var, then we need to determine
                # if we had set it to something new in the context. Or, if the env var
                # didn't exist in the first place.
                if env in os.environ:
                    # If there's a current env value, then it must be the one that we set
                    # in __enter__. Therefore, we want to remove it here to restore the
                    # previous env var state (in which env was never set).
                    del os.environ[env]
                # If the env var isn't currently in the Environment variables state,
                # then we had requested it temporarily unset in the context without
                # the caller realizing that env was never set beforehand.
                # Thus, this "reset" action for this case is equivalent to a no-op.
        # forget about previous context setting
        # could be used for another __enter__ --> __exit__ cycle, if desired
        self.__prior_env_var_setting.clear()

    def set(self) -> None:
        """Alias for :func:`__enter__`."""
        self.__enter__()

    def unset(self) -> None:
        """Alias for :func:`__exit__`."""
        self.__exit__(None, None, None)  # type: ignore


def _check_env_var_setting(name: str, value: EnvValues) -> Env:
    valid_environment_name(name)
    return to_environment_value(value)
