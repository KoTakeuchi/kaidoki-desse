# 実行ディレクトリ: I:\school\kaidoki-desse\main\signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Category

User = get_user_model()


@receiver(post_save, sender=User)
def create_default_category(sender, instance, created, **kwargs):
    """
    新規ユーザー作成時に「未分類」カテゴリを自動生成
    """
    if created:
        Category.objects.get_or_create(
            user=instance,
            category_name="未分類",
            defaults={"is_global": False}
        )
