-- Prerequisites--

1. Python 3 installed

2. PostgreSQL and psycopg2 installed

3. Create database name using pgAdmin: right click at Server/PostgreSQL/Databases and choose create database


-- How to install proper settings and run server to access web application. --

1. To activate virtual environment, move to the upper directory including env folder
then, command "source env/bin/activate" on Terminal.

2. To install dependencies, move to directory including "manage.py"
then, command "pip install -r requirements.txt" on Terminal.

3. Command "python manage.py makemigrations",then "python manage.py migrate".

4. To run Django local server, command "python manage.py runserver".

5. Once the server runs, type "http://127.0.0.1:8000/population/" on your browser to populate all raw data into Django model.
(Note: It would take long time around 12 mins, then it shows "Data Uploaded" on the page.)

6. Re-run the server. (It would take around 2 mins..)

7. Access the web application by typing "http://127.0.0.1:8000/main/" on your browser.


-- Configure database connector --

go to bitcoin_prediction/bitcoin_prediction/setting.py and replace the values inside DATABASES with your database details.