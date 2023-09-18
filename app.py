# 引用flask相關資源
from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
# 引用時間模組
import time
import datetime
# TODO: 引用各種表單類別
import os

from forms import (
    CreateProductForm,
    EditProductForm,
    DeleteProductForm,
    CreateCommentForm,
    EditCommentForm
)

# 初始化Firebase Firestore
# https://firebase.google.com/docs/firestore/quickstart
import firebase_admin
from firebase_admin import credentials, firestore, auth
from flask_wtf.csrf import CSRFProtect

# 驗證金鑰
cred = credentials.Certificate("jim-flask-ntu341-firebase-key.json")
firebase_admin.initialize_app(cred)

# 資料庫
db = firestore.client()

app = Flask(__name__)

csrf = CSRFProtect(app)
# 可讓每個模板都可取得CSRF Token
csrf.init_app(app)

# 取消快取，可以及時更新CSS JS
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
# 設定應用程式的SECRET_KEY
app.config['SECRET_KEY'] = 'ntuflask2021'  # Change this!
# cookie 名稱
cookie_name = 'ntu-cookie'

def is_admin():
    return check_login()['auth_user']['is_admin']


#每個路由都會走一次
@app.context_processor
def check_login():
    auth_user = {
        "user": {},
        "is_login": False,
        "is_admin": False
    }
    # 取回session_cookie
    session_cookie = request.cookies.get(cookie_name)
    try:
        user = auth.verify_session_cookie(session_cookie)
        auth_user["is_login"] = True
        auth_user["user"] = user
        email = user["email"]
        # 取得 admin_list/{email} 文件
        admin_doc = db.document("admin_list/" + email).get()
        print(email)
        print(admin_doc)
        print(admin_doc.exists)
        # 如果此文件存在
        if admin_doc.exists:
            auth_user["is_admin"] = True
            print(admin_doc)
    except:
        pass
        # print("驗證失敗")
    return dict(auth_user=auth_user)


@app.route('/api/login', methods=['POST'])
def login():
    # 取得JS傳給後端的物件(dict)
    id_token = request.json["id_token"]
    # 設定過期日
    expires_in = datetime.timedelta(days=5)
    print("id_token", id_token)
    # 準備給前端的回應
    res = jsonify({"msg": "後端登入成功了"})
    session_cookie = auth.create_session_cookie(
        id_token, expires_in=expires_in)
    # cookie的有效期限
    expires = datetime.datetime.now() + expires_in
    # 將cookie寫入至瀏覽器
    res.set_cookie(
        cookie_name, session_cookie, expires=expires, httponly=True
    )
    return res


@app.route('/api/logout', methods=['POST'])
def logout():
    res = jsonify({"msg": "Logout!"})
    res.set_cookie(cookie_name, expires=0)
    return res


@app.route('/')
def index_page():
    # 取得資料庫的商品列表資料
    doc_list = db.collection("product_list").order_by(
        "created_at", direction="DESCENDING").get()
    product_list = []
    # 取出所有取得到的文件(object)
    for doc in doc_list:
        # 文件的ID doc.id
        doc_id = doc.id
        # 取得文件裡存的資料 doc.to_dict
        product = doc.to_dict()
        # 將文件的id存到產品內
        product["id"] = doc_id
        product_list.append(product)
    # 首頁路由
    return render_template('index.html',
                           header_title="首頁",
                           product_list=product_list
                           )


@app.route('/product/create', methods=["GET", "POST"])
def create_product_page():
    if not is_admin():
        return redirect('/')
    # 建立商品頁的路由

    # 建立商品表單的物件實例
    form = CreateProductForm()
    # print(form.validate_on_submit())
    # 設定表單送出後的處理
    if form.validate_on_submit():
        # 整理資料庫要存的資料
        product = {
            "title": form.title.data,
            "img": form.img.data,
            "price": form.price.data,
            "category": form.category.data,
            "description": form.description.data,
            "on_sale": form.on_sale.data,
            "created_at": time.time()
        }
        # 將產品資料存到資料庫的product_list集合
        db.collection("product_list").add(product)

        # 取得引導頁面函數對應的網址
        redirect_url = url_for("create_finished_page")  #轉跳韓式
        flash(f"{product['title']} 已被成功建立", "success")

        # new_product save to session
        session['product'] = product

        # 引導到 /product/create-finished
        return redirect(redirect_url)

    # TODO: 將新商品的資料儲存在session內以便下個頁面可顯示新資料
    return render_template('product/create.html',
                           header_title="建立商品",
                           form=form
                           )


