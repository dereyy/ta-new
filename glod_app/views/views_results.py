from django.shortcuts import render

# Create your views here.

def results_index(request):
    return render(request, 'glod_app/results_index.html')
