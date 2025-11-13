from flask import Flask, render_template, request, redirect, url_for, session
import json
import os

app = Flask(__name__)
app.secret_key = 'super_secret_key'

DATA_FOLDER = 'data'
USERS_FILE = os.path.join(DATA_FOLDER, 'users.json')
STUDENTS_FILE = os.path.join(DATA_FOLDER, 'students.json')


# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===
def load_json(path):
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump([], f)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# === ГЛАВНАЯ СТРАНИЦА ===
@app.route('/')
def index():
    return render_template('index.html')


# === РЕГИСТРАЦИЯ ===
@app.route('/register', methods=['GET', 'POST'])
def register():
    users = load_json(USERS_FILE)
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        if any(u['username'] == username for u in users):
            return render_template('register.html', error="Такой пользователь уже существует!")

        users.append({'username': username, 'password': password, 'role': role})
        save_json(USERS_FILE, users)
        return redirect(url_for('login'))

    return render_template('register.html')


# === ВХОД ===
@app.route('/login', methods=['GET', 'POST'])
def login():
    users = load_json(USERS_FILE)
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = next((u for u in users if u['username'] == username and u['password'] == password), None)
        if user:
            session['user'] = user
            return redirect(url_for('teacher' if user['role'] == 'teacher' else 'student'))
        else:
            return render_template('login.html', error="Неверное имя пользователя или пароль")

    return render_template('login.html')


# === КАБИНЕТ УЧИТЕЛЯ ===
@app.route('/teacher')
def teacher():
    if 'user' not in session or session['user']['role'] != 'teacher':
        return redirect(url_for('login'))

    students = load_json(STUDENTS_FILE)
    return render_template('teacher.html', students=students, user=session['user'])


# === ДОБАВЛЕНИЕ УЧЕНИКА ===
@app.route('/add_student', methods=['POST'])
def add_student():
    if 'user' not in session or session['user']['role'] != 'teacher':
        return redirect(url_for('login'))

    name = request.form['name']
    subject = request.form['subject']
    grades = request.form['grades']

    students = load_json(STUDENTS_FILE)

    # Проверяем, существует ли ученик
    student = next((s for s in students if s['name'] == name), None)
    if not student:
        student = {'name': name, 'subjects': []}
        students.append(student)

    # Добавляем предмет и оценки
    student['subjects'].append({'subject': subject, 'grades': grades})
    save_json(STUDENTS_FILE, students)

    return redirect(url_for('teacher'))


# === УДАЛЕНИЕ УЧЕНИКА ===
@app.route('/delete_student/<name>')
def delete_student(name):
    if 'user' not in session or session['user']['role'] != 'teacher':
        return redirect(url_for('login'))

    students = load_json(STUDENTS_FILE)
    students = [s for s in students if s['name'] != name]
    save_json(STUDENTS_FILE, students)
    return redirect(url_for('teacher'))


# === РЕДАКТИРОВАНИЕ ПРЕДМЕТОВ И ОЦЕНОК ===
@app.route('/edit_student/<name>', methods=['GET', 'POST'])
def edit_student(name):
    if 'user' not in session or session['user']['role'] != 'teacher':
        return redirect(url_for('login'))

    students = load_json(STUDENTS_FILE)
    student = next((s for s in students if s['name'] == name), None)

    if request.method == 'POST':
        subject = request.form['subject']
        grades = request.form['grades']

        # Найти предмет и обновить
        for subj in student['subjects']:
            if subj['subject'] == subject:
                subj['grades'] = grades
                break
        else:
            student['subjects'].append({'subject': subject, 'grades': grades})

        save_json(STUDENTS_FILE, students)
        return redirect(url_for('teacher'))

    return render_template('edit_student.html', student=student)


# === КАБИНЕТ УЧЕНИКА ===
@app.route('/student')
def student():
    if 'user' not in session or session['user']['role'] != 'student':
        return redirect(url_for('login'))

    user = session['user']
    students = load_json(STUDENTS_FILE)
    student_info = next((s for s in students if s['name'] == user['username']), None)
    return render_template('student.html', student=student_info, user=user)


# === ВЫХОД ===
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
