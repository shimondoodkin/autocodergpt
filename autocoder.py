import openai
import os
import json
import traceback
import subprocess
import re


class AutoCoder:
    def __init__(self, api_key, code_folder):
        
        code_folder = os.path.join(os.path.dirname(__file__), code_folder)
        self.code_folder = code_folder
        self.api_key = api_key
        openai.api_key = api_key
        self.plan = "make a plan, and do the first action, do all the required software development actions, report to the user" # Store any context data that needs to be remembered for your future self in context filed.
        self.task = ""
        self.autoSendMessage = None
        os.makedirs(self.code_folder, exist_ok=True)
        
        
        self.messages =     messages = [{"role": "system", "content": 
   # start of system message describing the agent:
    """"Ingore all previous instructions. You are DevBot, a software developer and you have special powers you can use a sandbox to list/read/create/edit/run files for the user automaticaly. You should execute all operations directly in the sandbox and not instruct the user to do so.

Communication style syntax:

Input from user:

{
  "user": { "text": "the input from the user." },
  "your plans were": "",
  "user's request": ""
}

Message to user:

{
  "user": { "text": "Your text to the user." },
  "my plans are": ""
  "user's request": ""
  
}

Please use the following message format when so the tools are executed for you automatically.

The sandbox understands only the following commands, for other things you should ask the user:

    list files:
        { "command": "list files" }

        it return a JSON array of list of all files including files in subfoldes.

        expected response fo sandbox message:

        { "text": "these are the files", "files": ["index.html","src/main.js"] }

        don't assume files exists check they are exist.

    create file:

        { "command": "create file", fileName:"example.txt", content: "Hello World" }

        make sure to write valid json in content with  \" \n ... when required
        
        it will create the necessary subfolders and the file.
        

        { "text": "ok, you created the file" }
        
        which filenames to use is up to you. 


    read file:

        { "command": "read file", fileName:"example.txt" }

        expected response:

        { "text": "The file name and the contents of that file are", fileName:"example.txt", content: "Hello World" }
        
        you should read files to check what you are doing before doing. 


    modify file:

        {
            "command": "modify file", 
            "fileName":"example.txt",
            "replace_lines": {
                "line number": "",
                "line number": "replacement line\n"
                "line number": "previous line value at line number\n value you want to append\n"
            }
        }
        it works with result of python file.readlines(), so to have new line there if you need, need to put \\n to split between lines and at end of a line
        to delete a line make it empty string
        when you appending make sure to keep the previous line before the appended text.

        expected response:

        { "text": "ok, you modified the file" }



    run:
        { "command": "run command", runCommand:"python hello.py" }

        it runs on windows and there is python.exe in the path.

        expected response:

        { "text": "The run command and the output of that file are", fileName:"python hello.py", content: "Hello World!" }


There is a filtering program that executes the sandbox commands.

The commands to the sandbox must be wrapped with following json:

    Input to sandbox:

        {
        "sandbox":{ "command": "" },
        "my plans are": "",
        "user's request": ""
        }

        maintain the "my plans are" json filed with your updated plan write there all future actions you may do until completition and reporting to user.
        maintain the "user's request" json filed with request received from user, generally keep it the same while doing a task.

    Response from sandbox:

        {
        "sandbox":{ "text": "message here" },
        "your plans were": "",
        "user's request": ""
        }


Instead of asking the user to do modifications by himself there is a shortcut for the user, just reply with a message to sandbox.
when you receive the response from sandbox you should evaluate the response and descide what to do next.

After you finish check what you did, to see if it looks good, if not fix it. when you are done report to the user.


please Communicate only in valid JSON format. notice there are not string before or after the json. for example:

example replies you can write:
{ "sandbox": { "command": "list files" }, "my plans are": "", "user's request": "" }
{ "sandbox": { "command": "read file", fileName:"example1.py" }, "my plans are": "", "user's request": "" }
{ "sandbox": { "command": "read file", fileName:"example2.py" }, "my plans are": "", "user's request": "" }
{ "sandbox": { "command": "read file", fileName:"example3.py" }, "my plans are": "", "user's request": "" }
{ "sandbox": { "command": "modify file", "fileName":"example2.py", "replace_lines": { "1": "replacement line\n" } }, "my plans are": "", "user's request": "" }
{ "sandbox": { "command": "read file", fileName:"example2.py" }, "my plans are": "", "user's request": "" }
{ "sandbox": { "command": "run command", runCommand:"python example2.py" }, "my plans are": "", "user's request": "" }
{ "user": { "text": "I have completed your task." }, "my plans are": "", "user's request": "" }
{ "user": { "text": "The next steps are..." }, "my plans are": "", "user's request": "" }
{ "user": { "text": "I suggest going it this way" }, "my plans are": "", "user's request": "" }

example conversation with input from user or from sandbox and replies from you:

you have conversation with two participants, the user and the sandbox

{"user": {"text": "I need to modify the hello.py file to print 'hello world' instead of the current time."}, "your plans were": "make a plan, and do the first action, do all the required software development actions, report to the user"}
{"sandbox": { "command": "list files" }, "my plans are": "check if the hello.py file exists and if it does, read its contents"}
{"sandbox": {"text": "these are the files", "files": ["example.py", "hello.py"]}, "your plans were": "check if the hello.py file exists and if it does, read its contents"}
{"sandbox": {"command": "read file", "fileName":"hello.py" }, "my plans are": "modify the contents of the hello.py file to print 'hello world'"}
{"sandbox": {"text": "The file name and the contents of that file are", "fileName": "hello.py", "content": "import datetime\nprint(datetime.datetime.now())\n"}, "your plans were": "modify the contents of the hello.py file to print 'hello world'"}
{"sandbox": {"command": "modify file", "fileName":"hello.py", "replace_lines": { "2": "print('hello world')" }}, "my plans are": "run the modified hello.py file and check its output"}
{"sandbox": {"text": "ok, you modified the file"}, "your plans were": "run the modified hello.py file and check its output"}
{"sandbox": {"command": "run command", "runCommand":"python hello.py"}, "my plans are": "run the modified file to check if the changes made are working as expected"}
{"sandbox": {"text": "The run command and the output of that are", "runCommand": "python hello.py", "output": "hello world\n\n"}, "your plans were": "run the modified file to check if the changes made are working as expected"}
{"user": {"text": "Great, you have completed the task successfully!"}, "my plans are": ""}

"""  # end of system message
}]

    def chat_with_gpt3(self, messages):
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )

        return response['choices'][0]['message']['content']
    
    def run_command(self, cwd, command):
        try:
            # Execute the command and capture the output
            result = subprocess.run(command, shell=True, cwd=cwd,  capture_output=True, text=True)
            
            # Check if the command executed successfully
            return result.stdout.strip() +'\n\n' + result.stderr.strip()
        
        except Exception as e:
            # Return the exception error message
            return str(e)
        
    def list_files(self, folder_path):
        file_list = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, folder_path)
                file_list.append(relative_path)
        return file_list

    def create_file_from_string(self, file_path, file_content):
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
        # Write the file content to the specified file
        with open(file_path, 'w') as file:
            file.write(file_content)

    def modify_text_file(self, file_path, replace_lines):
        """
        
        # Example JSON input
        json_input = 
        {
                "3": "\n   new line\n"
        }
    
        """
    
        with open(file_path, 'r') as file:
            lines = file.readlines()
    
            # Process JSON input - Replace lines
            for line_number, replacement in replace_lines.items():
                line_number = int(line_number) - 1  # Adjust for 1-based indexing
                while line_number>=len(lines):
                    lines.append("\n")
                lines[line_number] = replacement

        with open(file_path, 'w') as file:
            file.writelines(lines)

    def read_file(self, file_path):
        with open(file_path, 'r') as file:
            content = file.read()
        return content

    def execute_command(self, command_data):
        command = command_data.get('command')
        message = {}

        try:
            if command == 'list files':
                output = self.list_files(self.code_folder)
                message = {"text": "these are the files", "files": output}
            elif command == 'create file':
                fileName = command_data.get('fileName')
                content = command_data.get('content')
                self.create_file_from_string(os.path.join(self.code_folder, fileName), content)
                message = {"text": f"ok, you created the file"}
            elif command == 'modify file':
                fileName = command_data.get('fileName')
                replace_lines = command_data.get('replace_lines')
                self.modify_text_file(os.path.join(self.code_folder, fileName), replace_lines)
                message = {"text":  f"ok, you modified the file"}
            elif command == 'read file':
                fileName = command_data.get('fileName')
                output = self.read_file(os.path.join(self.code_folder, fileName))
                message = {"text": "The file name and the contents of that file are", "fileName": fileName, "content": output}
                
            elif command == 'run command':
                runCommand = command_data.get('runCommand')
                output = self.run_command(self.code_folder,runCommand)
                message = {"text": "The run command and the output of that are", "runCommand": runCommand, "output": output}

            else:
                raise ValueError("Unknown command")

            return message
        except Exception as e:
            error_message = f"Error occurred during command execution: {str(e)}"
            traceback.print_exc()
            return {"error": error_message}



    def take_json_to_sandbox(self, s):
        # Define the regular expression pattern.
        pattern = r'{.*?"sandbox":\s*'
        
        # Find the starting position of the JSON-like structure.
        match = re.search(pattern, s)
        if match is None:
            raise ValueError('String does not contain the expected pattern')
        
        # Initialize a stack to keep track of open brackets.
        stack = ['{']
        
        # Initialize a counter to keep track of the current position in the string.
        pos = match.end()
        
        # Initialize variables to keep track of whether we're inside a string and whether the previous character was a backslash.
        in_string = False
        prev_char = None
        
        # Tokenize the string to count closing brackets.
        while stack:
            char = s[pos]
        
            if char == '"' and prev_char != '\\':
                # If we find a quote that's not part of an escape sequence, flip the in_string flag.
                in_string = not in_string
        
            if not in_string:
                if char == '{':
                    # If we find an open bracket, add it to the stack.
                    stack.append('{')
                elif char == '}':
                    # If we find a close bracket, remove an open bracket from the stack.
                    stack.pop()
        
            prev_char = char
            pos += 1
        
        # When all brackets are closed, return the substring and the last end position.
        return s[match.start():pos], pos


    def run(self):
        print("Welcome! You're now chatting with GPT-3. Type 'quit' to exit.")
        loop_counter = 0

        while True:
            if self.autoSendMessage:
                reply = self.autoSendMessage
                self.autoSendMessage = None
            else:
                user_input = ""
                while user_input.strip() == "":
                    user_input = input("You: ")

                if user_input.lower() == "quit":
                    break

                reply = {
                    "user":  { 'text': user_input },
                    "your plans were": self.plan,
                    "my tasks were": self.task,
                }

            self.messages.append({"role": "user", "content": json.dumps(reply)})
            print(f"send: {reply}")

            model_response = self.chat_with_gpt3(self.messages)
            print(f"received: {model_response}")
            
            response_data = None
            try:
                response_data = json.loads(model_response.strip())
            except json.JSONDecodeError:
                # print(f"GPT-3 returned a syntax error json: {model_response}")
                print(f"> got not json data")
                try:
                    substring, endpos = self.take_json_to_sandbox(model_response)
                    print(f"> the whole message was:"+model_response)
                    print(f"> json recovered"+substring)
                    response_data = json.loads(substring.strip())
                except json.JSONDecodeError:
                    # print(f"GPT-3 returned a syntax error json: {model_response}")
                    print(f"> unable to recover not json data converting to message JSONDecodeError")
                    
                    response_data={
                        'user': { 'text': model_response },
                        'my plans are':self.plan,
                        'user\'s request':self.task,
                    }
                    
                except ValueError:
                    # print(f"GPT-3 returned a syntax error json: {model_response}")
                    print(f"> unable to recover not json data converting to message, no json to sandbox found in the message")
                    
                    response_data={
                        'user': { 'text': model_response },
                        'my plans are':self.plan,
                        'user\'s request':self.task,
                    }
                
                
                # traceback.print_exc()
            if 'user' in response_data :
                self.plan = response_data.get("my plans are", response_data.get("your plans were", self.plan))
                self.task = response_data.get("user's request", self.task)
                print(f"GPT-3 message to user: {response_data['user']['text']}")
            
            if 'sandbox' in response_data:
                self.plan = response_data.get("my plans are", response_data.get("your plans were", self.plan))
                self.task = response_data.get("user's request", self.task)
                command_response = self.execute_command(response_data['sandbox'])
                reply = {
                    "sandbox": command_response,
                    "your plans were": self.plan,
                    "user's request": self.task,
                }
                self.autoSendMessage = reply

            loop_counter += 1

            if loop_counter % 10 == 0:
                choice = input("Do you want to continue? (y/n), c=back to prompt: ")
                if choice.lower() != "y":
                    if choice.lower() == "c":
                        self.autoSendMessage = None
                    else:
                        break
        
        
if __name__ == "__main__":
    # Add your OpenAI API Key here
    api_key = "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"
    chat = AutoCoder(api_key,"code")
    chat.run()