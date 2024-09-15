from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from googletrans import Translator
import bcrypt
import os

# Initialize Flask app
app = Flask(__name__)

# Configure the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'  # Add a secret key for session management (if needed)
db = SQLAlchemy(app)
translator = Translator()

# Define the User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def __init__(self, email, password, name):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

# Create database tables
with app.app_context():
    db.create_all()

    # Add a single user if not already present
    if not User.query.filter_by(email='bhuwan1@gmail.com').first():
        new_user = User(email='bhuwan1@gmail.com', password='123456789', name='Test User')
        db.session.add(new_user)
        db.session.commit()

# FAQ Data (in-memory for simplicity)
faq_data = []

# Chatbot Responses
def get_bot_response(user_input):
    responses = {
        "banana": "Bananas are a natural source of energy and contain high levels of potassium, which helps maintain heart health.",
        "mango": "Mangoes are known as the king of fruits and are rich in vitamins A and C.",
        "apple": "Apples come in over 7,500 varieties and are a great source of fiber and antioxidants",
        "default": "I'm not sure how to respond to that."
    }
    return responses.get(user_input.lower(), responses["default"])

# Routes

# Chat Route
@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message')
    
    if not user_input:
        return jsonify({'response': "I didn't receive a message!"})
    
    print(f"User input: {user_input}")  # Debugging: Ensure input is received
    bot_response = get_bot_response(user_input)
    print(f"Bot response: {bot_response}")  # Debugging: Ensure response is generated

    return jsonify({'response': bot_response})

# Render Chat Page
@app.route('/chat')
def chat_page():
    return render_template('chat.html')

# FAQ Routes
@app.route('/faq')
def faq_page():
    return render_template('faq.html', faqs=faq_data)

@app.route('/add_faq', methods=['POST'])
def add_faq():
    question = request.form.get('question')
    answer = request.form.get('answer')
    if question and answer:
        faq_data.append({'question': question, 'answer': answer})
    return redirect(url_for('faq_page'))

@app.route('/edit_faq/<int:index>', methods=['POST'])
def edit_faq(index):
    if 0 <= index < len(faq_data):
        updated_question = request.form.get('question')
        updated_answer = request.form.get('answer')
        faq_data[index]['question'] = updated_question
        faq_data[index]['answer'] = updated_answer
        return '', 200  # Successful edit
    return '', 400  # Bad request

@app.route('/delete_faq/<int:index>', methods=['GET'])
def delete_faq(index):
    if 0 <= index < len(faq_data):
        faq_data.pop(index)
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error'}), 400

# Home Route
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/home')
def home():
    return render_template('home.html')

# Login Route
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            return redirect(url_for('home'))  # Redirect to /home after login
        else:
            return render_template('login.html', error="Invalid credentials")  # Return error message

    return render_template('login.html')

# Translation Route
@app.route('/translate', methods=['GET', 'POST'])
def translate_page():
    translated_text = None
    if request.method == 'POST':
        text_to_translate = request.form['text_to_translate']
        target_language = request.form['language_pair']  # Get selected language pair from form

        if text_to_translate and target_language:
            try:
                translation = translator.translate(text_to_translate, dest=target_language)
                translated_text = translation.text
            except Exception as e:
                translated_text = f"Error: {str(e)}"
        
        return render_template('translate.html', original=text_to_translate, translated=translated_text, target_language=target_language)
    
    return render_template('translate.html')

# About Route
@app.route('/about')
def about():
    return render_template('about.html')

# Deployment Handling (Render.com)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Use dynamic port assignment for Render.com
    app.run(debug=False, host='0.0.0.0', port=port)
