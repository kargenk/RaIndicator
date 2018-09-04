#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import base64
import cv2
import matplotlib.pyplot as plt
import numpy as np
import json
import collections as cl

# 雨雲検知関数
def searchRain(array):
    # XRAINの反例画像から色を取得
    purple, red, orange, yellow, blue_10_20, blue_5_10, blue_1_5, blue_0_1, ex, no = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    cMap = np.array([[154,0,121], [231,40,0], [255,153,0], [250,245,0], [0,56,255], [33,152,255], [102,204,255], [153,255,255]])
    for h in range(array.shape[0]):
        for w in range(array.shape[1]):
            if(np.allclose(array[h,w,:], cMap[0])):
                purple += 1
            elif(np.allclose(array[h,w,:], cMap[1])):
                red += 1
            elif(np.allclose(array[h,w,:], cMap[2])):
                orange += 1
            elif(np.allclose(array[h,w,:], cMap[3])):
                yellow += 1
            elif(np.allclose(array[h,w,:], cMap[4])):
                blue_10_20 += 1
            elif(np.allclose(array[h,w,:], cMap[5])):
                blue_5_10 += 1
            elif(np.allclose(array[h,w,:], cMap[6])):
                blue_1_5 += 1
            elif(np.allclose(array[h,w,:], cMap[7])):
                blue_0_1 += 1
            elif(np.allclose(array[h,w,:], [255,255,255])):
                no += 1
            else:
                ex += 1 # 完全一致ではなかったもの
    
    # 雨量と該当ピクセル数の辞書を作成
    keys = ['over 80 mm/h', '50 - 80 mm/h', '30 - 50 mm/h', '20 - 30 mm/h', '10 - 20 mm/h', '5 - 10 mm/h', '1 - 5 mm/h', 'no rain', 'exception']
    values = [purple, red, orange, yellow, blue_10_20, blue_5_10, blue_1_5, blue_0_1, no, ex]
    rainPointDict = dict(zip(keys, values))
    
    # 川や高速道路などの例外(ex)が多ければ雨はないと判定
    if max(rainPointDict.items(), key=lambda x:x[1])[0] == 'exception':
        return 'no rain'
    else:
        # lambdaを用い 配列要素の１番目を返却する無名関数を作成し、オプション引数に渡す
        return max(rainPointDict.items(), key=lambda x:x[1])[0]

def fetch_origin_image(longitude, latitude):
    # ブラウザのオプションを格納する
    options = Options()

    # Headlessモードを有効にする(コメントアウトするとブラウザが実際に立ち上がる)
    # バックグラウンドで動くモードで，実際には普通のブラウザとして動いているが，デスクトップには表示されない
    options.set_headless(True)

    # ブラウザを起動する
    driver = webdriver.Chrome("./chromedriver.exe", chrome_options=options)
    # driver = webdriver.Chrome("/usr/lib/chromium-browser/chromedriver", chrome_options=options)

    # 経度の指定
    # lon = str(135.9615) # bkc:135.9615
    # lat = str(34.98208)  # bkc:34.98208

    # ブラウザでWebページ(XRAINレーダー雨量画面，GIS版)にアクセスする
    driver.get("http://www.river.go.jp/x/krd0107010.php?" +
               "lon=" + longitude +
               "&lat=" + latitude +
               "&opa=0&zoom=12&leg=0&ext=0")

    # レーダー雨量画像が表示される領域であるcanvasを取得
    canvas = driver.find_element_by_css_selector('#mp-radar > div > canvas')

    # canvasをPNGのbase64データを取得
    canvas_base64 = driver.execute_script("return arguments[0].toDataURL('image/png').substring(21);", canvas)

    # デコード
    canvas_png = base64.b64decode(canvas_base64)

    # png形式で画像を保存
    with open("./img/canvas.png", 'wb') as f:
        f.write(canvas_png)

    # ブラウザを終了(全てのタブを閉じる)
    driver.quit()

def get_rain_image():
    # 保存したレーダー画像の読み込み
    img_bgr = cv2.imread("./img/canvas.png")
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    # 画像のサイズ取得
    oHeight, oWidth, oChannels = img_rgb.shape[:3]

    # 中心座標の取得
    hCenter = oHeight/2
    wCenter = oWidth/2

    # 自陣の周囲の1,3,5kmの画像を生成
    square1 = img_bgr[int(hCenter-35):int(hCenter+35), int(wCenter-35):int(wCenter+35)]     # 周囲1km四方
    square3 = img_bgr[int(hCenter-105):int(hCenter+105), int(wCenter-105):int(wCenter+105)] # 周囲3km四方
    square5 = img_bgr[int(hCenter-175):int(hCenter+175), int(wCenter-175):int(wCenter+175)] # 周囲5km四方
    cv2.imwrite("./img/2km.png", square1)
    cv2.imwrite("./img/6km.png", square3)
    cv2.imwrite("./img/10km.png", square5)

def get_json():
    # 指定距離の画像を読み込む
    img = cv2.cvtColor(cv2.imread("./img/10km.png"), cv2.COLOR_BGR2RGB)
    height, width = img.shape[:2]

    # 境界用変数
    hBorder = int(height / 3)
    wBorder = int(width / 3)

    # 画像を8方位と自陣の計9パネルに分割
    NW = img[0:hBorder, 0:wBorder]                     # 北西
    N = img[0:hBorder, wBorder:wBorder*2]              # 北
    NE = img[0:hBorder, wBorder*2:wBorder*3]           # 北東
    W = img[hBorder:hBorder*2, 0:wBorder]              # 西
    C = img[hBorder:hBorder*2, wBorder:wBorder*2]      # 中央(自陣)
    E = img[hBorder:hBorder*2, wBorder*2:wBorder*3]    # 東
    SW = img[hBorder*2:hBorder*3, 0:wBorder]           # 南西
    S = img[hBorder*2:hBorder*3, wBorder:wBorder*2]    # 南
    SE = img[hBorder*2:hBorder*3, wBorder*2:wBorder*3] # 南東

    # 連結画像を生成
    plt.subplot(331),plt.imshow(NW),plt.title('NW')
    plt.subplot(332),plt.imshow(N),plt.title('N')
    plt.subplot(333),plt.imshow(NE),plt.title('NE')
    plt.subplot(334),plt.imshow(W),plt.title('W')
    plt.subplot(335),plt.imshow(C),plt.title('C')
    plt.subplot(336),plt.imshow(E),plt.title('E')
    plt.subplot(337),plt.imshow(SW),plt.title('SW')
    plt.subplot(338),plt.imshow(S),plt.title('S')
    plt.subplot(339),plt.imshow(SE),plt.title('SE')
    plt.savefig('./static/images/xrain.png')

    # 9枚の画像を格納した配列を生成
    direction_img = np.array([NW, N, NE, W, C, E, SW, S, SE])

    direction = ['NW', 'N', 'NE', 'W', 'C', 'E', 'SW', 'S', 'SE'] # 8方位

    # 各方位ごとに全画素値を探索して，最も適している雨量を取得
    rainfall = [] # 雨量
    for i in direction_img:
        rainfall.append(searchRain(i))

    # キーが方位，値が雨量の順序指定型の辞書を作成
    rainDict = cl.OrderedDict()
    for j in range(len(direction)):
        rainDict[direction[j]] = rainfall[j]

    # 辞書からJSONファイルを作成
    with open('./rainfall.json', 'w', encoding='utf8') as f:
        json.dump(rainDict, f)
