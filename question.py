import sqlite3
global db_name
db_name = 'questions.db'


class CreateDB:
    def __init__(self):
        self.connection = sqlite3.connect(db_name)
        cursor = self.connection.cursor()

        # Create table for question types
        cursor.execute('''CREATE TABLE IF NOT EXISTS question_type (
                       question_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
                       question_type STRING
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


class Question:
    def __init__(self, question_id=None, question_text="", question_type="", answers=[], is_correct=[]):
        self.q_id = question_id
        self.q_text = question_text
        self.q_type = question_type
        self.answers = answers
        self.is_correct = is_correct
        self.current_index = 0

    def loadQuestion(self, filename):
        self.connection = sqlite3.connect(db_name)
        cursor = self.connection.cursor()

        with open(filename, encoding='utf-8') as file:
            group = []  # Buffer to hold lines of the same question
            for line in file:
                line = line.strip()
                if not line or line.startswith('question_id'):
                    continue

                parts = line.split(';')
                if len(parts) != 5:
                    continue
                
                q_id = int(parts[0])
                

                if group and int(group[0][0]) != q_id:
                    self.insertQuestion(cursor, group) # Process the previous question group
                    group = [] # Start a new group for the next question
                
                group.append(parts)  # Добавляем строку в буфер
            
            if group:
                self.insertQuestion(cursor, group) # Process the last question group

        self.connection.commit()


    def insertQuestion(self, cursor, group):
        # Assuming all lines in the group have the same id, text and type
        q_text = group[0][1]  # Question text (same for all 4 lines)
        q_type = group[0][2]  # Question type (same for all 4 lines)
        
        answers = [parts[3] for parts in group]  # 4 answers
        is_correct_flags = [parts[4].strip().lower() == 'true' for parts in group]  # 4 flags
        
        # Insert question_type
        cursor.execute('''SELECT question_type_id FROM question_type 
                       WHERE question_type = ?;''', (q_type,))
        result = cursor.fetchone()
        if result:
            q_type_id = result[0]
        else:
            cursor.execute('INSERT INTO question_type (question_type) VALUES (?);', (q_type,))
            q_type_id = cursor.lastrowid
        
        # Insert question
        cursor.execute('INSERT INTO question (question, question_type_id) VALUES (?, ?);', (q_text, q_type_id))
        question_id = cursor.lastrowid
        
        # Insert all 4 answers at once
        for answer, is_correct in zip(answers, is_correct_flags):
            cursor.execute('INSERT INTO answer (answer, is_correct, question_id) VALUES (?, ?, ?);', 
                        (answer, is_correct, question_id))

    def getQuestion(self, q_id):
        self.connection = sqlite3.connect(db_name)
        cursor = self.connection.cursor()

        # Load question and answers from database
        cursor.execute('''SELECT question_id, question, question_type, answer, is_correct 
                       FROM question INNER JOIN answer USING (question_id)
                       INNER JOIN question_type USING (question_type_id)
                       WHERE question_id = ?;''', (q_id,))
        data = cursor.fetchall()

        if not data:
            return None

        q_text = data[0][1]
        q_type = data[0][2]
        answers = [row[3] for row in data]
        is_correct = [row[4] for row in data]

        return Question(
            question_id=q_id,
            question_text=q_text,
            question_type=q_type,
            answers=answers,
            is_correct=is_correct
        )
    



def main():
    CreateDB()
    q = Question()
    q.loadQuestion('questions.csv')
    q.getQuestion(1)

if __name__ == "__main__":
    main()


### GONNA FINISH THIS LATER ###