# 実行ディレクトリ: I:\school\kaidoki-desse\main\admin.py
from django.contrib import admin
from .models import (
    Category,
    Product,
    PriceHistory,
    NotificationEvent,
    UserNotificationSetting,
    ErrorLog,
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
        "priority",
        "threshold_price",
        "is_in_stock",
        "flag_reached",
        "created_at",
    )
    list_filter = ("is_in_stock", "flag_reached", "priority")
    search_fields = ("product_name", "shop_name", "user__username")
    ordering = ("-created_at",)
    filter_horizontal = ("categories",)

    def get_categories(self, obj):
        """カテゴリをカンマ区切りで表示"""
        return ", ".join(c.category_name for c in obj.categories.all())
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
# 🔔 通知イベント管理
# =========================================================
@admin.register(NotificationEvent)
class NotificationEventAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "product", "event_type",
                    "message", "occurred_at", "is_read")
    list_filter = ("event_type", "is_read")
    search_fields = ("user__username", "product__product_name", "message")
    ordering = ("-occurred_at",)


# =========================================================
# ⚙️ 通知設定管理
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
        "updated_at",
    )
    list_filter = ("enabled",)
    search_fields = ("user__username", "email")
    ordering = ("-updated_at",)


# =========================================================
# 🧩 エラーログ管理
# =========================================================
@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "type_name",
                    "source", "message", "created_at")
    list_filter = ("type_name",)
    search_fields = ("type_name", "source", "message", "user__username")
    ordering = ("-created_at",)
