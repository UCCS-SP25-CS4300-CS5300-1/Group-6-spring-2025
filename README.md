# Group-6-spring-2025
## Github Workflow
In order to try and imitate a proper environment we will utilize this type of workflow in terms of branches. main will be untouched and will be the production environment to ensure that during development no issues are automatically propogated to the production side. So off of the main branch we will use the dev branch. Any issues/features/etc will be their own branches off of dev and once completed will be merged to dev. Once dev has been confirmed to have no issues following a merging session which will include all of our codes then it will be merged to main which then will reflect production.  
## Starting Django Server
> python3 manage.py runserver

This will start the server by default on 127.0.0.1:8000.
In settings.py the ALLOWED_HOSTS setting is ['*'] so any host can access the website (unsecure but usable for testing)



## Starting the AI model
Go into project directory, copy and paste the following into terminal:

```bash
pip install transformers torch
```
