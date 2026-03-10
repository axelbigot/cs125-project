# cs125-project

> Ensure you are running in a venv

1. `pip install -r requirements.txt`
2. `python manage.py migrate`
3. `python manage.py runserver`

App will be available at `localhost:8000`

> Seeing a Users Preferences

1. `python manage.py shell`
2. 
```python
from django.contrib.auth.models import User
from cs125_project.api.models import UserPreference

u = User.objects.get(username="youremail@example.com")
u.preferences.to_dict()
```