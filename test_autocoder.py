import pytest
import os
import json
from autocoder import AutoCoder  # assuming your class is in a file named gpt3_chat.py

class TestAutoCoder:
    @pytest.fixture
    def chat(self):
        api_key = 'your_openai_api_key'
        return AutoCoder(api_key,'test_code')

    def test_create_file_from_string(self, chat):
        file_path = 'test_code/test_file.txt'
        file_content = 'Hello, World!'
        chat.create_file_from_string(file_path, file_content)

        assert os.path.isfile(file_path)

        with open(file_path, 'r') as file:
            assert file.read() == file_content

    def test_modify_text_file(self, chat):
        file_path = 'test_code/test_file.txt'
        file_content = 'Hello\nWorld\n'
        chat.create_file_from_string(file_path, file_content)

        json_data = {
            "replace_line": {
                "2": "Earth\n"
            }
        }
        chat.modify_text_file(file_path, json_data)

        with open(file_path, 'r') as file:
            assert file.read() == 'Hello\nEarth\n'

    def test_read_file(self, chat):
        file_path = 'test_code/test_file.txt'
        file_content = 'Hello, World!'
        chat.create_file_from_string(file_path, file_content)

        assert chat.read_file(file_path) == file_content

    def test_list_files(self, chat):
        file_path = 'test_code/test_file.txt'
        file_content = 'Hello, World!'
        chat.create_file_from_string(file_path, file_content)

        assert 'test_file.txt' in chat.list_files('test_code')