
-- How to install proper settings and run server to access web application. --

1. To activate virtual environment, move to the upper directory including env folder
then, command "source env/bin/activate" on Terminal.

2. To install dependencies, move to directory including "manage.py"
then, command "pip install -r requirements.txt" on Terminal.

3. Command "python manage.py makemigrations",then "python manage.py migrate".

4. To run Django local server, commands "python manage.py runserver".

5. Access the web application by typing "http://127.0.0.1:8000/main/" on your browser.