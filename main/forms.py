from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import Product, Category, NotificationSetting, UserNotificationSetting

# ------------------------------------------------------------
# 共通：ユーザーモデル取得
# ------------------------------------------------------------
User = get_user_model()


# ============================================================
# 商品フォーム（登録・編集）
# ============================================================
class ProductForm(forms.ModelForm):
    """商品登録・編集フォーム（複数カテゴリ＋楽天URL＋フラグ仕様対応）"""

    # ✅ 定価
    regular_price = forms.DecimalField(
        label="定価",
        required=False,
        min_value=1,
        error_messages={
            "min_value": "定価は1円以上で入力してください。",
            "invalid": "定価は数値で入力してください。",
        },
        widget=forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
    )

    # ✅ 登録時価格
    initial_price = forms.DecimalField(
        label="登録時価格",
        required=False,
        min_value=1,
        error_messages={
            "min_value": "登録時価格は1円以上で入力してください。",
            "invalid": "登録時価格は数値で入力してください。",
        },
        widget=forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
    )

    # ✅ 買い時価格（この金額以下で通知）
    threshold_price = forms.DecimalField(
        label="買い時価格（この金額以下で通知）",
        required=False,
        min_value=1,
        error_messages={
            "min_value": "買い時価格は1円以上で入力してください。",
            "invalid": "買い時価格は数値で入力してください。",
        },
        widget=forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
    )

    # ✅ カテゴリ（複数選択可能）
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.none(),  # 初期は空、__init__で絞り込み
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="カテゴリ（複数選択可）",
    )

    class Meta:
        model = Product
        fields = [
            "product_name",
            "product_url",
            "shop_name",
            "categories",       # ← category → categories に変更
            "regular_price",
            "initial_price",
            "threshold_price",
            "priority",
            "flag_type",
            "flag_value",
            "image_url",
        ]
        labels = {
            "threshold_price": "買い時価格（この金額以下で通知）",
            "flag_type": "通知条件フラグ",
            "flag_value": "通知条件値",
        }
        widgets = {
            "priority": forms.RadioSelect,
            "flag_type": forms.RadioSelect,
        }

    # ============================================================
    # 初期化処理
    # ============================================================
    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # ✅ ログインユーザーに紐づくカテゴリのみ表示
        if user:
            self.fields["categories"].queryset = Category.objects.filter(
                Q(user=user) | Q(is_global=True)
            ).order_by("category_name")
            self.user = user

        # ✅ Bootstrapスタイル適用
        for field in self.fields.values():
            if not isinstance(field.widget, (forms.RadioSelect, forms.CheckboxSelectMultiple)):
                field.widget.attrs.update({"class": "form-control"})

        # ✅ 既存商品の場合、flag_type を編集不可に
        if self.instance and self.instance.pk:
            if "flag_type" in self.fields:
                self.fields["flag_type"].disabled = True

        # ✅ 商品URLプレースホルダ・説明追加
        self.fields["product_url"].widget.attrs.update({
            "placeholder": "https://item.rakuten.co.jp/カテゴリ名/商品名",
        })
        self.fields["product_url"].help_text = (
            "楽天市場 https://item.rakuten.co.jp/ から登録する商品URLをコピペしてください。"
        )

    # ============================================================
    # URLバリデーション（楽天URLチェック＋重複防止）
    # ============================================================
    def clean_product_url(self):
        product_url = self.cleaned_data.get("product_url")

        # 楽天市場URL形式チェック
        if not product_url.startswith("https://item.rakuten.co.jp/"):
            raise ValidationError("このURLは楽天市場の商品ページではありません。")

        # ユーザー情報確認
        if not hasattr(self, "user"):
            raise ValidationError("ユーザー情報が取得できません。")

        # 重複チェック
        existing = Product.objects.filter(
            user=self.user, product_url=product_url)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)

        if existing.exists():
            raise ValidationError("この商品URLはすでに登録されています。")

        return product_url

    # ============================================================
    # 総合バリデーション（価格関係・フラグ依存）
    # ============================================================
    def clean(self):
        cleaned_data = super().clean()
        regular_price = cleaned_data.get("regular_price")
        threshold_price = cleaned_data.get("threshold_price")
        flag_type = cleaned_data.get("flag_type")
        flag_value = cleaned_data.get("flag_value")

        # ✅ 買い時価格 < 定価チェック
        if regular_price and threshold_price and threshold_price > regular_price:
            raise ValidationError("買い時価格は通常価格以下に設定してください。")

        # ✅ フラグ依存制御
        if flag_type == "buy_price":
            if not threshold_price:
                raise ValidationError("買い時価格を入力してください。")

        elif flag_type == "percent_off":
            if not regular_price:
                raise ValidationError("割引率通知を選択する場合は定価を入力してください。")
            if flag_value is None:
                raise ValidationError("割引率を入力してください（5〜95の範囲で5刻み）。")
            if not (5 <= flag_value <= 95):
                raise ValidationError("割引率は5〜95の範囲で入力してください。")

        return cleaned_data


