from django.shortcuts import render
from .ai import ai_model  # Import the AI model instance

def index(request):
    return render(request, 'index.html')



#Recieves a request object from django
def generate_workout(request):

    #Creating dictionary to pass HTML to
    context = {}
    
    #Check if user clicked a button
    if request.method == 'POST':

        #Obtain the user input that was submitted.
        user_input = request.POST.get('user_input', '')

        #Check is user input is empty
        if user_input:
            try:
                #if not empty- get a response from the ai model with user input as prompt
                response = ai_model.get_response(user_input)
            except Exception as e:
                response = f"Error generating response: {str(e)}"

            #Adding both output and response to context diary
            context['output'] = response
            context['user_input'] = user_input

    #Rendering the html while passing the context diary
    return render(request, 'generate_workout.html', context)