from .models import Product, Category
from django import forms
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from django.core.exceptions import ValidationError
from .models import Product, Category, NotificationSetting, UserNotificationSetting

# ------------------------------------------------------------
# 共通：ユーザーモデル取得
# ------------------------------------------------------------
User = get_user_model()


class ProductForm(forms.ModelForm):
    """商品登録・編集フォーム（複数カテゴリ＋楽天URL＋通知フラグ対応）"""

    # ① 商品URL（楽天市場のみ）
    product_url = forms.URLField(
        label="商品URL",
        required=True,
        widget=forms.URLInput(attrs={
            "placeholder": "https://item.rakuten.co.jp/ショップ名/商品コード/",
            "class": "form-control",
            "id": "id_product_url",
        }),
        error_messages={
            "required": "商品URLを入力してください。",
            "invalid": "正しいURLを入力してください。",
        },
    )

    # ② 商品名（必須）
    product_name = forms.CharField(
        label="商品名",
        required=True,
        widget=forms.TextInput(attrs={
            "placeholder": "例）Uネック裏起毛リブカットソー",
        }),
        error_messages={"required": "商品名を入力してください。"},
    )

    # ③ 定価
    regular_price = forms.DecimalField(
        label="定価",
        required=False,
        min_value=1,
        error_messages={
            "min_value": "定価は1円以上で入力してください。",
            "invalid": "定価は数値で入力してください。",
        },
        widget=forms.NumberInput(attrs={"min": "1"}),
    )

    # ④ 登録時価格
    initial_price = forms.DecimalField(
        label="登録時価格",
        required=False,
        min_value=1,
        error_messages={
            "min_value": "登録時価格は1円以上で入力してください。",
            "invalid": "登録時価格は数値で入力してください。",
        },
        widget=forms.NumberInput(attrs={"min": "1"}),
    )

    # ⑤ 買い時価格
    threshold_price = forms.DecimalField(
        label="買い時価格（この金額以下で通知）",
        required=False,
        min_value=1,
        error_messages={
            "min_value": "買い時価格は1円以上で入力してください。",
            "invalid": "買い時価格は数値で入力してください。",
        },
        widget=forms.NumberInput(attrs={"min": "1"}),
    )

    # ⑥ カテゴリ（複数選択）
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.none(),
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
            "categories",
            "regular_price",
            "initial_price",
            "threshold_price",
            "priority",
            "flag_type",
            "flag_value",
        ]
        labels = {
            "flag_type": "通知条件フラグ",
            "flag_value": "通知条件値",
        }
        widgets = {
            "priority": forms.RadioSelect,
            "flag_type": forms.RadioSelect,
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # --- ユーザー固有＋共通カテゴリを対象にする ---
        if user:
            self.fields["categories"].queryset = Category.objects.filter(
                Q(user=user) | Q(is_global=True)
            ).order_by("category_name")
            self.user = user

        # --- Bootstrapクラス適用 ---
        for field in self.fields.values():
            if not isinstance(field.widget, (forms.RadioSelect, forms.CheckboxSelectMultiple)):
                css_class = field.widget.attrs.get("class", "")
                field.widget.attrs["class"] = f"{css_class} form-control".strip()

        # --- 編集時は flag_type を変更不可 ---
        if self.instance and self.instance.pk:
            self.fields["flag_type"].disabled = True

        # --- 商品URL補助文 ---
        self.fields["product_url"].help_text = (
            "楽天市場（https://item.rakuten.co.jp/）の商品URLを貼り付けてください。"
        )

    # ============================================================
    # URLバリデーション（楽天URL＋重複防止）
    # ============================================================
    def clean_product_url(self):
        product_url = self.cleaned_data.get("product_url")

        if not product_url.startswith("https://item.rakuten.co.jp/"):
            raise ValidationError("このURLは楽天市場の商品ページではありません。")

        if not hasattr(self, "user"):
            raise ValidationError("ユーザー情報が取得できません。")

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

        # ✅ 定価・買い時価格の整合性
        if regular_price and threshold_price and threshold_price > regular_price:
            raise ValidationError("買い時価格は定価以下に設定してください。")

        # ✅ フラグ依存制御
        if flag_type == "buy_price":
            if not threshold_price:
                raise ValidationError("『買い時価格』を入力してください。")
            cleaned_data["flag_value"] = threshold_price

        elif flag_type == "percent_off":
            if not regular_price:
                raise ValidationError("『％OFF』通知を選択する場合は定価を入力してください。")
            if flag_value is None:
                raise ValidationError("『％OFF』値を入力してください（5〜95の範囲で5刻み）。")
            if not (5 <= flag_value <= 95 and flag_value % 5 == 0):
                raise ValidationError(
                    "％OFFは5〜95の範囲で5刻み（5,10,15,…,95）で指定してください。")

        elif flag_type == "lowest_price":
            cleaned_data["flag_value"] = None
            cleaned_data["threshold_price"] = None

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
    """サインアップ用フォーム（日本語化＋重複チェック）"""

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
        error_messages = {
            "username": {"unique": "同じユーザー名が既に登録されています。"},
            "email": {"unique": "このメールアドレスは既に登録されています。"},
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


# ============================================================
# パスワード再設定フォーム（未登録アドレスにエラー表示）
# ============================================================
class CustomPasswordResetForm(PasswordResetForm):
    """登録されていないメールアドレスならエラーを出すフォーム"""

    email = forms.EmailField(
        label="メールアドレス",
        max_length=254,
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "example@example.com",
            "autocomplete": "email",
        }),
        error_messages={"required": "メールアドレスを入力してください。"},
    )

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip()
        if not email:
            raise ValidationError("メールアドレスを入力してください。")
        if not User.objects.filter(email__iexact=email, is_active=True).exists():
            raise ValidationError("指定のメールアドレスは登録されていません。")
        return email