@app.route('/product/create-finished')
def create_finished_page():
    # 取得 new_product
    product = session['product']
    # 商品建立成功的路由
    return render_template('product/create_finished.html',
                           header_title="商品建立完成",
                           product=product
                           )


@app.route('/product/<pid>/show', methods=["GET", "POST"])
def show_product_page(pid):
    # 建立留言表單
    form = CreateCommentForm()
    if form.validate_on_submit():
        comment = {
            "email": form.email.data,
            "content": form.content.data,
            "created_at": time.time(),
            # 記錄此留言所屬的產品ID
            "product_id": pid
        }
        db.collection("comment_list").add(comment)
        flash("留言成功", "success")
        return redirect(f"/product/{pid}/show")
    # 預設留言清單
    comment_list = []
    comment_docs = db.collection("comment_list").where(
        "product_id", "==", pid).order_by("created_at").get()

    for doc in comment_docs:
        comment = doc.to_dict()
        # 產生一份更新留言的表單並存在此留言(dict)中
        comment["form"] = EditCommentForm(prefix=doc.id)
        # 如果更新留言的表單有被送出
        if comment["form"].validate_on_submit():
            # 取出表單內更新的內容
            edited_comment = {
                "content": comment["form"].content.data
            }
            # 存到資料庫更新
            db.document(f"comment_list/{doc.id}").update(edited_comment)
            flash("留言更新完成", "warning")
            return redirect(f"/product/{pid}/show")
        comment_list.append(comment)
    # print("留言清單", comment_list)
    # 透過pid(文件的id)取得文件資料
    doc = db.document(f"product_list/{pid}").get()
    product = doc.to_dict()
    return render_template('product/show.html',
                           header_title=product["title"],
                           header_img=product["img"],
                           product=product,
                           form=form,
                           comment_list=comment_list
                           )


@app.route('/product/<pid>/edit', methods=["GET", "POST"])
def edit_product_page(pid):
    if not is_admin():
        return redirect('/')
    # 編輯商品頁的路由
    # 取得資料庫指定pid的商品資料
    doc = db.document(f"product_list/{pid}").get()
    product = doc.to_dict()
    # 產生移除表單
    delete_form = DeleteProductForm()
    # 移除表單被送出且該填的都有填
    if delete_form.validate_on_submit():
        # 根據文件id移除商品
        db.document(f"product_list/{pid}").delete()
        flash(f"{product['title']} 已被成功移除", "danger")
        # 回首頁
        return redirect("/")
    # 建立編輯商品表單的實例
    form = EditProductForm()
    # 如果表單驗證成功且被送出
    if form.validate_on_submit():
        # 描述產品新資料
        edited_product = {
            "title": form.title.data,
            "img": form.img.data,
            "price": form.price.data,
            "description": form.description.data,
            "on_sale": form.on_sale.data,
            "updated_at": time.time()
        }
        # 透過文件id更新資料
        db.document(f"product_list/{pid}").update(edited_product)
        # 顯示提示
        flash(f"{edited_product['title']} 已被更新", "warning")
        return redirect("/")
    # 讓表單的每個欄位預設該產品的值
    form.title.data = product['title']
    form.img.data = product['img']
    form.price.data = product['price']
    form.category.data = product['category']
    form.description.data = product['description']
    form.on_sale.data = product['on_sale']
    return render_template('product/edit.html',
                           header_title=product['title'],
                           header_img=product['img'],
                           form=form,
                           delete_form=delete_form
                           )


if __name__ == '__main__':
    port = int(os.environ.get("PORT",5000))
    dev_host = '127.0.0.1'
    heroku_host = '0.0.0.0'
    # 應用程式開始運行
    app.run(debug=True, host=dev_host, port=port)
