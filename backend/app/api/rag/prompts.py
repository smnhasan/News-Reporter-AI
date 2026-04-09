from datetime import datetime
from typing import List, Dict

def get_chat_prompt(user_input: str, history: List = [], context: str = None) -> List[Dict[str, str]]:
    today_date = datetime.today().strftime("%d %B %Y")  
    
    system_content = (
        f"Cutting Knowledge Date: December 2023\n"
        f"Today Date: {today_date}\n\n"
        "You are a helpful news reporter bot. You do not have specific name. If user asks about basic chit-chat, reply them. "
        # "DO NOT provide information which is not present on the Retrieved Context. "
        # "If there is no information about the question on the context just say 'I do not know about it'. "
        # "Provide precise response."
        "Generate response in markdown. "
        "You will be provided with snippets of Retrieved Context labeled like 'Document [1]:'. "
        "If you use information from a specific Document, you MUST place its bracketed number at the end of the sentence (e.g., 'The sky is blue [1].'). "
        "DO NOT generate a 'Sources:' list yourself. Just insert the correct bracket numbers inline."
    )

    if context:
        system_content += f"\n\nRetrieved Context:\n{context}"

    messages = [
        {"role": "system", "content": system_content}
    ]

    # Append chat history
    for role, message in history:
        messages.append({"role": role, "content": message})

    # Append current user input
    messages.append({"role": "user", "content": user_input})

    return messages

def get_standalone_query_generation_prompt(user_input: str, history: List) -> List[Dict[str, str]]:
    system_content = (
        "Think step-by-step. Write the standalone query of the last user message so that it contains all the information "
        "of this question and best suited for context retrieval. Just write the query in detailed form. "
        "DO NOT write any extra explanation. DO NOT write the answer."
    )

    messages = [
        {"role": "system", "content": system_content}
    ]

    # Append chat history
    for role, message in history:
        messages.append({"role": role, "content": message})

    # Append current user input
    user_content = f"Last User Message: {user_input}\n\nStandalone Query: (Standalone Query should be in detailed form. DO NOT Answer the query here.)"
    messages.append({"role": "user", "content": user_content})

    return messages
