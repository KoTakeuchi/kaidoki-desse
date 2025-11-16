# --- START(1/2): main/forms.py ---
from django.contrib.auth.models import User
from .models import Product, Category
from django.contrib.auth.forms import PasswordChangeForm
from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from main.models import Product, Category, UserNotificationSetting  # ✅ Profile削除
from django.contrib.auth.forms import PasswordChangeForm
User = get_user_model()


# --- START: main/forms.py ---
# ======================================================
# 商品登録・編集フォーム
# ======================================================
class ProductForm(forms.ModelForm):
    """商品登録・編集フォーム（カテゴリ最大2件）"""

    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple(
            attrs={"class": "category-checkbox"}
        ),
        label="カテゴリ（最大2件まで選択可）",
    )

    flag_type = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
        label="通知条件",
    )

    class Meta:
        model = Product
        fields = [
            "product_name",
            "shop_name",
            "product_url",
            "initial_price",
            "threshold_price",
            "priority",
            "categories",
            "flag_type",
            "flag_value",
        ]
        widgets = {
            "product_name": forms.TextInput(
                attrs={"class": "form-control", "readonly": "readonly"}
            ),
            "shop_name": forms.TextInput(
                attrs={"class": "form-control", "readonly": "readonly"}
            ),
            "product_url": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "楽天市場の商品URL",
                }
            ),
            "initial_price": forms.NumberInput(
                attrs={"class": "form-control",
                       "readonly": "readonly", "min": "1"}
            ),
            "threshold_price": forms.NumberInput(
                attrs={"class": "form-control", "min": "1"}
            ),
            "priority": forms.Select(
                choices=[("高", "高"), ("普通", "普通")],
                attrs={"class": "form-select"},
            ),
            "flag_value": forms.NumberInput(
                attrs={"class": "form-control", "min": "0"}
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # --- カテゴリ選択肢設定 ---
        if self.user and self.user.is_authenticated:
            self.fields["categories"].queryset = Category.objects.filter(
                Q(is_global=True, user__isnull=True)
                | Q(user=self.user, is_global=False)
            ).order_by("id")
        else:
            self.fields["categories"].queryset = Category.objects.filter(
                is_global=True)

        # --- 編集時カテゴリ初期値 ---
        if self.instance and self.instance.pk:
            self.initial["categories"] = self.instance.categories.values_list(
                "id", flat=True)

            # ✅ 編集画面時は商品名・ショップ名を編集可
            self.fields["product_name"].widget.attrs.pop("readonly", None)
            self.fields["shop_name"].widget.attrs.pop("readonly", None)

            # ✅ 編集時は product_url を必須から除外（変更不要なため）
            self.fields["product_url"].required = False

            # flag_type は固定表示
            self.fields["flag_type"].widget = forms.HiddenInput()
        else:
            # ✅ 新規登録時は編集不可（API入力用）
            self.fields["product_name"].widget.attrs["readonly"] = "readonly"
            self.fields["shop_name"].widget.attrs["readonly"] = "readonly"

        # --- flag_type に応じた flag_value のプレースホルダを設定 ---
        if self.instance.flag_type == "buy_price":
            self.fields["flag_value"].widget.attrs.update(
                {"placeholder": "例：15000（円）"})
        elif self.instance.flag_type == "percent_off":
            self.fields["flag_value"].widget.attrs.update(
                {"placeholder": "例：10（％）"})

    def clean_product_url(self):
        """楽天URL＋重複防止"""
        url = self.cleaned_data.get("product_url", "")

        # ✅ 編集時（既存インスタンスあり）でURL未入力ならスキップ
        if not url and self.instance and self.instance.pk:
            return self.instance.product_url

        if not url.startswith("https://item.rakuten.co.jp/"):
            raise ValidationError("楽天市場の商品URLを入力してください。")

        if self.user:
            qs = Product.objects.filter(user=self.user, product_url=url)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError("この商品URLはすでに登録されています。")
        return url

    def clean_categories(self):
        """カテゴリは最大2件まで"""
        cats = self.cleaned_data.get("categories")
        if cats and len(cats) > 2:
            raise ValidationError("カテゴリは最大2件まで選択できます。")
        return cats

    def clean_flag_type(self):
        """通知条件の選択必須チェック（編集時は既存値を維持）"""
        flag_type = self.cleaned_data.get("flag_type")

        if not flag_type and self.instance and self.instance.pk:
            return self.instance.flag_type

        if not flag_type or flag_type == "None":
            raise ValidationError("通知条件を選択してください。")

        valid_choices = ["buy_price", "percent_off", "lowest_price"]
        if flag_type not in valid_choices:
            raise ValidationError("通知条件を選択してください。")

        return flag_type

    def clean(self):
        """通知条件と価格の整合チェック"""
        cleaned_data = super().clean()
        flag_type = cleaned_data.get("flag_type")
        initial_price = cleaned_data.get("initial_price")
        threshold_price = cleaned_data.get("threshold_price")
        flag_value = cleaned_data.get("flag_value")

        if flag_type == "buy_price":
            if threshold_price and initial_price and threshold_price > initial_price:
                self.add_error("threshold_price", "登録時価格より低い金額を入力してください。")

        if flag_type == "percent_off" and flag_value is not None:
            if flag_value > 100:
                self.add_error("flag_value", "割引率は100%以下で入力してください。")

        return cleaned_data
# --- END: main/forms.py ---


# ======================================================
# 買い時価格フォーム
# ======================================================
class ThresholdPriceForm(forms.ModelForm):
    """商品詳細ページで買い時価格を更新"""

    class Meta:
        model = Product
        fields = ["threshold_price"]
        widgets = {
            "threshold_price": forms.NumberInput(
                attrs={
                    "class": "form-control form-control-sm text-end",
                    "placeholder": "買い時価格（円）",
                    "min": 1,
                }
            ),
        }


# main/forms.py（追加）


class UserProfileForm(forms.ModelForm):
    """ユーザー情報編集フォーム"""

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name"]
        labels = {
            "username": "ユーザー名",
            "email": "メールアドレス",
            "first_name": "名",
            "last_name": "姓",
        }
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
        }

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("このメールアドレスは既に使用されています。")
        return email

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("このユーザー名は既に使用されています。")
        return username
