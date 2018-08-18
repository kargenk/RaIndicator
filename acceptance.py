#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for
import json
import XRAIN_detector as det # 自作のモジュール

# 自身の名称をappという名前でインスタンス化
app = Flask(__name__)

# webアプリケーション用のルーティングを記述

# indexにアクセスしたときの処理
@app.route('/')
def index():
    title = "デモ"
    message = "経度(longitude)と緯度(latitude)を入力してください"
    # index.htmlをレンダリング
    return render_template('index.html',
                           message=message, title=title)

# /postにアクセスしたときの処理
@app.route('/post', methods=['POST', 'GET'])
def post():
    title = '入力画面'
    if request.method == 'POST':
        # リクエストフォームから経度と緯度を取得
        lon = request.form['longitude']
        lat = request.form['latitude']

        # 該当地点からの方位と雨量のJSONデータを作成
        det.fetch_origin_image(lon, lat)
        det.get_rain_image()
        det.get_json()

        # # index.htmlをレンダリング
        # return render_template('index.html',
        #                       longitude=lon, latitude=lat, title=title)
        with open('./rainfall.json', 'r') as f:
            jsonData = json.load(f)
        return json.dumps(jsonData)
    else:
        # エラーなどによるリダイレクト処理
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.debug = False # デバッグモードの無効化
    app.run('0.0.0.0')        # 実行，引数にhostとポートを指定可能
    #app.run()
