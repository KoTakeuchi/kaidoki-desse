from django.contrib.auth.models import User
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class CommonCategory(models.Model):
    """共通カテゴリ（全ユーザー共通で管理されるカテゴリ）"""
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
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="最終更新者",
        related_name="updated_categories"
    )

    def __str__(self):
        return self.category_name

    class Meta:
        verbose_name = "共通カテゴリ"
        verbose_name_plural = "共通カテゴリ"
        ordering = ["id"]


class ErrorLog(models.Model):
    """管理用エラーログ（対応ステータス付き）"""
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="ユーザー",
        related_name="admin_error_logs",  # ← 追加！
    )
    source = models.CharField(max_length=100, verbose_name="発生箇所")
    type_name = models.CharField(max_length=100, verbose_name="エラー種類")
    message = models.TextField(verbose_name="内容")
    created_at = models.DateTimeField(auto_now_add=True)

    STATUS_CHOICES = [
        ("unresolved", "未対応"),
        ("in_progress", "対応中"),
        ("resolved", "対応済み"),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="unresolved",
        verbose_name="対応ステータス"
    )
    handled_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="handled_admin_errors",
        verbose_name="対応者",
    )
    note = models.TextField(blank=True, null=True, verbose_name="対応メモ")

    def __str__(self):
        return f"[{self.type_name}] {self.source}"

    class Meta:
        verbose_name = "管理用エラーログ"
        verbose_name_plural = "管理用エラーログ"
        ordering = ["-created_at"]

# I:\school\kaidoki-desse\admin_app\models.py


class NotificationLog(models.Model):
    METHOD_CHOICES = [
        ('email', 'メール'),
        ('app', 'アプリ'),
    ]

    TYPE_CHOICES = [
        ('mail_buy_timing', '買い時お知らせ'),
        ('mail_stock', '在庫お知らせ'),
        ('threshold_hit', '買い時価格'),
        ('discount_over', '割引率'),
        ('lowest_price', '最安値'),
        ('stock_few', '在庫少'),
        ('stock_restore', '在庫復活'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(
        'main.Product', on_delete=models.CASCADE, null=True, blank=True)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    message = models.TextField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    occurred_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.get_method_display()}] {self.get_type_display()} ({self.user.username})"
