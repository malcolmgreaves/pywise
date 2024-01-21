import os
from typing import Any, ContextManager, Dict, Optional, Sequence

__all__: Sequence[str] = ("Environment",)


class Environment(ContextManager):
    """Context manager for temporarily setting environment variables.

     This context manager sets specific environment variables when in use. When entering a context,
     this class will record the previous values for all of the env vars that it will set. Upon exit,
     this class restores all previous values to the environment variables that it changed during
     the context. Variables that were unset before entering the context with :class:`Environment`
     will be unset when the context is exited.

     **WARNING**: Mutates the `os.environ` environment variable mapping in the :func:`__enter__`
                  and :func:`__exit__` methods. Every `__enter__` **MUST** be followed-up by an `__exit__`.

     The suggested use pattern is to make a new :class:`Environment` for each scope where one
    requires temporarily setting environment variables. This common use case looks like:
     >>> with Environment(ENV_VAR='your-value'):
     >>>     # do something that needs this ENV_VAR set to 'your-value'
     >>>     ...
     >>> # Environment variable "ENV_VAR" is reset to its prior value.
     >>> # If there was not a previously set value for "ENV_VAR", then it is unset now.

     You can also use `environment` to temporarily ensure that an environment variable is not set:
     >>>> with Environment(ENV_VAR=None):
     >>>>   # There is no longer any Environment variable value for "ENV_VAR"
     >>>>   ...
     >>>> # If there was one beforehand, the Environment variable "ENV_VAR" is reset.
     >>>> # Otherwise, it is still unset.

     However, it is possible, however to create one :class:`Environment` instance and re-use to
     temporarily reset the same declared environment variable state. This use case looks like:
     >>>> os.environ['ENV_VAR'] = 'first value'
     >>>> setter = Environment(ENV_VAR='new value')
     >>>> with setter:
     >>>>    # ENV_VAR is now set to 'new value'
     >>>> # ENV_VAR is restored: it is set to 'first value'
     >>>> os.environ['ENV_VAR'] = 'second value'
     >>>> setter.set()
     >>>> # ENV_VAR is now set to 'new value' again
     >>>> setter.unset()
     >>>> # ENV_VAR is now restored: it is set to 'second value'
    """

    def __init__(self, **env_vars) -> None:
        """Initializes the manager with new environemnt variable values to use during the context.

         NOTE: All environment variables must be string (`str`) valued or `None`.
               Simple primitive values -- `float`, `int`, `bytes`, `bool` -- will be coerced into
               a `str` value in the constructor. Any value of another type will result in a
               `ValueError` being raised.

         Note that supplying `None` means that the environment variable will not be present.
         That is, it will be deleted from the mapping `os.environ` during the context.

         This is different than setting the environment variable to the empty string (`""`).
         Using `X=None` means that `"X" in os.environ` will be `False`. Whereas, using `X=""`
         means that `"X" in os.environ` will be `True`.

        The constructor allows for specifying env vars as keyword arguments:
        >>>> Environment(ENV_VAR_1='...', ENV_VAR_2='...', ENV_VAR_K='...')

        It is also possible to supply these via a dictionary:
        >>>> envars: Dict[str, str] = {"ENV_VAR_1": '...', "ENV_VAR_2": '...', "ENV_VAR_K": '...'}
        >>>> Environment(**envars)

        However, if any key i.e. environment variable name is empty, or not a string (`str`), then
        this constructor will raise a `ValueError`.


        ERRORS:
              - Raises :class:`ValueError` if:
                 - the environment variable name is not a non-empty string
                 - the value is not None or a string (or a value that can be automatically coerced
                                                      into a string)

        """
        # used in __enter__ and __exit__: keeps track of prior existing Environment
        # variable settings s.t. they can be reset when the context block is finished
        self.__prior_env_var_setting: Dict[str, Optional[str]] = dict()

        # we store the user's set of desired temporary values for Environment variables
        # we also validate these settings to a minimum bar of correctness
        self.__new_env_var_settings: Dict[str, Optional[str]] = {
            env_var: _check_env_var_setting(env_var, value) for env_var, value in env_vars.items()
        }

    def __enter__(self) -> "Environment":
        """Grabs the current in-environment values and sets the variables to their supplied values.

        The context-entering step. This method grabs all of the current in-environment values for
        all supplied variables. This grabs the exact values inside `os.environ`.

        Then, this method sets each of these variables to the values that were supplied at
        construction time.

        WARNING: Mutates internal state!
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

        Using the values captured in `__enter__`, this context-exiting method will restore
        all overriden environment variables to their previous values. If any environment variable
        that was set during the context did not have a previous value before the managed context,
        then it is unset. As in, it won't appear in `os.environ` once this method finishes.

        NOTE: This method ignores all input arguments.

        WARNING: Mutates internal state!
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


def _check_env_var_setting(env_var: Any, value: Any) -> Optional[str]:
    """Ensures `env_var` is ok to set. Returns acceptable `value`. Raises `ValueError` otherwise."""
    if not isinstance(env_var, str) or len(env_var) == 0:
        raise ValueError(f"Need valid environment variable name, not ({type(env_var)}) '{env_var}'")
    if value is None or isinstance(value, str):
        new_val: Optional[str] = value
    else:
        if isinstance(value, (bytes, int, float, bool)):
            new_val = str(value)
        else:
            raise ValueError(
                f"Environment variable {env_var} must be either None, a string (str), or "
                "a value that can be coerced into a string automatically "
                f"(int, float, bool, bytes). Value is unacceptable {type(value)=}: {value}"
            )

    return new_val
