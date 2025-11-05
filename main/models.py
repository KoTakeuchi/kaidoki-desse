from admin_app.models import CommonCategory  # ← 追加
from django.db import models
from django.db.models.signals import pre_save, post_save
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver


# ========================================
# 共通：正の値バリデータ
# ========================================


def validate_positive(value):
    """価格系フィールドで0以下の値を禁止"""
    if value is not None and value <= 0:
        raise ValidationError("価格は1円以上で入力してください。")


# ==========================================================
# カスタムマネージャ（共通＋ユーザーカテゴリ管理）
# ==========================================================
class CategoryManager(models.Manager):
    def for_user(self, user):
        """共通カテゴリ＋ユーザー専用カテゴリを取得"""
        return self.filter(Q(is_global=True) | Q(user=user))

    def get_or_create_unclassified(self, user):
        """未分類カテゴリを取得または作成"""
        return self.get_or_create(
            user=user,
            category_name="未分類",
            is_global=False
        )


# ==========================================================
# カテゴリテーブル（クラスベースリファクタ版）
# ==========================================================
class Category(models.Model):
    category_name = models.CharField("カテゴリ名", max_length=100, db_index=True)
    is_global = models.BooleanField(default=False, verbose_name="共通カテゴリ")
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="所有ユーザー",
    )
    created_at = models.DateTimeField("作成日時", auto_now_add=True)
    updated_at = models.DateTimeField("更新日時", auto_now=True)

    # ✅ カスタムマネージャ登録
    objects = CategoryManager()

    class Meta:
        db_table = "categories"
        verbose_name = "カテゴリ"
        verbose_name_plural = "カテゴリ"
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
        ordering = ["id"]

    def __str__(self):
        scope = "共通" if self.is_global else f"{self.user.username if self.user else '—'}"
        return f"[{scope}] {self.category_name}"

    # ======================================================
    # カテゴリ操作系メソッド
    # ======================================================
    def assign_to_unclassified(self):
        """
        このカテゴリに紐づく商品を「未分類」に移動する。
        削除時の安全処理で使用。
        """
        from main.models import Product  # 循環参照防止のため遅延インポート
        unclassified, _ = Category.objects.get_or_create_unclassified(
            self.user)
        Product.objects.filter(category=self).update(category=unclassified)


# ==========================================================
# ユーザー作成時に未分類カテゴリを自動生成
# ==========================================================
@receiver(post_save, sender=User)
def create_default_category(sender, instance, created, **kwargs):
    """新規ユーザー登録時、自動で未分類カテゴリを生成"""
    if created:
        Category.objects.get_or_create_unclassified(instance)

# ========================================
# 商品テーブル（修正版・共通カテゴリ対応）
# ========================================


