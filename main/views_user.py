from django.shortcuts import render


def user_edit(request):
    return render(request, 'user/user_edit.html')
