from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def flag_setting(request):
    """通知設定ページ（仮）"""
    return render(request, "main/flag_setting.html")
