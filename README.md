# Online Quiz Platform

##### Requiremnts : 
* Python3 
* Github Desktop or Git 

##### Usage : 

               git clone https://github.com/amrinam3/Django-Quiz-Project.git
               cd Django-Quiz-Project
               pip install -r requirements.txt
               python manage.py migrate
               python manage.py runserver


Now go to **127.0.0.1:8000**  from your browser 

##### Completed Tasks : 
* Homepage
* User Authentication
* Session Management
* Data Model
* Data Model Register with Admin
* Login with SMS
* HTML For Check Output from Database
* Required Forms Added
* Proper UI Implemented
* Profile Creation & View
* Exam Creation
* Exam Enrollment
* History of Exams
* Send feedback about Questions
* Show Results
* Searching Feature
* Password Changing System
* Full Exam Results Log (Examinee & Examiner)
* And so ...


## How to Install and Run this project?

### Pre-Requisites:
1. Install Git Version Control
[ https://git-scm.com/ ]

2. Install Python Latest Version
[ https://www.python.org/downloads/ ]

3. Install Pip (Package Manager)
[ https://pip.pypa.io/en/stable/installing/ ]

*Alternative to Pip is Homebrew*

### Installation
**1. Create a Folder where you want to save the project**

**2. Create a Virtual Environment and Activate**

Install Virtual Environment First
```
$  pip install virtualenv
```

Create Virtual Environment

For Windows
```
$  python -m venv venv
```
For Mac
```
$  python3 -m venv venv
```

Activate Virtual Environment

For Windows
```
$  source venv/scripts/activate
```

For Mac
```
$  source venv/bin/activate
```

**3. Clone this project**
```
$  git clone https://github.com/arminam3/Django-Shop.git
```

Then, Enter the project
```
$  cd django-shop
```

**4. Install Requirements from 'requirements.txt'**
```python
$  pip install -r requirements.txt
```

**5. Add the hosts**

- Got to settings.py file 
- Then, On allowed hosts, Add [‘*’]. 
```python
ALLOWED_HOSTS = ['*']
```
*No need to change on Mac.*


**6. Now Run Server**

Command for PC:
```python
$ python manage.py runserver
```

Command for Mac:
```python
$ python3 manage.py runserver
```

**7. Login Credentials**

Create Super User (Admin)

Command for PC:
```
$  python manage.py createsuperuser
```

Command for MAC:
```
$  python3 manage.py createsuperuser
```
Then Add Email, Username and Password

