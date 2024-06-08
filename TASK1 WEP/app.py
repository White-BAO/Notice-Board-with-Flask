from flask import Flask, render_template, redirect, url_for, request, send_file, session
import pymysql
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
from werkzeug.utils import secure_filename
import os
from wtforms.validators import InputRequired

app = Flask(__name__)
app.config['SECRET_KEY'] = 'B4C'
app.config['UPLOAD_FOLDER'] = 'files'
app.config['profile_pic'] = 'static/profile_pic'

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

# get_user 함수 
def get_user(USER_NAME, PW=None):
    if PW:
        cursor.execute(f"SELECT USER_ID, NAME, SCHOOL, profile_pic FROM USERINFO WHERE USER_NAME='{USER_NAME}' AND PW='{PW}'")
    else:
        cursor.execute(f"SELECT USER_ID, NAME, SCHOOL, profile_pic FROM USERINFO WHERE USER_NAME='{USER_NAME}'")
    user = cursor.fetchone()
    if user:
        # 프로필 사진이 NULL인 경우 빈 문자열로 대체
        user['profile_pic'] = user['profile_pic'] if user['profile_pic'] else ""
    return user

# update_user 함수에서 profile_pic_filename을 업데이트할 때 디렉토리를 변경해줍니다.
def update_user(USER_ID, NAME, SCHOOL, profile_pic_filename=None):
    if profile_pic_filename:
        cursor.execute(f"UPDATE USERINFO SET NAME='{NAME}', SCHOOL='{SCHOOL}', profile_pic='{profile_pic_filename}' WHERE USER_ID={USER_ID}")
    else:
        cursor.execute(f"UPDATE USERINFO SET NAME='{NAME}', SCHOOL='{SCHOOL}' WHERE USER_ID={USER_ID}")
    db.commit()
    return USER_ID

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

class UploadFileForm(FlaskForm):
    file = FileField("File", validators=[InputRequired()])
    submit = SubmitField("Upload File")

# /post 라우트 함수
@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def show_post(post_id): 
    form = UploadFileForm()  # 파일 업로드 폼 생성
    post = get_post(post_id)  # 게시물 가져오기

    if post:
        if form.validate_on_submit():
            file = form.file.data 
            file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'], secure_filename(file.filename)))
            return "File has been uploaded successfully, Back to the previous page!"

        # 업로드된 파일이 저장된 디렉토리 경로 설정
        upload_dir = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
        # 업로드된 파일 목록 가져오기
        uploaded_files = os.listdir(upload_dir)

        # 비밀글일 경우
        if post.get('is_secret'):
            if request.method == 'POST':
                password = request.form.get('password')
                if password == post.get('secret_password'):
                    return render_template('post.html', post=post, form=form, uploaded_files=uploaded_files)
                else:
                    return "Incorrect password. You cannot view this post."

            # 비밀번호 입력 폼을 보여줌
            return render_template('enter_password.html', post_id=post_id)

        # 비밀글이 아닌 경우
        return render_template('post.html', post=post, form=form, uploaded_files=uploaded_files)
    else:
        return "Post not found."




# 게시물 생성 함수 및 라우트
@app.route('/post', methods=['GET', 'POST'])
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        is_secret = 'is_secret' in request.form  # 비밀글 여부 확인
        secret_password = request.form.get('password') if is_secret else None  # 비밀번호 입력 받기
        
        # 게시물 데이터를 데이터베이스에 저장
        cursor.execute("INSERT INTO BOARD (title, content, is_secret, secret_password) VALUES (%s, %s, %s, %s)", (title, content, is_secret, secret_password))
        db.commit()

        # 생성된 게시물의 ID를 가져옴
        cursor.execute("SELECT LAST_INSERT_ID()")
        post_id = cursor.fetchone()['LAST_INSERT_ID()']

        return redirect(url_for('show_post', post_id=post_id))
    
    return render_template('create_post.html')  # 게시물 생성 폼 템플릿으로 변경

# 파일 다운로드
@app.route('/download/<files>')
def download_file(files):
    # 파일이 있는 디렉토리와 파일명을 지정합니다.
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], files)
    # 해당 파일을 다운로드합니다.
    return send_file(filepath, as_attachment=True)

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

