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


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "category_name", "is_global", "user", "created_at")
    list_filter = ("is_global",)
    search_fields = ("category_name",)
    ordering = ("-created_at",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """複数カテゴリ対応版 Product 管理画面"""

    list_display = (
        "id",
        "product_name",
        "user",
        "get_categories",  # ← category → get_categories に変更
        "flag_type",
        "flag_value",
        "flag_reached",
        "created_at",
    )
    # ← category → categories
    list_filter = ("flag_type", "flag_reached", "categories")
    search_fields = ("product_name", "shop_name")
    ordering = ("-created_at",)
    filter_horizontal = ("categories",)  # ← ManyToManyField用ウィジェット

    def get_categories(self, obj):
        """カテゴリをカンマ区切りで表示"""
        return ", ".join([c.category_name for c in obj.categories.all()])
    get_categories.short_description = "カテゴリ"


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "price", "stock_count", "checked_at")
    list_filter = ("checked_at",)
    search_fields = ("product__product_name",)
    ordering = ("-checked_at",)


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "product", "message", "notified_at")
    search_fields = ("user__username", "product__product_name", "message")
    ordering = ("-notified_at",)


@admin.register(NotificationEvent)
class NotificationEventAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "product", "event_type",
                    "occurred_at", "sent_flag")
    list_filter = ("event_type", "sent_flag")
    search_fields = ("user__username", "product__product_name")
    ordering = ("-occurred_at",)


@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "type_name",
                    "source", "message", "created_at")
    list_filter = ("type_name", "created_at")
    search_fields = ("type_name", "source", "message", "user__username")
    ordering = ("-created_at",)


@admin.register(UserNotificationSetting)
class UserNotificationSettingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "enabled",
        "notify_hour",
        "notify_minute",
        "app_notify_frequency",
    )
    list_filter = ("enabled", "app_notify_frequency")
    search_fields = ("user__username",)
    ordering = ("-updated_at",)


@admin.register(NotificationSetting)
class NotificationSettingAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "product", "threshold_price")
    search_fields = ("user__username", "product__product_name")
    ordering = ("user",)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "product", "type",
                    "message", "created_at", "is_read")
    list_filter = ("type", "is_read")
    search_fields = ("user__username", "product__product_name", "message")
    ordering = ("-created_at",)