class Product(models.Model):
    PRIORITY_CHOICES = [
        ("普通", "普通"),
        ("高", "高"),
    ]

    FLAG_CHOICES = [
        ("buy_price", "買い時価格で通知"),
        ("percent_off", "割引率で通知"),
        ("lowest_price", "最安値で通知"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="ユーザー"
    )

    # ✅ 共通カテゴリ（1つのみ選択可能）
    common_category = models.ForeignKey(
        CommonCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        verbose_name="共通カテゴリ",
    )

    # ✅ カテゴリを複数選択可能に（独自カテゴリ）
    categories = models.ManyToManyField(
        Category,
        blank=True,
        related_name="products",
        verbose_name="カテゴリ（複数選択可）",
    )

    product_name = models.CharField("商品名", max_length=100)
    product_url = models.URLField("商品URL", max_length=255, unique=True)
    shop_name = models.CharField(
        "ショップ名", max_length=255, blank=True, null=True)

    # ✅ 商品画像URL（任意）
    image_url = models.URLField(
        "商品画像URL", max_length=255, null=True, blank=True, default=""
    )

    # --- 価格関連 ---
    regular_price = models.DecimalField(
        "定価", max_digits=10, decimal_places=0, null=True, blank=True, validators=[validate_positive]
    )
    initial_price = models.DecimalField(
        "登録時価格", max_digits=10, decimal_places=0, null=True, blank=True, validators=[validate_positive]
    )
    threshold_price = models.DecimalField(
        "買い時価格",
        max_digits=10,
        decimal_places=0,
        null=True,
        blank=True,
        help_text="この金額以下になったら通知",
        validators=[validate_positive],
    )

    priority = models.CharField(
        "優先度", max_length=2, choices=PRIORITY_CHOICES, default="普通")

    # --- 通知条件フラグ ---
    flag_type = models.CharField(
        "通知条件タイプ",
        max_length=20,
        choices=FLAG_CHOICES,
        default="buy_price",
        help_text="どの条件で通知するかを指定（買い時価格・割引率・最安値）",
    )
    flag_value = models.FloatField(
        "フラグ値",
        null=True,
        blank=True,
        help_text="通知条件となる金額または％（例：5000円以下、20％以上など）",
    )
    flag_reached = models.BooleanField("フラグ達成状態", default=False)

    # --- 在庫関連 ---
    is_in_stock = models.BooleanField(
        "在庫あり",
        default=True,
        help_text="APIから取得した在庫情報。Falseなら一覧でグレーアウト表示",
    )
    latest_stock_count = models.IntegerField(
        "最新在庫数",
        null=True,
        blank=True,
        help_text="最新の在庫数量（数量不明時はNULL）",
    )
    stock_low_threshold = models.PositiveIntegerField(
        default=5,
        verbose_name="在庫少通知閾値（商品別）",
        help_text="この数量以下になったら在庫少通知を発行",
    )
    restock_notify_enabled = models.BooleanField(
        "在庫復活通知を有効にする",
        default=False,
        help_text="在庫が復活した際に通知を受け取る",
    )
    restock_last_checked = models.DateTimeField(
        "最終在庫確認日時",
        null=True,
        blank=True,
        help_text="在庫情報を最後に確認した日時（バッチ用）",
    )

    created_at = models.DateTimeField("作成日時", auto_now_add=True)
    updated_at = models.DateTimeField("更新日時", auto_now=True)

    class Meta:
        db_table = "products"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "product_url"], name="uq_user_producturl")
        ]
        verbose_name = "商品"
        verbose_name_plural = "商品"

    def __str__(self):
        return self.product_name

    # =========================================================
    # ✅ 在庫状態変化を検知して NotificationEvent を登録
    # =========================================================
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        prev_in_stock = None

        if not is_new:
            try:
                prev_in_stock = Product.objects.get(pk=self.pk).is_in_stock
            except Product.DoesNotExist:
                pass

        super().save(*args, **kwargs)


@receiver(pre_save, sender=Product)
def detect_restock(sender, instance, **kwargs):
    """
    ✅ 在庫復活検知（在庫なし → あり）
    在庫が復活したタイミングで NotificationEvent を生成
    """
    if not instance.pk:
        return  # 新規登録時はスキップ

    try:
        old = Product.objects.get(pk=instance.pk)
        # 在庫が「なし → あり」に変わった場合のみ検知
        if old.is_in_stock is False and instance.is_in_stock is True:
            if instance.restock_notify_enabled:
                # 循環参照防止のため遅延インポート
                from main.models import NotificationEvent
                from django.utils import timezone

                NotificationEvent.objects.create(
                    user=instance.user,
                    product=instance,
                    event_type=NotificationEvent.EventType.RESTOCK,
                    message=f"『{instance.product_name}』が在庫復活しました！",
                    occurred_at=timezone.now(),
                    sent_flag=False
                )
    except Product.DoesNotExist:
        pass
# ========================================
# 価格履歴テーブル（数量対応）
# ========================================


class PriceHistory(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, verbose_name="商品"
    )
    price = models.DecimalField(
        "価格", max_digits=10, decimal_places=0, validators=[validate_positive]
    )
    stock_count = models.IntegerField(
        "在庫数",
        null=True,
        blank=True,
        help_text="取得時点の在庫数（数量不明時はNULL）",
    )
    checked_at = models.DateTimeField("取得日時", auto_now_add=True)

    class Meta:
        ordering = ["-checked_at"]
        db_table = "price_histories"
        verbose_name = "価格・在庫履歴"
        verbose_name_plural = "価格・在庫履歴"

    def __str__(self):
        stock_display = "不明" if self.stock_count is None else f"{self.stock_count}個"
        return f"{self.product.product_name} - ¥{self.price}（在庫:{stock_display}）[{self.checked_at:%Y-%m-%d}]"

