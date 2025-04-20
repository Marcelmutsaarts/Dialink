import datetime
import uuid
from werkzeug.security import generate_password_hash, check_password_hash

class User:
    def __init__(self, username, password):
        self.id = str(uuid.uuid4())
        self.username = username
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Helper om user om te zetten naar dict voor JSON opslag
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "password_hash": self.password_hash
        }

    # Helper om user te laden vanuit dict (JSON)
    @staticmethod
    def from_dict(data):
        user = User(username=data['username'], password='') # Dummy password, hash is al gezet
        user.id = data['id']
        user.password_hash = data['password_hash']
        return user

class Post:
    def __init__(self, user_id: str, content: str, image_filename: str = None):
        self.id = str(uuid.uuid4())
        self.user_id = user_id # Veranderd van user naar user_id
        self.content = content
        self.image_filename = image_filename # Nieuw veld voor afbeelding
        self.timestamp = datetime.datetime.now()
        self.comments = []

    def __str__(self):
        return f"Post van {self.user_id} ({self.timestamp}):\n{self.content}"

    # Helper om post om te zetten naar dict voor JSON opslag (incl. comments)
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "content": self.content,
            "image_filename": self.image_filename,
            "timestamp": self.timestamp.isoformat(), # Sla op als ISO string
            "comments": [c.to_dict() for c in self.comments]
        }

    # Helper om post te laden vanuit dict (JSON)
    @staticmethod
    def from_dict(data):
        post = Post(user_id=data['user_id'], content=data['content'], image_filename=data.get('image_filename'))
        post.id = data['id']
        post.timestamp = datetime.datetime.fromisoformat(data['timestamp'])
        post.comments = [Comment.from_dict(c_data) for c_data in data['comments']]
        return post

class Comment:
    def __init__(self, user_id: str, content: str, post_id: str, original_content: str = None, parent_comment_id: str = None):
        self.id = str(uuid.uuid4()) # Unique ID for the comment itself
        self.post_id = post_id # ID of the post this comment belongs to
        self.parent_comment_id = parent_comment_id # ID of the comment this is a reply to (None for top-level)
        self.user_id = user_id # Veranderd van user naar user_id
        self.original_content = original_content if original_content is not None else content
        self.moderated_content = content
        self.timestamp = datetime.datetime.now()
        self.replies = [] # List to hold nested replies (Comment objects)

    def add_reply(self, reply: 'Comment'):
        self.replies.append(reply)

    def __str__(self):
        prefix = "[Dialoog] " if self.original_content != self.moderated_content else ""
        return f"{prefix}Reactie van {self.user_id} ({self.timestamp}):\n{self.moderated_content}"

    # Helper om comment om te zetten naar dict voor JSON opslag (incl. replies)
    def to_dict(self):
        return {
            "id": self.id,
            "post_id": self.post_id,
            "parent_comment_id": self.parent_comment_id,
            "user_id": self.user_id,
            "original_content": self.original_content,
            "moderated_content": self.moderated_content,
            "timestamp": self.timestamp.isoformat(),
            "replies": [r.to_dict() for r in self.replies]
        }

    # Helper om comment te laden vanuit dict (JSON)
    @staticmethod
    def from_dict(data):
        comment = Comment(
            user_id=data['user_id'],
            content=data['moderated_content'], # Start met gemodereerde content
            post_id=data['post_id'],
            original_content=data['original_content'],
            parent_comment_id=data.get('parent_comment_id') # Gebruik .get() voor optioneel veld
        )
        comment.id = data['id']
        comment.timestamp = datetime.datetime.fromisoformat(data['timestamp'])
        comment.replies = [Comment.from_dict(r_data) for r_data in data['replies']]
        return comment 