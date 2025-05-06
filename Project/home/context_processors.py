"""
This module contains a utility function to generate the base URL for the application.

The `base_url` function takes an HTTP request and constructs the base URL by combining
the scheme (e.g., 'http' or 'https') and the host (e.g., 'example.com') of the request.
This base URL is then returned with an added `/proxy/8000/` path for routing purposes.

Function:
    base_url(request): Returns a dictionary containing the base URL for the application
                        with a proxy path.

Arguments:
    request (HttpRequest): The HTTP request object containing the scheme and host information.

Returns:
    dict: A dictionary with a single key 'base_url' containing the complete base URL string.
"""


def base_url(request):
    """
    Generates the base URL for the application, including the scheme, host, and proxy path.

    Args:
        request (HttpRequest): The HTTP request object used to extract the scheme and host.

    Returns:
        dict: A dictionary with the 'base_url' key, containing the constructed base URL string.
    """

    return {"base_url": f"{request.scheme}://{request.get_host()}/proxy/8000/"}
