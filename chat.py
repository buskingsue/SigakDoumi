# chat.py

import sys
import requests

sys.stdin.reconfigure(encoding='utf-8')

# FastAPI server URL for chat
API_URL = "http://61.108.166.15:8000/chat/"

def send_to_fastapi(question, conversation_id, current_step):
    """
    Send user query to FastAPI server and receive the response
    """
    # Prepare the payload as expected by FastAPI server
    payload = {
        "question": question,
        "conversation_id": conversation_id,
        "current_step": current_step
    }

    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        data = response.json()

        # Extract response data from FastAPI response
        answer = data.get("answer", "No answer provided")
        intent = data.get("intent", "")
        current_step = data.get("current_step", current_step)
        context = data.get("context", {})

        # Return the relevant data back to the main program
        return answer, intent, current_step, context

    except requests.exceptions.RequestException as e:
        print(f"Error communicating with the server: {e}")
        return "Sorry, something went wrong.", None, current_step, {}

def main():
    print("Chat with the AI (type 'exit' or 'quit' to end)")
    conversation_id = "default"  # Use a default conversation ID
    current_step = None  # This can be updated based on backend responses

    while True:
        # Input from the user (chat query)
        user_input = input("You: ").strip()

        if user_input.lower() in ["exit", "quit"]:
            print("Exiting chat.")
            break

        # Send the query to FastAPI server
        answer, intent, current_step, context = send_to_fastapi(user_input, conversation_id, current_step)

        # Print the answer from FastAPI
        print("AI:", answer)
        print("intent:", intent)

        # Check if we need to trigger any actions based on the intent
        if intent:
            print(f"Intent detected: {intent}")
            # Here we can add actions based on the intent, e.g., triggering actions in the system
            handle_action(intent, context)

        # Optionally, handle current_step or other variables based on the response
        # You could update conversation state or perform additional logic as needed
        conversation_id = context.get("conversation_id", conversation_id)

def handle_action(intent, context):
    """
    Handle different actions based on the intent from the FastAPI server response.
    You can expand this function to trigger more complex actions depending on your needs.
    """
    if intent == "ADD_MEDICINE":
        print("Performing action: Adding medicine...")
        # Trigger the corresponding action on Raspberry Pi or your system
        # You can add more logic here to interact with databases, APIs, etc.
    
    elif intent == "REMOVE_MEDICINE":
        print("Performing action: Removing medicine...")
        # Trigger the corresponding action on Raspberry Pi or your system

    elif intent == "CHECK_SCHEDULE":
        print("Performing action: Checking schedule...")
        # Trigger the corresponding action to check schedule

    # Add more actions as needed

if __name__ == "__main__":
    main()