# 회원가입 폼 라우트
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        USER_NAME = request.form['USER_NAME']
        PW = request.form['PW']
        NAME = request.form['NAME']
        SCHOOL = request.form['SCHOOL']
        
        # 사용자 정보를 MySQL에 저장
        try:
            cursor.execute("INSERT INTO USERINFO (USER_NAME, PW, NAME, SCHOOL) VALUES (%s, %s, %s, %s)", (USER_NAME, PW, NAME, SCHOOL))
            db.commit()
            return redirect(url_for('index'))  # 회원가입 후 인덱스 페이지로 리다이렉트
        except Exception as e:
            db.rollback()  # 롤백
            return "회원가입에 실패했습니다."
    return render_template('register.html')  # 회원가입 폼 템플릿으로 변경

# 로그인 라우트
@app.route('/login', methods=['POST'])
def login():
    USER_NAME = request.form['USER_NAME']
    PW = request.form['PW']

    # 데이터베이스에서 사용자 정보 조회
    user = get_user(USER_NAME, PW)

    if user:
        # 로그인이 성공한 경우에만 세션에 사용자 정보 저장
        session['USER_ID'] = user['USER_ID']
        session['USER_NAME'] = USER_NAME
        session['NAME'] = user['NAME']
        session['SCHOOL'] = user['SCHOOL']

        # 로그인 성공 후에는 LOGIN_FAILED 세션 키를 제거합니다.
        session.pop('LOGIN_FAILED', None)

        # 로그인 성공 시 myprofile 페이지로 리다이렉션
        return redirect(url_for('myprofile', USER_ID=user['USER_ID']))  

    else:
        # 로그인이 실패한 경우에도 세션에 기본 정보를 저장하여 로그인 실패를 구분할 수 있도록 함
        session['LOGIN_FAILED'] = True
        return 'Invalid username or password, back to the previous page.'

# 유저 정보 수정
@app.route('/update_user', methods=['POST'])
def update_user_route():
    USER_ID = request.form['USER_ID']
    NAME = request.form['NAME']
    SCHOOL = request.form['SCHOOL']

    if 'profile_pic' in request.files:
        profile_pic = request.files['profile_pic']
        if profile_pic.filename != '':
            profile_pic_filename = secure_filename(profile_pic.filename)
            profile_pic_dir = os.path.join(app.root_path, app.config['profile_pic'])

            if not os.path.exists(profile_pic_dir):
                os.makedirs(profile_pic_dir)

            profile_pic_path = os.path.join(profile_pic_dir, profile_pic_filename)
            profile_pic.save(profile_pic_path)

            updated_USER_ID = update_user(USER_ID, NAME, SCHOOL, profile_pic_filename)
        else:
            updated_USER_ID = update_user(USER_ID, NAME, SCHOOL)
    else:
        updated_USER_ID = update_user(USER_ID, NAME, SCHOOL)

    if updated_USER_ID:
        return redirect(url_for('myprofile', USER_ID=USER_ID))
    else:
        return "Failed to update user information."

# myprofile 라우트 
@app.route('/myprofile/<int:USER_ID>')
def myprofile(USER_ID):
    if 'USER_ID' in session and session['USER_ID'] == USER_ID:
        user = get_user(session['USER_NAME'])  # 세션에서 USER_NAME을 사용하여 사용자 정보 가져오기
        if user:
            profile_pic_path = None
            if user['profile_pic']:  # 프로필 사진이 있는지 확인
                profile_pic_path = url_for('static', filename=f"profile_pic/{user['profile_pic']}")
            return render_template('myprofile.html', user=user, profile_pic_path=profile_pic_path)
    # 로그인되지 않았거나 사용자 정보를 찾을 수 없는 경우 로그인 페이지로 리다이렉션
    return redirect(url_for('index'))

# 다른 사용자 프로필 보기 라우트
@app.route('/view_profile/<int:USER_ID>')
def view_profile(USER_ID):
    user = None
    if 'USER_ID' in session:
        user = get_user_by_id(USER_ID)
    if user:
        profile_pic_path = None
        if user['profile_pic']:  # 프로필 사진이 있는지 확인
            profile_pic_path = url_for('static', filename=f"profile_pic/{user['profile_pic']}")
        return render_template('view_profile.html', user=user, profile_pic_path=profile_pic_path)
    return redirect(url_for('index'))