# ========================================
# 通知ログ・設定・イベント・エラー類
# ========================================


class NotificationLog(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    notified_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notification_logs"
        ordering = ["-notified_at"]
        verbose_name = "通知ログ"
        verbose_name_plural = "通知ログ一覧"

    def __str__(self):
        return f"{self.user.username} への通知: {self.product.product_name}"


class NotificationEvent(models.Model):
    class EventType(models.TextChoices):
        THRESHOLD_HIT = "threshold_hit", "買い時価格ヒット"
        LOWEST_PRICE = "lowest_price", "過去最安値を更新"
        DISCOUNT_OVER = "discount_over", "割引率指定以上"
        STOCK_LOW = "stock_low", "在庫少通知"
        RESTOCK = "restock", "在庫復活通知"  # ✅ 追加

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="notification_events"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notification_events"
    )
    event_type = models.CharField(max_length=64, choices=EventType.choices)
    message = models.TextField(blank=True, default="")
    occurred_at = models.DateTimeField(auto_now_add=True)
    sent_flag = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "notification_events"
        indexes = [
            models.Index(fields=["user", "product",
                         "event_type", "occurred_at"])
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "product", "event_type", "occurred_at"],
                name="uniq_event_same_second",
            )
        ]
        verbose_name = "通知イベント"
        verbose_name_plural = "通知イベント一覧"

    def __str__(self):
        return f"{self.user.username}:{self.product.product_name}:{self.get_event_type_display()}"


# ========================================
# ✅ 修正版：ErrorLog（NULL許可＋フィールド整理）
# ========================================
class ErrorLog(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    type_name = models.CharField(max_length=100)
    source = models.CharField(max_length=100)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "error_logs"
        verbose_name = "エラーログ"
        verbose_name_plural = "エラーログ"

    def __str__(self):
        username = self.user.username if self.user else "匿名ユーザー"
        return f"[{username}] {self.type_name} @ {self.source}"


# ========================================
# 通知設定（ユーザー単位）
# ========================================
class UserNotificationSetting(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, verbose_name="ユーザー"
    )
    enabled = models.BooleanField(default=True, verbose_name="メール通知を有効にする")
    notify_hour = models.PositiveIntegerField(
        default=9, verbose_name="メール通知時刻（時）")
    notify_minute = models.PositiveIntegerField(
        default=0, verbose_name="メール通知時刻（分）")
    timezone = models.CharField(
        max_length=50, default="Asia/Tokyo", verbose_name="タイムゾーン")
    email = models.EmailField(blank=True, null=True, verbose_name="通知メールアドレス")

    APP_NOTIFY_FREQUENCY_CHOICES = [
        ("frequent", "多め（都度通知）"),
        ("daily", "少なめ（1日1回）"),
    ]
    app_notify_frequency = models.CharField(
        max_length=10,
        choices=APP_NOTIFY_FREQUENCY_CHOICES,
        default="frequent",
        verbose_name="アプリ内通知頻度",
    )
    app_notify_hour = models.PositiveIntegerField(
        default=9, verbose_name="アプリ通知時刻（時）")
    app_notify_minute = models.PositiveIntegerField(
        default=0, verbose_name="アプリ通知時刻（分）")
    stock_low_threshold = models.PositiveIntegerField(
        default=5, verbose_name="在庫少通知閾値")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_notification_settings"
        verbose_name = "ユーザー通知設定"
        verbose_name_plural = "ユーザー通知設定"

    def __str__(self):
        mail_status = "有効" if self.enabled else "無効"
        return f"{self.user.username}：メール通知{mail_status}"


# ========================================
# 買い時価格設定
# ========================================
class NotificationSetting(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    threshold_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="買い時価格"
    )

    class Meta:
        db_table = "notification_settings"

    def __str__(self):
        return f"{self.user.username} - {self.product.product_name} ({self.threshold_price})"


# ========================================
# 通知履歴
# ========================================
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    type = models.CharField(
        max_length=50,
        choices=[
            ("price_drop", "価格通知"),
            ("restock", "再入荷通知"),
            ("stock_low", "在庫少通知"),
        ],
        default="price_drop",
    )
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    class Meta:
        db_table = "notifications"

    def __str__(self):
        return f"{self.user.username} - {self.message[:20]}"
