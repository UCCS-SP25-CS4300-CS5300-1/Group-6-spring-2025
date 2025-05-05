"""
Context processor for injecting the application's base URL into templates.
"""

def base_url(request):
    """
    Returns a dictionary with the base URL for use in templates.

    Args:
        request: The HTTP request object.

    Returns:
        dict: A dictionary with 'base_url' key pointing to the proxy path.
    """
    return {
        'base_url': f"{request.scheme}://{request.get_host()}/proxy/8000/"
    }