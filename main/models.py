# 実行ディレクトリ: I:\school\kaidoki-desse\main\models.py
from django.contrib.auth.signals import user_logged_in
from django.db import models
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()


# ======================================================
# 共通：正の値バリデータ
# ======================================================
def validate_positive(value):
    if value is not None and value <= 0:
        raise ValidationError("価格は1円以上で入力してください。")


# ======================================================
# カテゴリ（共通・独自兼用）
# ======================================================
class CategoryManager(models.Manager):
    def for_user(self, user):
        """共通カテゴリ＋ユーザー独自カテゴリを返す"""
        return self.filter(Q(is_global=True) | Q(user=user))

    def get_or_create_unclassified(self, user):
        """未分類カテゴリを取得または作成"""
        return self.get_or_create(
            user=user,
            category_name="未分類",
            is_global=False
        )


class Category(models.Model):
    category_name = models.CharField("カテゴリ名", max_length=100, db_index=True)
    is_global = models.BooleanField("共通カテゴリ", default=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, verbose_name="所有ユーザー"
    )
    created_at = models.DateTimeField("作成日時", auto_now_add=True)
    updated_at = models.DateTimeField("更新日時", auto_now=True)

    objects = CategoryManager()

    class Meta:
        db_table = "categories"
        verbose_name = "カテゴリ"
        verbose_name_plural = "カテゴリ"
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["category_name"],
                condition=Q(is_global=True, user__isnull=True),
                name="uniq_global_category_name",
            ),
            models.UniqueConstraint(
                fields=["category_name", "user"],
                condition=Q(is_global=False),
                name="uniq_user_category_name_per_user",
            ),
        ]

    def __str__(self):
        scope = "共通" if self.is_global else f"{self.user.username if self.user else '—'}"
        return f"[{scope}] {self.category_name}"


@receiver(post_save, sender=User)
def create_default_category(sender, instance, created, **kwargs):
    """新規ユーザー登録時、自動で未分類カテゴリを作成"""
    if created:
        Category.objects.get_or_create_unclassified(instance)

# ======================================================
# 論理削除対応マネージャ
# ======================================================


class ProductManager(models.Manager):
    """論理削除対応マネージャ"""

    def get_queryset(self):
        # デフォルトでは削除済みを除外
        return super().get_queryset().filter(is_deleted=False)

    def all_with_deleted(self):
        # 削除済みも含めて取得
        return super().get_queryset()

    def deleted_only(self):
        # 削除済みのみ取得
        return super().get_queryset().filter(is_deleted=True)


# ======================================================
# 商品
# ======================================================
class Product(models.Model):
    PRIORITY_CHOICES = [
        ("普通", "普通"),
        ("高", "高"),
    ]

    FLAG_TYPE_CHOICES = [
        ("buy_price", "買い時価格"),
        ("percent_off", "割引率"),
        ("lowest_price", "最安値"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="products"
    )
    product_name = models.CharField("商品名", max_length=255)
    shop_name = models.CharField(
        "ショップ名", max_length=255, blank=True, null=True)
    product_url = models.URLField("商品URL")
    image_url = models.URLField("商品画像URL", blank=True, null=True)

    # 価格情報
    initial_price = models.DecimalField(
        "登録時価格",
        max_digits=10,
        decimal_places=0,
        null=True,
        blank=True,
        validators=[validate_positive],
    )
    latest_price = models.DecimalField(
        "最新価格",
        max_digits=10,
        decimal_places=0,
        null=True,
        blank=True,
        validators=[validate_positive],
    )
    threshold_price = models.DecimalField(
        "買い時価格",
        max_digits=10,
        decimal_places=0,
        null=True,
        blank=True,
        validators=[validate_positive],
    )

    # 通知条件関連
    flag_type = models.CharField(
        "買い時条件タイプ",
        max_length=20,
        choices=FLAG_TYPE_CHOICES,
        blank=True,
        null=True,
        help_text="買い時価格／割引率／最安値のいずれかを指定",
    )
    flag_value = models.DecimalField(
        "通知条件値",
        max_digits=10,
        decimal_places=0,
        null=True,
        blank=True,
        help_text="買い時価格・割引率・最安値の基準値（flag_typeに応じて解釈）",
    )

    # ステータス
    is_in_stock = models.BooleanField("在庫あり", default=True)
    latest_stock_count = models.IntegerField("最新在庫数", null=True, blank=True)
    flag_reached = models.BooleanField("買い時達成", default=False)
    priority = models.CharField(
        "優先度",
        max_length=10,
        choices=PRIORITY_CHOICES,
        default="普通",
    )

    # カテゴリ（共通＋独自）
    categories = models.ManyToManyField(
        Category, related_name="products", blank=True
    )

    # ✅ 共通カテゴリを追加（管理用マスタ）
    common_categories = models.ManyToManyField(
        "admin_app.CommonCategory",
        related_name="products",
        blank=True,
        verbose_name="共通カテゴリ",
        help_text="共通カテゴリマスタとの紐付け",
    )

    # 作成・更新
    created_at = models.DateTimeField("作成日時", auto_now_add=True)
    updated_at = models.DateTimeField("更新日時", auto_now=True)

    # ✅ 新規追加：論理削除
    is_deleted = models.BooleanField("削除フラグ", default=False)

    # ✅ カスタムマネージャ適用
    objects = ProductManager()

    class Meta:
        verbose_name = "商品"
        verbose_name_plural = "商品"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "product_url"], name="uq_user_product_url"
            )
        ]

    def __str__(self):
        return self.product_name

    # ======================================================
    # 論理削除メソッド
    # ======================================================

    def delete(self, using=None, keep_parents=False):
        """論理削除：物理削除せず is_deleted=True にする"""
        self.is_deleted = True
        self.save(update_fields=["is_deleted"])


