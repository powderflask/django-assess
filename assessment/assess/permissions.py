from importlib import import_module
from functools import partial
from django.apps import apps
from django.core.exceptions import PermissionDenied

# import Plugin Permissions module
appConfig = apps.get_app_config('assess')
permissions = import_module(appConfig.settings.PERMISSIONS)

def permission_required(permission_fn):
    """
        Constructs a CBV decorator that checks permission_fn(view.request.user, view.kwargs) before calling
          view.dispatch to test if request.user has a given (object) permission.
        Usage:  @permission_required("permission_function_name")  class MyViewClass: ...
    """
    def decorator(view_class):
        _dispatch = view_class.dispatch

        def dispatch(self, request, *args, **kwargs):
            if not permission_fn(request.user, **self.kwargs):
                raise PermissionDenied()
            return _dispatch(self, request, *args, **kwargs)

        view_class.dispatch = dispatch
        return view_class

    return decorator


def get_permissions_context_from_request(request, **kwargs):
    """
        Return a dictionary of permissions functions (partials that can be called with no arguments)
        request.user and kwargs are bound to each function in the context.
    """
    context = {}
    for name in dir(permissions):
        fn = getattr(permissions, name)
        if callable(fn):
            context[name] = partial(fn, request.user, **kwargs)
    return context


def get_permissions_context(view):
    """ Shortcut to return permissions context for a view using view.kwargs """
    return get_permissions_context_from_request(view.request, **view.kwargs)

