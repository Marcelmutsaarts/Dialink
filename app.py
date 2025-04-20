from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import re # Nodig voor nl2br
from markupsafe import Markup # Correcte import voor Markup
from werkzeug.utils import secure_filename # Nodig voor veilige bestandsnamen
import uuid # Nodig voor unieke bestandsnamen
import json
from functools import wraps # Voor login_required decorator
from src.models import Post, Comment, User # We halen nu modellen uit src
from src.moderation import moderate_comment # En de moderatiefunctie
import datetime

app = Flask(__name__, template_folder='templates') # Explicitly set template folder
app.config['TEMPLATES_AUTO_RELOAD'] = True # Force template reloading
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'een-zeer-geheime-sleutel-voor-nu') # Gebruik env var of default

# Configuratie voor uploads
UPLOAD_FOLDER = 'static/uploads/posts'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Zorg dat de upload map bestaat
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Custom Filter --- 
def nl2br(value):
    """Converts newlines in a string to HTML breaks."""
    # Gebruik Markup om te zorgen dat de <br> tags niet worden ge-escaped
    return Markup(re.sub(r'\r\n|\r|\n', '<br>\n', value))

# Registreer het filter bij Jinja
app.jinja_env.filters['nl2br'] = nl2br

# --- JSON Data Handling ---
DATA_FILE = 'data.json'

# Globale variabelen voor data (worden gevuld door load_data)
users = []
posts = []

def load_data():
    global users, posts
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            users = [User.from_dict(u_data) for u_data in data.get('users', [])]
            posts = [Post.from_dict(p_data) for p_data in data.get('posts', [])]
            print(f"Data geladen: {len(users)} gebruikers, {len(posts)} posts")
    except FileNotFoundError:
        print("data.json niet gevonden, start met lege lijsten.")
        users = []
        posts = []
    except json.JSONDecodeError:
        print("Fout bij het lezen van data.json, start met lege lijsten.")
        users = []
        posts = []
    except Exception as e:
        print(f"Onverwachte fout bij laden data: {e}")
        users = []
        posts = []

def save_data():
    try:
        with open(DATA_FILE, 'w') as f:
            data_to_save = {
                'users': [u.to_dict() for u in users],
                'posts': [p.to_dict() for p in posts]
            }
            json.dump(data_to_save, f, indent=4)
            print("Data opgeslagen naar data.json")
    except Exception as e:
        print(f"Fout bij opslaan data: {e}")

# Laad data bij opstarten
load_data()

# Helper om user op ID te vinden
def find_user_by_id(user_id):
    return next((u for u in users if u.id == user_id), None)

# Helper om user op username te vinden
def find_user_by_username(username):
    return next((u for u in users if u.username.lower() == username.lower()), None)

# --- Helper Function to find comments recursively ---
def find_comment_by_id(comment_id: str, search_list: list[Comment]):
    """Recursively search for a comment by ID within a list and its replies."""
    for comment in search_list:
        if comment.id == comment_id:
            return comment
        found_in_replies = find_comment_by_id(comment_id, comment.replies)
        if found_in_replies:
            return found_in_replies
    return None

# --- Decorator voor login ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Je moet ingelogd zijn om deze pagina te bekijken.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Context Processor (om user info in alle templates beschikbaar te maken) ---
@app.context_processor
def inject_user():
    user_id = session.get('user_id')
    if user_id:
        return dict(current_user=find_user_by_id(user_id))
    return dict(current_user=None)

# --- Routes ---

@app.route('/')
def index():
    """Render de hoofdpagina met alle posts en comments."""
    # Sorteer posts van nieuw naar oud voor weergave
    sorted_posts = sorted(posts, key=lambda p: p.timestamp, reverse=True)
    # Haal gebruikersnamen op voor weergave
    users_dict = {u.id: u.username for u in users}
    return render_template('index.html', posts=sorted_posts, users=users_dict)

@app.route('/add_post', methods=['POST'])
@login_required # Nu beveiligd
def add_post():
    """Verwerk het formulier om een nieuwe post toe te voegen."""
    user_id = session['user_id'] # We weten dat deze bestaat door @login_required
    content = request.form.get('content')
    image_file = request.files.get('image') # Haal het image bestand op

    image_filename_to_save = None

    # Verwerk de afbeelding als deze is geüpload en toegestaan is
    if image_file and image_file.filename != '' and allowed_file(image_file.filename):
        # Genereer een veilige en unieke bestandsnaam
        original_filename = secure_filename(image_file.filename)
        extension = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}.{extension}"
        
        try:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            image_file.save(image_path)
            image_filename_to_save = unique_filename # Sla alleen de bestandsnaam op
            print(f"Afbeelding opgeslagen: {image_filename_to_save}")
        except Exception as e:
            print(f"Fout bij opslaan afbeelding: {e}")
            # Optioneel: geef een foutmelding aan de gebruiker

    # Maak de post aan (met of zonder afbeelding)
    if content:
        new_post = Post(user_id=user_id, content=content, image_filename=image_filename_to_save)
        posts.append(new_post)
        save_data() # Sla data op na toevoegen post
    else:
         flash('Post inhoud mag niet leeg zijn.', 'warning')
        
    return redirect(url_for('index'))

