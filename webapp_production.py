# --- webapp_production.py ---

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import assistant_core
import os, sys, json
from sqlalchemy import inspect as sql_inspect

# APP SETUP
def resource_path(relative_path):
    try: 
        base_path = sys._MEIPASS
    except Exception: 
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

app = Flask(__name__, template_folder=resource_path('templates'), static_folder=resource_path('static'))

# Production configuration
if getattr(sys, 'frozen', False): 
    application_path = os.path.dirname(sys.executable)
else: 
    application_path = os.path.dirname(os.path.abspath(__file__))

# Use environment variable for database URL in production
if os.environ.get('DATABASE_URL'):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
else:
    db_path = os.path.join(application_path, 'database.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

# Use environment variable for secret key in production
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a-very-secret-string-for-flask')

# Upload folder configuration
UPLOAD_FOLDER = os.path.join(application_path, 'uploads')
if not os.path.exists(UPLOAD_FOLDER): 
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# DATABASE MODELS
class User(UserMixin, db.Model): 
    id=db.Column(db.Integer, primary_key=True)
    email=db.Column(db.String(100), unique=True)
    password_hash=db.Column(db.String(200))
    conversations=db.relationship('Conversation', backref='user', cascade="all, delete-orphan")

class Conversation(db.Model): 
    id=db.Column(db.Integer, primary_key=True)
    title=db.Column(db.String(100), default='New Chat')
    user_id=db.Column(db.Integer, db.ForeignKey('user.id'))
    messages=db.relationship('Message', backref='conversation', cascade="all, delete-orphan")

class Message(db.Model): 
    id=db.Column(db.Integer, primary_key=True)
    sender=db.Column(db.String(10))
    text=db.Column(db.Text)
    is_long=db.Column(db.Boolean, default=False)
    conversation_id=db.Column(db.Integer, db.ForeignKey('conversation.id'))

@login_manager.user_loader
def load_user(user_id): 
    return db.session.get(User, int(user_id))

# AUTH & MAIN ROUTES
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: 
        return redirect(url_for('index'))
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form.get('email')).first()
        if user and check_password_hash(user.password_hash, request.form.get('password')): 
            login_user(user, remember=True)
            return redirect(url_for('index'))
        else: 
            flash('Invalid credentials.')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated: 
        return redirect(url_for('index'))
    if request.method == 'POST':
        if User.query.filter_by(email=request.form.get('email')).first(): 
            flash('Email already exists.')
            return redirect(url_for('signup'))
        new_user = User(
            email=request.form.get('email'), 
            password_hash=generate_password_hash(request.form.get('password'), method='pbkdf2:sha256')
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user, remember=True)
        return redirect(url_for('index'))
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout(): 
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index(): 
    return render_template('index.html')

# API ROUTES
@app.route('/api/conversations', methods=['GET', 'POST'])
@login_required
def handle_conversations():
    if request.method == 'POST': 
        new_convo = Conversation(user_id=current_user.id)
        db.session.add(new_convo)
        db.session.commit()
        return jsonify({'id': new_convo.id, 'title': new_convo.title})
    convos = Conversation.query.filter_by(user_id=current_user.id).order_by(Conversation.id.desc()).all()
    return jsonify([{'id': c.id, 'title': c.title} for c in convos])

@app.route('/api/conversations/<int:convo_id>', methods=['GET', 'DELETE'])
@login_required
def handle_single_conversation(convo_id):
    convo = db.session.get(Conversation, convo_id)
    if not convo or convo.user_id != current_user.id: 
        return jsonify({'error': 'Unauthorized'}), 403
    if request.method == 'DELETE': 
        db.session.delete(convo)
        db.session.commit()
        return jsonify({'success': True})
    messages = Message.query.filter_by(conversation_id=convo_id).order_by(Message.id.asc()).all()
    return jsonify([{'sender': m.sender, 'text': m.text, 'is_long': m.is_long} for m in messages])