# 유저 아이디로 사용자 정보 조회 함수
def get_user_by_id(USER_ID):
    cursor.execute(f"SELECT USER_ID, NAME, SCHOOL, profile_pic FROM USERINFO WHERE USER_ID={USER_ID}")
    user = cursor.fetchone()
    if user:
        user['profile_pic'] = user['profile_pic'] if user['profile_pic'] else ""
    return user

# 비밀번호 찾기 라우트 함수
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        NAME = request.form['NAME']
        SCHOOL = request.form['SCHOOL']

        # 데이터베이스에서 이름과 학교를 기준으로 사용자 정보 조회
        user = get_user_by_name_and_school(NAME, SCHOOL)

        if user:
            # 사용자가 존재하고 입력한 학교가 일치하는 경우, ID와 PW를 사용자에게 전달하거나 보여줌.
            return f"Your ID: {user['USER_NAME']}, Your Password: {user['PW']}"
        else:
            # 사용자가 존재하지 않거나 입력한 정보가 일치하지 않는 경우 메시지를 표시.
            return "Sorry, we couldn't find your information. Please try again or contact support."
    return render_template('forgot_password.html')  # 비밀번호 찾기 폼을 렌더링합니다.


# 새로운 사용자 정보 함수
def get_user_by_name_and_school(NAME, SCHOOL):
    cursor.execute(f"SELECT USER_NAME, PW FROM USERINFO WHERE NAME='{NAME}' AND SCHOOL='{SCHOOL}'")
    user = cursor.fetchone()
    return user

# 로그아웃 라우트
@app.route('/logout')
def logout():
    session.pop('USER_ID', None)
    session.pop('USER_NAME', None)
    session.pop('NAME', None)
    session.pop('SCHOOL', None)
    return redirect(url_for('index'))

# 게시물 데이터를 임시로 저장하기 위한 딕셔너리
posts = {}

# 게시물 생성 함수 및 라우트
@app.route('/post', methods=['GET', 'POST'])
def create_or_show_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        is_secret = 'is_secret' in request.form  # 비밀글 여부 확인
        secret_password = request.form.get('password') if is_secret else None  # 비밀번호 입력 받기
        
        # 게시물 데이터를 데이터베이스에 저장
        cursor.execute("INSERT INTO BOARD (title, content, is_secret, secret_password) VALUES (%s, %s, %s, %s)", (title, content, is_secret, secret_password))
        db.commit()

        # 생성된 게시물의 ID를 가져옴
        cursor.execute("SELECT LAST_INSERT_ID()")
        post_id = cursor.fetchone()['LAST_INSERT_ID()']

        return redirect(url_for('show_post', post_id=post_id))
    
    elif request.method == 'GET':
        return render_template('create_post.html')  # 게시물 생성 폼 템플릿으로 변경


# 비밀번호 입력 처리
@app.route('/enter_password/<int:post_id>', methods=['POST'])
def enter_password(post_id):
    password = request.form['password']
    post = posts.get(post_id)
    
    # 입력된 비밀번호가 게시물의 비밀번호와 일치하는지 확인
    if post and password == post['secret_password']:
        return redirect(url_for('view_post', post_id=post_id))
    else:
        return 'Incorrect password.'

# 검색 기능
@app.route('/search', methods=['POST'])
def search():
    keyword = request.form['keyword']
    search_option = request.form['search_option']
    
    if search_option == 'title':
        # 제목에서만 검색하는 쿼리 실행
        cursor.execute("SELECT * FROM BOARD WHERE title LIKE %s", ('%' + keyword + '%'))
    elif search_option == 'content':
        # 내용에서만 검색하는 쿼리 실행
        cursor.execute("SELECT * FROM BOARD WHERE content LIKE %s", ('%' + keyword + '%'))
    elif search_option == 'both':
        # 제목과 내용에서 검색하는 쿼리 실행
        cursor.execute("SELECT * FROM BOARD WHERE title LIKE %s OR content LIKE %s", ('%' + keyword + '%', '%' + keyword + '%'))
    
    posts = cursor.fetchall()
    return render_template('index.html', posts=posts)

if __name__ == '__main__':
    app.run(debug=True)
