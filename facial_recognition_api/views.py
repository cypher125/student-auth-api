from django.shortcuts import render

def home(request):
    """
    Render the home page template.
    This view doesn't require authentication and serves as the landing page for the API.
    """
    return render(request, 'home.html') 