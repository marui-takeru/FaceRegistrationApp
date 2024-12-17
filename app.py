from flask import Flask, render_template, request, redirect, url_for, make_response
import mysql.connector
import boto3
import base64
import os
from io import BytesIO
from PIL import Image
import logging

# Flaskアプリケーション設定
app = Flask(__name__)
app.secret_key = 'suiko-nobu'  # セッション管理用のシークレットキー

# AWS S3の設定
S3_BUCKET = 'suiko-ehime-bucket-face-data'

# データベース接続の設定
db_config = {
    'host': 'database-1.c3yy084war8k.ap-northeast-1.rds.amazonaws.com',
    'user': 'admin',
    'password': 'suiko-ehime-mysql',
    'database': 'checkindb'
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    connection = None
    cursor = None

    try:
        # データベース接続
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # フォームデータ取得
        gender = request.form.get('gender', None)
        name = request.form.get('name', None)

        # 性別のバリデーション
        if gender not in ['Male', 'Female', 'Prefer not to say']:
            return "Invalid gender value", 400

        # Base64画像データを取得
        img_data = request.form['file']
        img_data = img_data.split(",")[1]
        img_bytes = base64.b64decode(img_data)

        # 画像処理
        image = Image.open(BytesIO(img_bytes))
        file_name = f"{name.replace(' ', '_')}.jpeg"
        file_path = os.path.join('uploads', file_name)

        # アップロードディレクトリが存在しない場合は作成
        if not os.path.exists('uploads'):
            os.makedirs('uploads')

        # 画像を保存
        image.convert('RGB').save(file_path, 'JPEG')

        # S3にアップロード
        s3 = boto3.client('s3')
        s3.upload_file(file_path, S3_BUCKET, file_name)

        # ローカルファイルを削除
        os.remove(file_path)

        # データベースに名前と性別を挿入
        query = "INSERT INTO information (person_name, last_time, gender) VALUES (%s, NOW(), %s)"
        values = (name, gender)
        cursor.execute(query, values)
        connection.commit()

        # アップロード成功後、完了画面にリダイレクト
        return redirect(url_for('upload_complete'))

    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=True)
        return f"Error: {str(e)}", 500

    finally:
        # データベース接続を閉じる
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/upload_complete')
def upload_complete():
    # キャッシュ防止のヘッダーを追加
    response = make_response(render_template('upload_complete.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

if __name__ == '__main__':
    app.run(debug=True)