# STREAMING ENDPOINT FOR SIMPLE CHAT
@app.route('/stream-command')
@login_required
def stream_command_route():
    command = request.args.get('command', '')
    convo_id = request.args.get('conversation_id')
    if not convo_id: 
        return Response("Error: Missing conversation ID", mimetype='text/event-stream')
    
    db.session.add(Message(sender='user', text=command, conversation_id=convo_id))
    db.session.commit()
    history = [{'role':'model' if m.sender=='assistant' else 'user', 'parts':[m.text]} for m in db.session.get(Conversation, convo_id).messages[-10:]]
    
    def generate():
        full_response_text = ""
        try:
            for chunk in assistant_core.stream_simple_command(history, command):
                yield f"data: {json.dumps(chunk)}\n\n"
                full_response_text += chunk
        finally:
            with app.app_context():
                is_long = len(full_response_text.split()) > 15
                db.session.add(Message(sender='assistant', text=full_response_text, is_long=is_long, conversation_id=convo_id))
                convo = db.session.get(Conversation, convo_id)
                if convo and convo.title == 'New Chat' and command: 
                    convo.title = command[:50]
                db.session.commit()
            yield "data: [DONE]\n\n"
    return Response(generate(), mimetype='text/event-stream')

# AGENTIC/FILE TASK ENDPOINT (NON-STREAMING)
@app.route('/process-command', methods=['POST'])
@login_required
def process_command_route():
    command = request.form.get('command', '')
    convo_id = request.form.get('conversation_id')
    response_text, is_long = "An unexpected error occurred.", False
    if not convo_id: 
        return jsonify({'error': 'Missing conversation ID'}), 400
    if not command and 'file' not in request.files: 
        return jsonify({'error': 'No command or file provided'}), 400
    
    user_message_text = command
    if 'file' in request.files and request.files['file'].filename != '':
        user_message_text = f"{command} [File: {request.files['file'].filename}]".strip()
    db.session.add(Message(sender='user', text=user_message_text, conversation_id=convo_id))
    db.session.commit()
    
    try:
        history = [{'role':'model' if m.sender=='assistant' else 'user', 'parts':[m.text]} for m in db.session.get(Conversation, convo_id).messages[-10:]]
        if 'file' in request.files and request.files['file'].filename != '':
            file = request.files['file']
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            response_generator = assistant_core.process_file_command(history, command, file_path)
            response_text = "".join(list(response_generator))
            if os.path.exists(file_path): 
                os.remove(file_path)
        else:
            response_text = assistant_core.execute_on_screen_task(command)

        if isinstance(response_text, str):
            is_long = len(response_text.split()) > 15
            db.session.add(Message(sender='assistant', text=response_text, is_long=is_long, conversation_id=convo_id))
            convo = db.session.get(Conversation, convo_id)
            if convo and convo.title == 'New Chat' and command: 
                convo.title = command[:50]
            db.session.commit()
            print(f"INFO: Successfully saved assistant response to DB: '{response_text[:50]}...'")
        else:
            response_text = "Received an invalid response from the core agent."
            print("ERROR: Non-string response.")
    except Exception as e:
        print(f"CRITICAL ERROR in /process-command: {e}")
        db.session.rollback()
    
    return jsonify({'response': response_text, 'is_long': is_long})

# HEALTH CHECK ENDPOINT
@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Application is running'})

# MAIN ENTRY POINT
def create_database_if_needed():
    with app.app_context():
        if not os.path.exists(db_path): 
            db.create_all()
            print("INFO: New database created.")
        else:
            inspector = sql_inspect(db.engine)
            if not inspector.has_table("user"): 
                db.create_all()
                print("INFO: DB file exists but tables not found. Creating.")
            else: 
                print("INFO: Database already exists.")

if __name__ == '__main__':
    if not assistant_core.initialize():
        print("Halting application due to API key initialization failure.")
        sys.exit(1)
    create_database_if_needed()
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 