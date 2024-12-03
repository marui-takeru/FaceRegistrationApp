from flask import Flask, render_template, request
import mysql.connector
import boto3
import base64
import os
from io import BytesIO
from PIL import Image

app = Flask(__name__)

# AWS S3の設定
S3_BUCKET = 'suiko-ehime-bucket-face-data'

# データベース接続の設定（適切な情報を設定してください）
db_config = {
    'host': 'database-1.c3yy084war8k.ap-northeast-1.rds.amazonaws.com',  # データベースのホスト
    'user': 'admin',  # データベースのユーザー名
    'password': 'suiko-ehime-mysql',  # データベースのパスワード
    'database': 'checkindb'  # 使用するデータベース名
}

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    connection = None  # connection 変数を初期化
    cursor = None  # cursor 変数を初期化

    try:
        # データベース接続とカーソルの作成
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        gender = request.form.get('gender', None)
        name = request.form.get('name', None)

        # 性別のバリデーション
        if gender not in ['Male', 'Female', 'Prefer not to say']:
            return "Invalid gender value", 400  # 不正な性別の場合はエラーを返す

        img_data = request.form['file']
        img_data = img_data.split(",")[1]
        img_bytes = base64.b64decode(img_data)
        image = Image.open(BytesIO(img_bytes))

        file_name = f"{name.replace(' ', '_')}.jpeg"
        file_path = os.path.join('uploads', file_name)

        if not os.path.exists('uploads'):
            os.makedirs('uploads')

        image.convert('RGB').save(file_path, 'JPEG')

        s3 = boto3.client('s3')
        s3.upload_file(file_path, S3_BUCKET, file_name)

        os.remove(file_path)

        # データベースに名前と性別を挿入
        query = "INSERT INTO information (person_name, entry_time, gender) VALUES (%s, NOW(), %s)"
        values = (name, gender)
        cursor.execute(query, values)
        connection.commit()

        return 'File uploaded and data saved successfully!'

    except Exception as e:
        return f"Error: {str(e)}", 500  # エラーを返す

    finally:
        # connection と cursor の存在を確認してから閉じる
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == '__main__':
    app.run(debug=True)
