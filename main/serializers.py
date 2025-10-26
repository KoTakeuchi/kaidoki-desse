from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Category, Product, PriceHistory, NotificationEvent, UserNotificationSetting


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "category_name", "is_global",
                  "user", "created_at", "updated_at"]
        read_only_fields = ["id", "user", "created_at",
                            "updated_at", "is_global"]  # 共通はREAD専用のため基本READONLY


class MyCategoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "category_name"]

    def create(self, validated_data):
        user = self.context["request"].user

        # ✅ 未ログインなら代替ユーザー使用
        if not user.is_authenticated:
            user = get_user_model().objects.filter(username="testuser").first()
            print("⚠️ Serializer側でも 'testuser' を使用中")

        # DB登録
        return Category.objects.create(
            user=user,
            is_global=False,
            **validated_data
        )


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), allow_null=True, required=False
    )
    latest_price = serializers.SerializerMethodField()  # ←追加

    class Meta:
        model = Product
        fields = [
            "id", "product_name", "product_url",
            "regular_price", "threshold_price", "initial_price",
            "category", "latest_price", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_latest_price(self, obj):
        """最新の価格履歴を取得"""
        latest = obj.pricehistory_set.order_by('-checked_at').first()
        return latest.price if latest else None

    def validate_category(self, value):
        # 共通カテゴリ（is_global=True）は誰でも選べる
        # 独自カテゴリ（is_global=False）は所有者のみ選択可
        if value is None:
            return value
        if value.is_global:
            return value
        req_user = self.context["request"].user
        if value.user_id != req_user.id:
            raise serializers.ValidationError("このカテゴリはあなたの所有ではありません。")
        return value


class PriceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceHistory
        fields = ['id', 'product', 'price', 'checked_at']  # ←修正


class NotificationEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationEvent
        fields = ['id', 'product', 'event_type', 'message',
                  'occurred_at', 'sent_flag', 'sent_at']


class UserNotificationSettingSerializer(serializers.ModelSerializer):
    """ユーザー通知設定API用シリアライザ"""

    class Meta:
        model = UserNotificationSetting
        fields = [
            'id',
            'user',
            'enabled',
            'notify_hour',
            'notify_minute',
            'timezone',
            'email',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']


class ProductWriteSerializer(serializers.ModelSerializer):
    """Product 登録・更新用シリアライザ"""

    class Meta:
        model = Product
        fields = [
            'id',
            'product_name',
            'product_url',
            'threshold_price',
            'category',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
