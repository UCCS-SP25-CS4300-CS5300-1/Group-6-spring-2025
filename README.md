# Group-6-spring-2025

## Github Workflow
In order to try and imitate a proper environment we will utilize this type of workflow in terms of branches. main will be untouched and will be the production environment to ensure that during development no issues are automatically propogated to the production side. So off of the main branch we will use the dev branch. Any issues/features/etc will be their own branches off of dev and once completed will be merged to dev. Once dev has been confirmed to have no issues following a merging session which will include all of our codes then it will be merged to main which then will reflect production.  
## Starting Django Server
> python3 manage.py runserver 0.0.0.0:3000
In settings.py the ALLOWED_HOSTS setting is ['*'] so any host can access the website

## Starting the AI model
Go into project directory, copy and paste the following into terminal:

```bash
pip install transformers torch
```
## django Requirements
I order to make sure we maintain a list of packages we are using that can easily be installed we will leverage requirements.txt located in Group-6-spring-2025/Project/requirements.txt
To install dependencies using it do:
> pip install requirements.txt

In order to update the file if you install new dependencies do:
> pipreqs Group-6-spring-2025/Project

You may need to install pipreqs first:
> pip install pipreqs

# Sprint 1 Changelog

### 1. User Profiles (New feature)
Associated Urls:
1. login
2. register
3. update_profile
4. user_data

The user profile page is capable of displaying data such as height, weight, body mass index (BMI) through height/weight calculations. The User can also change the Fitness level, Goals, and Injury History to reflect their needs.

### 2. Goal Setting (New feature)
Associated Urls:
1. goals
2. set-exercises
3. my-exercises
4. delete_exercise/<int:pk>/
   
The goal setting page provides the User with the capable of setting goals based on exercises, current weights, and the desired increase in that exercise.
The User may add exercises, remove exercises, view their selections and conveintely see the exercises selected along with their profile goals so they can make decisions accordingly.

### 3. AI Generate Workout Plans (New feature)
Associated Urls:
1. generate-workout
   
Using Lukamac/PlayPart-AI-Personal-Trainer the user can query the AI with certain phrases in order to tailor their workout experience. This feature will further be incorporated to alter other aspects such as goals and more.

### 4. Test Coverage Metrics && Coverage on commits
1. By leveraging `coverage==7.6.12` we use this tool in order to determine the test coverage of our files.
   `.coverage` is used by running `coverage run manage.py test` and to view the results run `coverage report`.
  In the case of our setup we run `coverage run --source=home,mysite,accounts,goals manage.py test` which tells the tool to look at the python modules included in the `--source=` option. This automatically filters the testing and we finish it with `coverage report`
2. In order to utilize this for the test coverage of every commit we utilize a pre-commit git hub hook. This will run everytime the developer runs `git commit`.
   Check out the github hook at `.githooks/pre-commit` then to set it up you need to change the git configuration like so: `git config --local core.hooksPath .githooks/` and it will run after _every_ commit.

### 5. CI Pipeline
1. The task to report test covereage metrics in console on each commit has been explained above in the _Test Coverage Metrics && Coverage on commits_ section.
2. The second task to run automated test for each commit is completed by using the github workflows. Our file is located at `.github/workflows/testdjango.yml`. In short, this workflow sets up the environments based of our `requirements.txt` the runs `python3 manage.py test` to run our entire test sweet. If it passes or fails it will be displayed and associated with that push.
3. Finally, the last task is to automatically, for each pull request, query OpenAI and have it output a review of the code and explain the changes. Our workflow file is located at `.github/workflows/ai_pr_review.yml` and queries the gpt-4 model. The workflow also posts the output of the OpenAI model response to the PR review comments.
4. yelllow

### 6. Host Production Environment
Using Digital Ocean through the GitHub Student Developer Pack the team was capable of deploying our main branch (with some adjustments) to the Digital Ocean Droplet to deploy the application. Every time our main branch is changed the build process automatically starts to deploy the latest and greatest of our applicaiton.
The default url to find the application is: [https://aifitnessapp-kqi6e.ondigitalocean.app].
Alternatively you can find it as this super cool url: [https://aifitnessapp.workingout.rocks]
