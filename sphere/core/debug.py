from debug_toolbar.middleware import show_toolbar as default_show_toolbar


def show_toolbar(request):
    """Keep developer controls out of the public catalog."""
    return request.user.is_staff and default_show_toolbar(request)
