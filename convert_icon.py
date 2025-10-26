# 実行ディレクトリ: I:\school\kaidoki-desse
from PIL import Image

# PNG画像を開く
img = Image.open("main/static/images/icon_kaidoki.png")

# 余白がある場合はトリミング（自動で外側を削除）
img = img.crop(img.getbbox())

# 高解像度128x128にリサイズ（1.5倍相当の見え方）
img = img.resize((128, 128), Image.Resampling.LANCZOS)

# ICOに変換
img.save("main/static/images/favicon.ico", format="ICO", sizes=[(128, 128)])

print("✅ favicon.ico を128px高解像度で再生成しました。")
