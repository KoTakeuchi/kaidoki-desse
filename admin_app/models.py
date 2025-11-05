from django.db import models
from django.contrib.auth.models import User


class CommonCategory(models.Model):
    category_name = models.CharField(max_length=100, unique=True, verbose_name="カテゴリ名")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="最終更新者"
    )

    def __str__(self):
        return self.category_name

    class Meta:
        verbose_name = "共通カテゴリ"
        verbose_name_plural = "共通カテゴリ"
        ordering = ["id"]