# ======================================================
# ユーザー通知設定フォーム
# ======================================================
# main/forms.py


class UserNotificationSettingForm(forms.ModelForm):
    """通知設定フォーム（メール通知＋アプリ内通知）"""

    HOUR_CHOICES = [(h, f"{h:02d}時") for h in range(24)]
    MINUTE_CHOICES = [(m, f"{m:02d}分") for m in range(0, 60, 5)]

    notify_hour = forms.ChoiceField(
        choices=HOUR_CHOICES,
        label="時",
        widget=forms.Select(attrs={"class": "form-select"})
    )
    notify_minute = forms.ChoiceField(
        choices=MINUTE_CHOICES,
        label="分",
        widget=forms.Select(attrs={"class": "form-select"})
    )

    class Meta:
        model = UserNotificationSetting
        fields = [
            "enabled",
            "notify_hour",
            "notify_minute",
            "email",
            "app_notification_enabled",      # ✅ アプリ内通知ON/OFF
            "notification_retention_days",   # ✅ 保持期間
        ]
        labels = {
            "enabled": "メール通知を有効にする",
            "email": "通知メールアドレス",
            "app_notification_enabled": "アプリ内通知を有効にする",
            "notification_retention_days": "通知の保持期間",
        }
        widgets = {
            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "readonly": "readonly",
            }),
            "app_notification_enabled": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
            "notification_retention_days": forms.Select(attrs={
                "class": "form-select"
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ✅ メールアドレスをユーザーのメールアドレスで初期化
        if self.instance and self.instance.user:
            self.fields["email"].initial = self.instance.user.email

# ======================================================
# ユーザー登録フォーム
# ======================================================


class CustomUserCreationForm(UserCreationForm):
    """サインアップ用フォーム（日本語化）"""

    email = forms.EmailField(
        label="メールアドレス",
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control"}),
        help_text="通知やパスワード再設定に使用されます。",
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
        labels = {
            "username": "ユーザー名",
            "email": "メールアドレス",
            "password1": "パスワード",
            "password2": "パスワード（確認用）",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ["username", "email", "password1", "password2"]:
            self.fields[name].widget.attrs.update({"class": "form-control"})
            self.fields[name].help_text = None

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("このメールアドレスは既に登録されています。")
        return email


# ======================================================
# パスワード再設定フォーム
# ======================================================
class CustomPasswordResetForm(PasswordResetForm):
    """未登録メールアドレスならエラーを出す"""

    email = forms.EmailField(
        label="メールアドレス",
        max_length=254,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "example@example.com",
            }
        ),
        error_messages={"required": "メールアドレスを入力してください。"},
    )

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip()
        if not email:
            raise ValidationError("メールアドレスを入力してください。")
        if not User.objects.filter(email__iexact=email, is_active=True).exists():
            raise ValidationError("指定のメールアドレスは登録されていません。")
        return email
# --- END(2/2): main/forms.py ---
