from django.shortcuts import render

# Create your views here.

def dashboard_index(request):
    return render(request, 'glod_app/dashboard_index.html')
