import sqlite3


class Question:
    def __init__(self, question_id=None, question_text="",
                 question_type="", answers=[], is_correct=[],
                 db_name='questions.db'):
        self.q_id = question_id
        self.q_text = question_text
        self.q_type = question_type
        self.answers = answers
        self.is_correct = is_correct
        self.current_index = 0
        self.db_name = db_name


    def createQuestionDB(self):
        self.connection = sqlite3.connect(self.db_name)
        cursor = self.connection.cursor()

        # Clear existing data before loading
        cursor.execute('DROP TABLE IF EXISTS answer;')
        cursor.execute('DROP TABLE IF EXISTS question;')
        cursor.execute('DROP TABLE IF EXISTS question_type;')

        # Create table for question types
        cursor.execute('''CREATE TABLE IF NOT EXISTS question_type (
                       question_type_id INTEGER PRIMARY KEY,
                       question_type STRING UNIQUE
                       );''')

        # Create table for questions
        cursor.execute('''CREATE TABLE IF NOT EXISTS question (
                       question_id INTEGER PRIMARY KEY AUTOINCREMENT,
                       question STRING,
                       question_type_id INTEGER,
                       FOREIGN KEY (question_type_id) 
                       REFERENCES question_type(question_type_id)
                       );''')

        # Create table for answers
        cursor.execute('''CREATE TABLE IF NOT EXISTS answer (
                       answer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                       answer STRING,
                       is_correct BOOLEAN,
                       question_id INTEGER,
                       FOREIGN KEY (question_id) 
                       REFERENCES question(question_id)
                       );''')
        
        self.connection.commit()
        self.connection.close()


    def loadQuestion(self, filename):
        with open(filename, encoding='utf-8') as file:
            current_id = None
            group = []  # Buffer to hold lines of the same question
            for line in file:
                
                # Strip whitespaces and skip empty lines or header
                line = line.strip()
                if not line or line.startswith('question_id'): 
                    continue

                # Split line into parts and check if its valid
                parts = line.split(';')
                if len(parts) != 5:
                    continue

                # Extract id f
                q_id = parts[0]

                # If None, set q_id as current_id
                if current_id is None:
                    current_id = q_id
                
                # If q_id changes, insert question and answers into database
                if q_id != current_id:
                    self.insertQuestion(
                        q_text = group[0][1],
                        q_type = group[0][2],
                        answers =  [row[3] for row in group],
                        is_correct = [row[4] for row in group]
                    )
                    group = []  # Clear buffer for next question
                    current_id = q_id  # Update current_id to new q_id

                group.append(parts)  # Add current line to buffer
            
            # Last question
            if group:
                self.insertQuestion(
                    q_text = group[0][1],
                    q_type = group[0][2],
                    answers =  [row[3] for row in group],
                    is_correct = [row[4] for row in group]
                )


    def insertQuestion(self, q_text, q_type, answers, is_correct):
        self.connection = sqlite3.connect(self.db_name)
        cursor = self.connection.cursor()

        # Insert q_type if it doesn't exist
        cursor.execute('''INSERT OR IGNORE INTO question_type 
                       (question_type) VALUES (?);''', (q_type,))
        
        # Get the q_type_id for next insertion
        cursor.execute('''SELECT question_type_id FROM question_type 
                       WHERE question_type = ?;''', (q_type,))
        question_type_id = cursor.fetchone()[0]

        # Insert q_text if it doesn't exist and q_type_id
        cursor.execute('''INSERT INTO question (question, question_type_id) 
                       VALUES (?, ?);''', (q_text, question_type_id))
        
        # Get the question_id for next insertion
        question_id = cursor.lastrowid

        # Insert answers with is_correct and question_id
        for answer, correct in zip(answers, is_correct):
            cursor.execute('''INSERT INTO answer (answer, is_correct, question_id) 
                           VALUES (?, ?, ?);''', (answer, correct, question_id))
        self.connection.commit()


    def getQuestionById(self, q_id):
        self.connection = sqlite3.connect(self.db_name)
        cursor = self.connection.cursor()

        # Load question and answers from database
        cursor.execute('''SELECT question_id, question, question_type, answer, is_correct 
                       FROM question INNER JOIN answer USING (question_id)
                       INNER JOIN question_type USING (question_type_id)
                       WHERE question_id = ?;''', (q_id,))
        rows = cursor.fetchall()

        if not rows:
            return None
        
        self.q_id=rows[0][0]
        self.q_text=rows[0][1]
        self.q_type=rows[0][2]
        self.answers=[row[3] for row in rows]
        self.is_correct=[row[4] == 'True' for row in rows]
        self.current_index=q_id

        return self


    def getQuestionsByTypeId(self, q_type_id):
        self.connection = sqlite3.connect(self.db_name)
        cursor = self.connection.cursor()

        # Load question type and question ids from database
        cursor.execute('''SELECT question_id, question FROM question
                       WHERE question_type_id = ?;''', (q_type_id,))
        rows = cursor.fetchall()

        if not rows:
            return None
        
        return "\n".join(f"{row[0]} {row[1]}" for row in rows)
        
    def createRandomOrder(self, q_type_id):
        self.connection = sqlite3.connect(self.db_name)
        cursor = self.connection.cursor()

        cursor.execute('''SELECT question_id FROM question
                       WHERE question_type_id = ?
                       ORDER BY RANDOM();''', (q_type_id,))
        random_order = cursor.fetchall()

        return random_order

    def getRandomQuestion(self, q_type_id):
        self.connection = sqlite3.connect(self.db_name)
        cursor = self.connection.cursor()

        cursor.execute('''SELECT question_id FROM question
                       WHERE question_type_id = ?
                       ORDER BY RANDOM() LIMIT 1;''', (q_type_id,))
        random_q_id = cursor.fetchone()

        if not random_q_id:
            return None

        question = self.getQuestionById(random_q_id[0])
  
        return question

    def flaskQuiz(self, q_type_id):
        # random_order = [q_id, q_text, q_type, answer, is_correct ]
        random_order = self.createRandomOrder(q_type_id) 

        if not random_order:
            return None

        questions = []
        for (q_id,) in random_order:
            question = Question(db_name=self.db_name).getQuestionById(q_id)
            
            if question:
                questions.append(question)
        
        return questions
    

