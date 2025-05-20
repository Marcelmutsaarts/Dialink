import unittest
import re
import json # For load_data tests
from unittest.mock import patch, mock_open # For load_data tests
from markupsafe import Markup, escape

# --- Replicated nl2br function from app.py ---
def nl2br(value):
    """Converts newlines in a string to HTML breaks after escaping HTML."""
    if not isinstance(value, str):
        value = str(value)
    escaped_value = escape(value)
    return Markup(re.sub(r'\r\n|\r|\n', '<br>\n', escaped_value))

class TestNl2brFilter(unittest.TestCase):
    def test_nl2br_escapes_html_and_converts_newlines(self):
        test_input = "<script>alert('XSS')</script>\nHello\r\nWorld\rEnd"
        expected_output_str = "&lt;script&gt;alert(&#39;XSS&#39;)&lt;/script&gt;<br>\nHello<br>\nWorld<br>\nEnd"
        result = nl2br(test_input)
        self.assertEqual(str(result), expected_output_str)
        self.assertIsInstance(result, Markup)

    def test_nl2br_with_non_string_input(self):
        test_input = 123
        expected_output_str = "123"
        result = nl2br(test_input)
        self.assertEqual(str(result), expected_output_str)
        self.assertIsInstance(result, Markup)

    def test_nl2br_with_string_containing_no_html_or_newlines(self):
        test_input = "Just a plain string."
        expected_output_str = "Just a plain string."
        result = nl2br(test_input)
        self.assertEqual(str(result), expected_output_str)
        self.assertIsInstance(result, Markup)

    def test_nl2br_with_only_newlines(self):
        test_input = "\n\r\n\r"
        expected_output_str = "<br>\n<br>\n<br>\n"
        result = nl2br(test_input)
        self.assertEqual(str(result), expected_output_str)
        self.assertIsInstance(result, Markup)

    def test_nl2br_with_empty_string(self):
        test_input = ""
        expected_output_str = ""
        result = nl2br(test_input)
        self.assertEqual(str(result), expected_output_str)
        self.assertIsInstance(result, Markup)

# --- For load_data tests: Replicated/Simplified Models and Globals ---
DATA_FILE = 'data.json' # Used by load_data
users = []
posts = []

# Simplified User and Post classes for testing load_data
class User:
    def __init__(self, id, username):
        self.id = id
        self.username = username

    @staticmethod
    def from_dict(data):
        # In a real scenario, this would do more validation/mapping
        return User(data.get('id'), data.get('username'))

class Post:
    def __init__(self, id, content):
        self.id = id
        self.content = content

    @staticmethod
    def from_dict(data):
        # In a real scenario, this would do more validation/mapping
        return Post(data.get('id'), data.get('content'))

# Replicated load_data function from app.py
def load_data():
    global users, posts # Make sure we're modifying the global ones defined in this test file
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            # Use the User and Post classes defined in this test file
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
    except Exception as e: # Generic catch-all
        print(f"Onverwachte fout bij laden data: {e}")
        users = []
        posts = []


class TestDataLoading(unittest.TestCase):
    def setUp(self):
        # Reset global state before each test
        global users, posts
        users = []
        posts = []

    @patch('builtins.print') # Mock print to capture its output
    @patch('builtins.open', side_effect=FileNotFoundError) # Mock open to raise FileNotFoundError
    def test_load_data_file_not_found(self, mock_open, mock_print):
        load_data()
        mock_print.assert_any_call("data.json niet gevonden, start met lege lijsten.")
        self.assertEqual(users, [])
        self.assertEqual(posts, [])

    @patch('builtins.print')
    @patch('json.load', side_effect=json.JSONDecodeError("Syntax error", "doc", 0))
    @patch('builtins.open', new_callable=mock_open, read_data="invalid json data")
    def test_load_data_json_decode_error(self, mock_file_open, mock_json_load, mock_print):
        load_data()
        mock_print.assert_any_call("Fout bij het lezen van data.json, start met lege lijsten.")
        self.assertEqual(users, [])
        self.assertEqual(posts, [])

    @patch('builtins.print')
    # Mock User.from_dict and Post.from_dict to just return the input dict for simplicity in this test
    # This way we don't need to worry about the exact structure of User/Post objects, just that they are created
    @patch('tests.test_app.User.from_dict', side_effect=lambda d: d) 
    @patch('tests.test_app.Post.from_dict', side_effect=lambda d: d)
    def test_load_data_success(self, mock_post_from_dict, mock_user_from_dict, mock_print):
        sample_data = {
            "users": [{"id": "u1", "username": "testuser"}],
            "posts": [{"id": "p1", "content": "test post"}]
        }
        # Mock open to return a file-like object with the sample data
        with patch('builtins.open', mock_open(read_data=json.dumps(sample_data))) as mock_file:
            load_data()

        mock_print.assert_any_call("Data geladen: 1 gebruikers, 1 posts")
        self.assertEqual(len(users), 1)
        self.assertEqual(len(posts), 1)
        # Check if from_dict was called with the correct data
        mock_user_from_dict.assert_called_with({"id": "u1", "username": "testuser"})
        mock_post_from_dict.assert_called_with({"id": "p1", "content": "test post"})
        # Check the content of global users/posts (which now store the dicts due to side_effect)
        self.assertEqual(users[0], {"id": "u1", "username": "testuser"})
        self.assertEqual(posts[0], {"id": "p1", "content": "test post"})


if __name__ == '__main__':
    unittest.main()
