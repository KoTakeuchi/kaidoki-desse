# --- START(1/2): main/forms.py ---
from django.contrib.auth.forms import PasswordChangeForm
from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from main.models import Product, Category, UserNotificationSetting  # ✅ Profile削除
from django.contrib.auth.forms import PasswordChangeForm
User = get_user_model()


# ======================================================
# 商品登録・編集フォーム
# ======================================================
class ProductForm(forms.ModelForm):
    """商品登録・編集フォーム（カテゴリ最大2件）"""

    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple(
            attrs={"class": "category-checkbox"}),
        label="カテゴリ（最大2件まで選択可）",
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
        ]
        widgets = {
            "product_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "商品名"}),
            "shop_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "ショップ名"}),
            "product_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "楽天市場の商品URL"}),
            "initial_price": forms.NumberInput(attrs={"class": "form-control", "readonly": "readonly", "min": "1"}),
            "threshold_price": forms.NumberInput(attrs={"class": "form-control", "placeholder": "買い時価格（円）", "min": "1"}),
            "priority": forms.Select(
                choices=[("高", "高"), ("普通", "普通")],
                attrs={"class": "form-select"},
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # --- カテゴリ選択肢設定 ---
        if self.user and self.user.is_authenticated:
            self.fields["categories"].queryset = Category.objects.filter(
                Q(is_global=True, user__isnull=True) | Q(
                    user=self.user, is_global=False)
            ).order_by("id")
        else:
            self.fields["categories"].queryset = Category.objects.filter(
                is_global=True)

        # --- 編集時カテゴリ初期値 ---
        if self.instance and self.instance.pk:
            self.initial["categories"] = self.instance.categories.values_list(
                "id", flat=True)

    def clean_product_url(self):
        """楽天URL＋重複防止"""
        url = self.cleaned_data.get("product_url", "")
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

# ======================================================
# ユーザー情報編集フォーム
# ======================================================


class ProfileForm(forms.ModelForm):
    """ユーザー情報編集フォーム（ユーザー名・メール・パスワード）"""

    current_password = forms.CharField(
        label="現在のパスワード",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "autocomplete": "current-password"}),
        required=True,
    )
    new_password1 = forms.CharField(
        label="新しいパスワード",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "autocomplete": "new-password"}),
        required=False,
        help_text="変更しない場合は空欄のままでOKです。",
    )
    new_password2 = forms.CharField(
        label="新しいパスワード（確認用）",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "autocomplete": "new-password"}),
        required=False,
    )

    class Meta:
        model = User
        fields = ["username", "email"]
        labels = {"username": "ユーザー名", "email": "メールアドレス"}
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.get("instance")
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        password = self.cleaned_data.get("current_password")
        if not self.user.check_password(password):
            raise forms.ValidationError("現在のパスワードが正しくありません。")
        return password

    def clean(self):
        cleaned = super().clean()
        pw1 = cleaned.get("new_password1")
        pw2 = cleaned.get("new_password2")

        # どちらか入力されていれば一致チェック
        if pw1 or pw2:
            if pw1 != pw2:
                raise forms.ValidationError("新しいパスワードが一致しません。")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        pw1 = self.cleaned_data.get("new_password1")

        if pw1:
            user.set_password(pw1)

        if commit:
            user.save()
        return user

# ======================================================
# ユーザー通知設定フォーム
# ======================================================


class UserNotificationSettingForm(forms.ModelForm):
    """通知設定フォーム（メール通知設定のみ）"""

    HOUR_CHOICES = [(h, f"{h:02d}時") for h in range(24)]
    MINUTE_CHOICES = [(m, f"{m:02d}分") for m in range(0, 60, 5)]

    notify_hour = forms.ChoiceField(choices=HOUR_CHOICES, label="メール通知時刻（時）")
    notify_minute = forms.ChoiceField(
        choices=MINUTE_CHOICES, label="メール通知時刻（分）")

    class Meta:
        model = UserNotificationSetting
        fields = ["enabled", "notify_hour", "notify_minute", "email"]
        labels = {"enabled": "メール通知を有効にする"}
        widgets = {"email": forms.EmailInput(attrs={"class": "form-control"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update(
                    {"class": "form-select" if isinstance(
                        field.widget, forms.Select) else "form-control"}
                )


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