# ============================================================
# 買い時価格フォーム
# ============================================================
class ThresholdPriceForm(forms.ModelForm):
    threshold_price = forms.IntegerField(
        required=False,
        label="買い時価格（この金額以下で通知）",
        min_value=1,
        error_messages={
            "min_value": "買い時価格は1円以上で入力してください。",
            "invalid": "買い時価格は数値で入力してください。",
        },
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "step": "1",
                "inputmode": "numeric",
                "pattern": r"[0-9]*",
                "placeholder": "例：1500",
                "min": "1",
            }
        ),
    )

    class Meta:
        model = Product
        fields = ["threshold_price"]


# ============================================================
# ユーザープロフィール編集フォーム
# ============================================================
class ProfileForm(forms.ModelForm):
    """ユーザー名・メールアドレス編集用"""

    class Meta:
        model = User
        fields = ["username", "email"]
        labels = {
            "username": "ユーザー名",
            "email": "メールアドレス",
        }
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }


# ============================================================
# ユーザー通知設定フォーム
# ============================================================
class UserNotificationSettingForm(forms.ModelForm):
    """メール・アプリ通知時刻などの設定"""

    HOUR_CHOICES = [(h, f"{h:02d}時") for h in range(0, 24)]
    MINUTE_CHOICES = [(m, f"{m:02d}分") for m in range(0, 60, 5)]  # 5分刻み

    notify_hour = forms.ChoiceField(choices=HOUR_CHOICES, label="メール通知時刻（時）")
    notify_minute = forms.ChoiceField(
        choices=MINUTE_CHOICES, label="メール通知時刻（分）")
    email = forms.EmailField(label="通知先メールアドレス（確認用）", required=False)

    APP_NOTIFY_CHOICES = [
        ("frequent", "多め（都度通知）"),
        ("daily", "少なめ（1日1回）"),
    ]
    app_notify_frequency = forms.ChoiceField(
        choices=APP_NOTIFY_CHOICES,
        label="アプリ内通知頻度",
        help_text="多め：検知のたびに通知／少なめ：指定時刻にまとめて通知",
    )
    app_notify_hour = forms.ChoiceField(
        choices=HOUR_CHOICES, label="アプリ通知時刻（時）")
    app_notify_minute = forms.ChoiceField(
        choices=MINUTE_CHOICES, label="アプリ通知時刻（分）")

    class Meta:
        model = UserNotificationSetting
        fields = [
            "enabled",
            "notify_hour",
            "notify_minute",
            "email",
            "app_notify_frequency",
            "app_notify_hour",
            "app_notify_minute",
        ]
        labels = {
            "enabled": "メール通知を有効にする",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # メールアドレスは参照専用
        self.fields["email"].widget.attrs["readonly"] = True
        # Bootstrap整形
        for field in self.fields.values():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update(
                    {"class": "form-select" if isinstance(
                        field.widget, forms.Select) else "form-control"}
                )


# ============================================================
# ユーザー登録フォーム（新規登録）
# ============================================================
class CustomUserCreationForm(UserCreationForm):
    """サインアップ用フォーム（メール必須）"""

    email = forms.EmailField(
        label="メールアドレス",
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control"}),
        help_text="通知やパスワード再設定に使用されます。",
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Bootstrap統一
        for name in ["password1", "password2"]:
            self.fields[name].widget.attrs.update({"class": "form-control"})
            self.fields[name].help_text = None

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user
