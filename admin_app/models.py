from django.db import models


class CommonCategory(models.Model):
    """
    共通カテゴリ（全ユーザー共有）
    管理者画面からCRUD操作可能
    """
    category_name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="カテゴリ名"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="作成日時"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新日時"
    )

    def __str__(self):
        return self.category_name

    class Meta:
        verbose_name = "共通カテゴリ"
        verbose_name_plural = "共通カテゴリ"
        ordering = ['id']
