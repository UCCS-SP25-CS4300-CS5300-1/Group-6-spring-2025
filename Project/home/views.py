from django.shortcuts import render

def index(request):
    print(request.method)
    return render(request, 'index.html')