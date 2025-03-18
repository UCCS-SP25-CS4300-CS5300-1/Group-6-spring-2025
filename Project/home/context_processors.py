def base_url(request):
    return {
        'base_url': f"{request.scheme}://{request.get_host()}/proxy/8000/"
    }