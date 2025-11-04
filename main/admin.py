# 実行ディレクトリ: I:\school\kaidoki-desse\main\admin.py
from django.contrib import admin
from .models import (
    Category,
    Product,
    PriceHistory,
    NotificationLog,
    NotificationEvent,
    ErrorLog,
    UserNotificationSetting,
    NotificationSetting,
    Notification,
)

# =========================================================
# 📁 カテゴリ管理
# =========================================================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "category_name", "is_global", "user", "created_at")
    list_filter = ("is_global",)
    search_fields = ("category_name", "user__username")
    ordering = ("-created_at",)


# =========================================================
# 🛒 商品管理
# =========================================================
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """複数カテゴリ対応版 Product 管理画面"""

    list_display = (
        "id",
        "product_name",
        "user",
        "get_categories",
        "flag_type",
        "flag_value",
        "flag_reached",
        "is_in_stock",
        "restock_notify_enabled",
        "created_at",
    )
    list_filter = ("flag_type", "flag_reached", "is_in_stock", "categories")
    search_fields = ("product_name", "shop_name", "user__username")
    ordering = ("-created_at",)
    filter_horizontal = ("categories",)

    def get_categories(self, obj):
        """カテゴリをカンマ区切りで表示"""
        return ", ".join([c.category_name for c in obj.categories.all()])
    get_categories.short_description = "カテゴリ"


# =========================================================
# 💰 価格履歴管理
# =========================================================
@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "price", "stock_count", "checked_at")
    list_filter = ("checked_at",)
    search_fields = ("product__product_name",)
    ordering = ("-checked_at",)


# =========================================================
# 🔔 通知関連モデル群
# =========================================================
@admin.register(NotificationEvent)
class NotificationEventAdmin(admin.ModelAdmin):
    """通知イベント（在庫変動・買い時ヒット等）"""
    list_display = (
        "id",
        "user",
        "product",
        "event_type",
        "message",
        "occurred_at",
        "sent_flag",
        "sent_at",
    )
    list_filter = ("event_type", "sent_flag")
    search_fields = ("user__username", "product__product_name", "message")
    ordering = ("-occurred_at",)


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    """通知メール送信ログ"""
    list_display = ("id", "user", "product", "message", "notified_at")
    search_fields = ("user__username", "product__product_name", "message")
    ordering = ("-notified_at",)
    list_per_page = 30


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """旧式通知（アプリ内通知）"""
    list_display = ("id", "user", "product", "type", "message", "created_at", "is_read")
    list_filter = ("type", "is_read")
    search_fields = ("user__username", "product__product_name", "message")
    ordering = ("-created_at",)


# =========================================================
# ⚙️ 通知設定・エラーログ管理
# =========================================================
@admin.register(UserNotificationSetting)
class UserNotificationSettingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "enabled",
        "email",
        "notify_hour",
        "notify_minute",
        "app_notify_frequency",
        "stock_low_threshold",
        "updated_at",
    )
    list_filter = ("enabled", "app_notify_frequency")
    search_fields = ("user__username", "email")
    ordering = ("-updated_at",)


@admin.register(NotificationSetting)
class NotificationSettingAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "product", "threshold_price")
    search_fields = ("user__username", "product__product_name")
    ordering = ("user",)


@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "type_name", "source", "message", "created_at")
    list_filter = ("type_name", "created_at")
    search_fields = ("type_name", "source", "message", "user__username")
    ordering = ("-created_at",)
