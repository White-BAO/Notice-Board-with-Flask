# using Flask
from flask import Flask, render_template, redirect, url_for, request
import pymysql

app = Flask(__name__)

# 데이터베이스 연결
db = pymysql.connect(host="localhost", user="root", password="kang8614", charset="utf8", database="python")
cursor = db.cursor(pymysql.cursors.DictCursor)

# 게시물 목록을 가져오는 함수
def get_posts():
    cursor.execute("SELECT * FROM BOARD")
    posts = cursor.fetchall()
    return posts

# 게시물 내용을 가져오는 함수
def get_post(post_id):
    cursor.execute(f"SELECT * FROM BOARD WHERE id={post_id}")
    post = cursor.fetchone()
    return post

# 게시물 삭제 함수
def delete_post(id):
    cursor.execute(f"DELETE FROM BOARD WHERE id={id}")
    db.commit()
    return id

# 게시물 업데이트 함수
def update_post(id, title, content):
    cursor.execute(f"UPDATE BOARD SET title='{title}', content='{content}' WHERE id={id}")
    db.commit()
    return id

# index 라우트 함수
@app.route('/')
def index():
    posts = get_posts()  # 게시물 목록을 가져옴
    return render_template('index.html', posts=posts)

# /post 라우트 함수
@app.route('/post/<int:post_id>')
def show_post(post_id):
    post = get_post(post_id)
    if post:
        return render_template('post.html', post=post)


# delete 라우트 함수
@app.route('/delete/<int:id>', methods=['POST', 'DELETE'])
def delete(id):
    deleted_post_id = delete_post(id)  # 게시물 삭제
    if deleted_post_id:
        return redirect(url_for('index'))  # 삭제 후 목록 페이지로 리다이렉트


# update 라우트 함수
@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    if request.method == 'GET':
        post = get_post(id)
        if post:
            return render_template('update.html', post=post)
    elif request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        updated_post_id = update_post(id, title, content)
        if updated_post_id:
            return redirect(url_for('show_post', post_id=id))


# create 라우트 함수
@app.route('/submit', methods=['POST'])
def submit():
    title = request.form['title']
    content = request.form['content']
    # 게시물을 데이터베이스에 등록하는 코드
    cursor.execute("INSERT INTO BOARD (title, content) VALUES (%s, %s)", (title, content))
    db.commit()
    return redirect(url_for('index'))  # 등록 후 목록 페이지로 리다이렉트

# 검색 기능
@app.route('/search', methods=['POST'])
def search():
    keyword = request.form['keyword']
    search_option = request.form['search_option']
    
    if search_option == 'title':
        # 제목에서만 검색하는 쿼리 실행
        cursor.execute(f"SELECT * FROM BOARD WHERE title LIKE '%{keyword}%'")
    elif search_option == 'content':
        # 내용에서만 검색하는 쿼리 실행
        cursor.execute(f"SELECT * FROM BOARD WHERE content LIKE '%{keyword}%'")
    elif search_option == 'both':
        # 제목과 내용에서 검색하는 쿼리 실행
        cursor.execute(f"SELECT * FROM BOARD WHERE title LIKE '%{keyword}%' OR content LIKE '%{keyword}%'")
    
    posts = cursor.fetchall()
    return render_template('index.html', posts=posts)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