@app.route('/add_comment/<post_id>', methods=['POST'])
@login_required # Nu beveiligd
def add_comment(post_id):
    """Verwerkt het formulier om een comment toe te voegen (top-level of reply)."""
    user_id = session['user_id']
    original_content = request.form.get('content')
    parent_comment_id = request.form.get('parent_comment_id') # Nieuw: ID van parent comment (kan leeg zijn)

    target_post = next((p for p in posts if p.id == post_id), None)

    if not (original_content and target_post):
        flash('Kon reactie niet toevoegen.', 'danger')
        return redirect(url_for('index'))

    # Bepaal de context voor de moderator
    parent_comment = None
    previous_comments_context = [] # Dit wordt de context voor de AI
    if parent_comment_id:
        parent_comment = find_comment_by_id(parent_comment_id, target_post.comments)
        if parent_comment:
            # Context voor een reply: bouw de keten van replies op tot de top-level comment
            # Simpele versie: we nemen nu alle comments onder de post als context
            # TODO: Verfijn contextopbouw voor diepe replies indien nodig
            previous_comments_context = target_post.comments
        else:
            # Parent ID gegeven maar niet gevonden? Fout -> terug naar index
            print(f"Fout: Parent comment {parent_comment_id} niet gevonden.")
            flash('Kon niet reageren op de geselecteerde comment.', 'danger')
            return redirect(url_for('index'))
    else:
        # Top-level comment: context zijn alle bestaande top-level comments
        previous_comments_context = target_post.comments

    # Modereer de comment met context
    print(f"Originele reactie ontvangen voor post {post_id} (parent: {parent_comment_id}): {original_content}")
    print("Reactie wordt gemodereerd met context...")
    
    # Haal de user dictionary op (nodig voor usernames in context)
    users_dict = {u.id: u.username for u in users}
    
    moderated_content = moderate_comment(
        post_content=target_post.content,
        previous_comments=previous_comments_context,
        current_comment_text=original_content,
        users_dict=users_dict # Geef users_dict door
    )
    print(f"Gemodereerde reactie: {moderated_content}")

    # Maak de nieuwe comment
    new_comment = Comment(
        user_id=user_id,
        content=moderated_content,
        post_id=post_id,
        original_content=original_content,
        parent_comment_id=parent_comment_id if parent_comment else None
    )

    # Voeg de comment toe op de juiste plaats
    if parent_comment:
        parent_comment.add_reply(new_comment)
    else:
        # Voeg top-level comment toe aan de post lijst
        target_post.comments.append(new_comment)

    save_data() # Sla data op na toevoegen comment

    return redirect(url_for('index'))

# --- Authenticatie Routes ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session: # Al ingelogd? Ga naar home
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Gebruikersnaam en wachtwoord zijn verplicht.', 'danger')
            return redirect(url_for('register'))

        # Check of gebruikersnaam al bestaat
        if find_user_by_username(username):
            flash('Gebruikersnaam bestaat al.', 'warning')
            return redirect(url_for('register'))

        # Nieuwe gebruiker aanmaken en opslaan
        new_user = User(username=username, password=password)
        users.append(new_user)
        save_data() # Sla nieuwe gebruiker op
        
        flash('Registratie succesvol! Je kunt nu inloggen.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session: # Al ingelogd? Ga naar home
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = find_user_by_username(username)
        
        if user and user.check_password(password):
            session['user_id'] = user.id # Sla user ID op in sessie
            flash(f'Welkom terug, {user.username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Ongeldige gebruikersnaam of wachtwoord.', 'danger')
            return redirect(url_for('login'))
            
    return render_template('login.html')

@app.route('/logout', methods=['POST'])
@login_required # Moet ingelogd zijn om uit te loggen
def logout():
    session.pop('user_id', None) # Verwijder user ID uit sessie
    flash('Je bent succesvol uitgelogd.', 'info')
    return redirect(url_for('index'))

# --- Run de app ---
if __name__ == '__main__':
    # Gebruik een poort die waarschijnlijk vrij is
    port = int(os.environ.get('PORT', 5001))
    # Debug=True zorgt voor auto-reload en meer foutinformatie tijdens ontwikkeling
    app.run(debug=True, host='0.0.0.0', port=port) 