def main(): # Create DB and load data
    q = Question(db_name='questions.db')
    q.createQuestionDB()
    q.loadQuestion('questions.csv')
    
def test_1(): # Test for getQuestionById
    q = Question(db_name='questions.db')
    test_q = q.getQuestionById(2)
    if test_q:
        print(f"Question ID: {test_q.q_id}")
        print(f"Text: {test_q.q_text}")
        print(f"Type: {test_q.q_type}")
        print(f"Answers: {test_q.answers}")
        print(f"Correct: {test_q.is_correct}")
    else:
        print("Question not found")

def test_2(): # Test for getQuestionByTypeId
    q = Question(db_name='questions.db')
    test_q = q.getQuestionsByTypeId(3)
    print(test_q)

def test_3(): # Test for createRandomOrder
    q = Question(db_name='questions.db')
    test_q = q.createRandomOrder(4)
    print(test_q)

def test_4(): # Test for flaskQuiz
    q = Question(db_name='questions.db')
    test_q = q.flaskQuiz(3)
    if test_q:
        for question in test_q:
            print(f"Question ID: {question.q_id}")
            print(f"Text: {question.q_text}")
            print(f"Type: {question.q_type}")
            print(f"Answers: {question.answers}")
            print(f"Correct: {question.is_correct}")
        else:
            print("Question not found")

def test_5(): # Test for getRandomQuestion
    q = Question(db_name='questions.db')
    q.getRandomQuestion(4)
    
    print(f"Question ID: {q.q_id}")
    print(f"Text: {q.q_text}")
    print(f"Type: {q.q_type}")
    print(f"Answers: {q.answers}")
    print(f"Correct: {q.is_correct}")




if __name__ == "__main__":
    main()
    test_5()


### Finished flask, now need to do the choice thing for every question type and other stuff ###