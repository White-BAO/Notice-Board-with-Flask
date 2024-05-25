from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# 투두리스트 만들기
todos = []

@app.route('/')
def index():
    return render_template('index.html', todos=todos) # HTML로 데이터 전달

@app.route('/add', methods=['POST'])
def add_todo():
    todo = request.form['todo'] # 투두리스트 목록받기
    todos.append(todo)  # 투두리스트 추가
    return redirect(url_for('index')) # HTML로 리다이렉션

@app.route('/complete/<int:todo_id>') # 완료한투두리스트 제거하기
def complete_todo(todo_id): 
    if todo_id < len(todos):
        todos.pop(todo_id) # 완료한 투두 제거
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=False)
