# 実行ディレクトリ: I:\school\kaidoki-desse\tools

from PIL import Image

# 入力・出力パス
input_path = r"I:\school\kaidoki-desse\main\static\images\no_image.png"
output_path = r"I:\school\kaidoki-desse\main\static\images\no_image.png"

# 画像を開く
img = Image.open(input_path).convert("RGB")

# 正方形にリサイズ（アスペクト比保持で余白白埋め）
size = (400, 400)
bg = Image.new("RGB", size, (255, 255, 255))
img.thumbnail(size, Image.Resampling.LANCZOS)

# 中央寄せで貼り付け
x = (size[0] - img.width) // 2
y = (size[1] - img.height) // 2
bg.paste(img, (x, y))

# 保存
bg.save(output_path, "PNG")
print(f"✅ リサイズ完了: {output_path}")
