from flask import Flask

app = Flask(__name__)

# 最大アップロードサイズを設定 (例えば 16MB)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

from flask import Flask, render_template, request
import boto3
import base64
import os
from io import BytesIO
from PIL import Image

app = Flask(__name__)

# AWS S3の設定
S3_BUCKET = 'suiko-ehime-bucket-face-data'

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    # Base64で送信された画像データを取得
    img_data = request.form['file']
    user_name = request.form['name']
    
    # "data:image/png;base64," の部分を除去
    img_data = img_data.split(",")[1]
    
    # Base64デコード
    img_bytes = base64.b64decode(img_data)

    # バイナリデータを画像として処理
    image = Image.open(BytesIO(img_bytes))
    
    # 名前を付けてJPEGファイルとして保存（拡張子をjpegに変更）
    file_name = f"{user_name.replace(' ', '_')}.jpeg"
    file_path = os.path.join('uploads', file_name)

    # 保存するディレクトリがなければ作成
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    
    # JPEG形式で保存
    image.convert('RGB').save(file_path, 'JPEG')

    # S3にアップロード
    s3 = boto3.client('s3')
    s3.upload_file(file_path, S3_BUCKET, file_name)

    # 一時ファイルを削除
    os.remove(file_path)

    return 'File uploaded successfully!'

if __name__ == '__main__':
    app.run(debug=True)
