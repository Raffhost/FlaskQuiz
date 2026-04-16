from flask import Flask, render_template, request, session, redirect, url_for
from question import Question

app = Flask(__name__)
app.secret_key = 'secret'


# Home page — starts a new game
@app.route('/')
def index():
    questions = Question(db_name='questions.db').flaskQuiz(3)

    if not questions:
        return "No questions found", 404

    session['questions'] = [question.q_id for question in questions]
    session['score'] = 0
    session['current'] = 0

    return redirect(url_for('quiz'))


# Quiz page — shows current question
@app.route('/quiz')
def quiz():
    current = session.get('current', 0)
    questions = session.get('questions', [])

    if current >= len(questions):
        return redirect(url_for('result'))

    question = Question(db_name='questions.db').getQuestionById(questions[current])

    if not question:
        return redirect(url_for('index'))

    return render_template('index.html',
        question=question.q_text,
        answers=list(zip(question.answers, question.is_correct)),
        score=session['score'],
        current=current + 1,
        total=len(questions)
    )


# Handle answer submission
@app.route('/answer', methods=['POST'])
def answer():
    is_correct = request.form.get('is_correct')

    if is_correct == '1':
        session['score'] = session['score'] + 1

    session['current'] = session['current'] + 1
    session.modified = True

    return redirect(url_for('quiz'))


# Result page — shown when all questions are answered
@app.route('/result')
def result():
    score = session.get('score', 0)
    total = len(session.get('questions', []))
    return f"Done! Score: {score} / {total}"


if __name__ == '__main__':
    app.run(debug=True)