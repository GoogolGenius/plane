# Copyright 2022-Present GoogleGenius
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
"""Internal utilities for the API wrapper."""

from __future__ import annotations

__all__: tuple[str, ...] = ("with_permission_check",)

from functools import wraps
from typing import Any, Callable, Coroutine, TYPE_CHECKING, TypeVar
from typing_extensions import Concatenate, ParamSpec, TypeAlias

from plane.api.errors import AccessException

if TYPE_CHECKING:
    from plane.http import HTTPAwareEndpoint

    _EndpointP = ParamSpec("_EndpointP")
    _EndpointT = TypeVar("_EndpointT")
    _EndpointF: TypeAlias = Callable[
        Concatenate[HTTPAwareEndpoint, _EndpointP], Coroutine[_EndpointT, Any, Any]
    ]


def has_permissions(required: str, permissions: list[str]) -> bool:
    """Check whether the required permissions match a list of permissions.

    Parameters
    ----------
    required : str
        The required permissions.
    permissions : list[str]
        The list of permissions.

    Returns
    -------
    bool
        Whether the permissions match.
    """
    required_list = required.split(".")

    while required_list:
        if ".".join(required_list) in permissions:
            return True
        required_list.pop()

    return False


def with_permission_check(
    required: str,
) -> Callable[[_EndpointF[_EndpointP, _EndpointT]], _EndpointF[_EndpointP, _EndpointT]]:
    """Decorate an instance method of `plane.http.HTTPAwareEndpoint` to validate the required permissions.

    !!! warning
        This is an internal function and should not be used unless you know what you are doing.

    Parameters
    ----------
    required : str
        The required permissions.

    Returns
    -------
    Callable[[_EndpointF[_EndpointP, _EndpointT]], _EndpointF[_EndpointP, _EndpointT]]
    """

    def decorator(
        function: _EndpointF[_EndpointP, _EndpointT]
    ) -> _EndpointF[_EndpointP, _EndpointT]:
        @wraps(function)
        async def wrapper(
            self: HTTPAwareEndpoint, *args: _EndpointP.args, **kwargs: _EndpointP.kwargs
        ) -> Coroutine[_EndpointT, Any, Any]:
            if self._http.permissions is None:
                raise AssertionError(
                    'Permissions is "None"; were permissions not yet fetched or unexpectedly modified?'
                )

            if not has_permissions(required, self._http.permissions):
                raise AccessException(required)

            return await function(self, *args, **kwargs)

        return wrapper

    return decorator
