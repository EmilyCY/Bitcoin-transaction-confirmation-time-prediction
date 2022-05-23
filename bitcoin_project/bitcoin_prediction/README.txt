-- Prerequisites--

1. Python 3 installed

2. PostgreSQL and psycopg2 installed 
 
-- How to install proper settings and run server to access web application. --

1. Install the vitrual envirnment using command "pip install virtualenv". Make a virtual environment using
command "virtualenv “name as you like”" 

2. To activate virtual environment, move to the upper directory including env folder
then, command "source env/bin/activate" on Terminal.

3. Install Django using command "pip install django"

4. To install dependencies, move to directory including "manage.py"
then, command "pip install -r requirements.txt" on Terminal.

5. Command "python manage.py makemigrations",then "python manage.py migrate".

6. To run Django local server, commands "python manage.py runserver".

7. Access the web application by typing "http://127.0.0.1:8000/main/" on your browser.

-- Configure database connector --

go to bitcoin_prediction/bitcoin_prediction/setting.py and replace the values inside DATABASES with your database
details.  