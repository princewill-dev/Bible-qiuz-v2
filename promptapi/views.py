from django.shortcuts import render
from django.http import JsonResponse
from openai import OpenAI
from django.views import View
from django.views.decorators.csrf import csrf_exempt
import openai
import PyPDF2
from typing import List
import numpy as np


def ChatPage(request):
    return render(request, 'promptapi/chat.html')


@csrf_exempt
def prompt(request):
    if request.method == 'POST':
        client = OpenAI()
        
        # Add the user's question to the thread
        user_question = request.POST.get('message', '')
        
        # Create a vector store if it doesn't exist
        vector_store = client.beta.vector_stores.create(
            name="Vector store for Bible-quiz-v2"
        )
        
        # Upload files to OpenAI and add to vector store
        file_paths = ["./bible.pdf"]
        file_streams = [open(path, "rb") for path in file_paths]
        file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store.id, files=file_streams
        )
        
        # Create an assistant with file_search enabled
        assistant = client.beta.assistants.create(
            name="Bible Quiz Expert",
            instructions="You are a helpful bible quiz expert, with an extended knowledge of the KJV Bible. You will answer questions about the Bible using the attached file. Always use the file to answer the question. Always return the answer in the same language as the question. Always return text only, no markdown or code.",
            model="gpt-4-turbo-2024-04-09",
            tools=[{"type": "file_search"}],
            tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}}
        )
        
        # Update the assistant with new tool resources
        assistant = client.beta.assistants.update(
            assistant_id=assistant.id,
            tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}}
        )
        
        # Attach the file to the message
        message_file = client.files.create(
            file=open("./bible.pdf", "rb"), purpose="assistants"
        )
        
        # Create a thread with a predefined message and file attachment
        thread = client.beta.threads.create(
            messages=[
                {
                    "role": "user",
                    "content": user_question,
                    "attachments": [
                        { "file_id": message_file.id, "tools": [{"type": "file_search"}] }
                    ],
                }
            ]
        )
        
        # Create a run and poll for completion
        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread.id, assistant_id=assistant.id
        )
        
        # Get the assistant's response
        messages = list(client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))
        
        # Check if messages list is not empty
        if messages and messages[0].content:
            assistant_response = messages[0].content[0].text
        else:
            assistant_response = "No response received from the assistant."
        
        return render(request, 'promptapi/chat.html', {
            'response': assistant_response,
            'message': user_question
        })
    
    # If GET request, just show the empty form
    return render(request, 'promptapi/chat.html')
