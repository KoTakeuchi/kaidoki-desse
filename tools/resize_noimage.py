# 実行ディレクトリ: I:\school\kaidoki-desse
from PIL import Image
import os

# 入力パスと出力パス
input_path = r"I:\school\kaidoki-desse\main\static\images\no_image.png"
output_path = input_path  # 上書き保存

# 画像を開く
img = Image.open(input_path).convert("RGB")

# 400×400にリサイズ（縦横比維持しつつ白背景で中央寄せ）
target_size = (400, 400)
resized = Image.new("RGB", target_size, (255, 255, 255))  # 白背景
img.thumbnail(target_size, Image.Resampling.LANCZOS)

# 中央に配置
x = (target_size[0] - img.width) // 2
y = (target_size[1] - img.height) // 2
resized.paste(img, (x, y))

# 上書き保存
resized.save(output_path, "PNG")
print(f"✅ no_image.png を 400x400 にリサイズして上書き保存しました: {output_path}")