# ======================================================
# 価格履歴
# ======================================================
class PriceHistory(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="price_histories")
    price = models.DecimalField(
        "価格", max_digits=10, decimal_places=0, validators=[validate_positive])
    stock_count = models.IntegerField("在庫数", null=True, blank=True)
    checked_at = models.DateTimeField("取得日時")

    class Meta:
        verbose_name = "価格履歴"
        verbose_name_plural = "価格履歴"
        ordering = ["-checked_at"]

    def __str__(self):
        return f"{self.product.product_name} - ¥{self.price}"


# ======================================================
# 通知イベント
# ======================================================
class NotificationEvent(models.Model):
    EVENT_TYPE_CHOICES = [
        ("stock_few", "在庫少通知"),
        ("stock_restore", "在庫復活通知"),
        ("threshold_hit", "買い時価格検知"),
        ("discount_over", "指定割引率下回り"),
        ("lowest_price", "過去最安値更新"),
    ]

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="notification_events")
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notification_events")
    event_type = models.CharField(
        "イベント種別", max_length=50, choices=EVENT_TYPE_CHOICES
    )
    message = models.TextField("通知内容", blank=True)
    occurred_at = models.DateTimeField("発生日時", auto_now_add=True)
    is_read = models.BooleanField("既読", default=False)

    class Meta:
        verbose_name = "通知イベント"
        verbose_name_plural = "通知イベント"
        ordering = ["-occurred_at"]

    def __str__(self):
        return f"{self.user.username}:{self.product.product_name}:{self.event_type}"


# ======================================================
# エラーログ
# ======================================================
class ErrorLog(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True)
    type_name = models.CharField("例外名", max_length=100)
    source = models.CharField("発生箇所", max_length=100)
    message = models.TextField("エラーメッセージ")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "エラーログ"
        verbose_name_plural = "エラーログ"
        ordering = ["-created_at"]

    def __str__(self):
        username = self.user.username if self.user else "匿名"
        return f"[{username}] {self.type_name} @ {self.source}"


# ======================================================
# ユーザー通知設定
# ======================================================

# main/models.py
class UserNotificationSetting(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="notification_setting")

    # メール通知
    enabled = models.BooleanField("メール通知を有効にする", default=True)
    notify_hour = models.PositiveIntegerField("通知時刻（時）", default=9)
    notify_minute = models.PositiveIntegerField("通知時刻（分）", default=0)
    email = models.EmailField("通知メールアドレス", blank=True, null=True)

    # ✅ アプリ内通知設定（シンプル版）
    app_notification_enabled = models.BooleanField(
        "アプリ内通知を有効にする",
        default=True,
        help_text="優先度「高」の商品の買い時通知・在庫通知を受け取ります"
    )

    notification_retention_days = models.PositiveIntegerField(
        "通知の保持期間（日）",
        default=7,
        choices=[
            (7, "7日間"),
            (30, "30日間"),
            (365, "無制限"),
        ],
        help_text="指定日数を過ぎた通知は自動的に既読になります"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "通知設定"
        verbose_name_plural = "通知設定"

    def __str__(self):
        return f"{self.user.username} 通知設定"
# ======================================================
# 管理者　ユーザー画面用
# ======================================================


User = get_user_model()


class UserProfile(models.Model):
    """ユーザーログイン情報（ログイン回数など）"""
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile")
    login_count = models.PositiveIntegerField("ログイン回数", default=0)

    def __str__(self):
        return f"{self.user.username} のプロフィール"

# ✅ ログイン時にカウントアップ


@receiver(user_logged_in)
def increment_login_count(sender, user, request, **kwargs):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.login_count += 1
    profile.save(update_fields=["login_count"])
