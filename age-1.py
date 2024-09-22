import streamlit as st
from dotenv import load_dotenv
import os
from groq import Groq
import re

# Load environment variables
load_dotenv()

# Initialize the Groq client with the API key
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    st.error("GROQ_API_KEY not found in environment variables!")
else:
    client = Groq(api_key=groq_api_key)

# Define the agent class
class Agent:
    def __init__(self, client: Groq, system: str = "") -> None:
        self.client = client
        self.system = system
        self.messages: list = []
        if self.system:
            self.messages.append({"role": "system", "content": system})

    def __call__(self, message=""):
        if message:
            self.messages.append({"role": "user", "content": message})
        result = self.execute()
        self.messages.append({"role": "assistant", "content": result})
        return result

    def execute(self):
        completion = self.client.chat.completions.create(
            model=model_choice,  # Use the selected model from the sidebar
            temperature=temperature_setting,  # Use the selected temperature from the sidebar
            messages=self.messages
        )
        return completion.choices[0].message.content

# Define the available tools
def calculate(operation: str) -> float:
    return eval(operation)

def get_planet_mass(planet: str) -> float:
    masses = {
        "earth": 5.972e24,
        "jupiter": 1.898e27,
        "mars": 6.39e23,
        "mercury": 3.285e23,
        "neptune": 1.024e26,
        "saturn": 5.683e26,
        "uranus": 8.681e25,
        "venus": 4.867e24
    }
    return masses.get(planet.lower(), 0.0)

st.set_page_config(layout="wide")
# Sidebar settings for model and temperature
st.sidebar.image("p2.png")  # Displaying the uploaded image in the sidebar
st.sidebar.header("Model Settings")

# Define model choices and their corresponding IDs
model_dict = {
    "Llama 3 8B": "llama3-8b-8192",
    "Llama 3.1 70B": "llama-3.1-70b-versatile",
    "Llama 3.1 8B": "llama-3.1-8b-instant",
    "Mixtral 8x7B": "mixtral-8x7b-32768",
    "Gemma 2 9B": "gemma2-9b-it",
    "LLaVA 1.5 7B": "llava-v1.5-7b-4096-preview"
}

# Dropdown for selecting model
model_choice_label = st.sidebar.selectbox(
    "Select a model",
    list(model_dict.keys())  # Display labels
)

# Get the selected model's ID from the dictionary
model_choice = model_dict[model_choice_label]

# Slider for temperature setting
temperature_setting = st.sidebar.slider(
    "Set Model Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.01
)

# Toggle for Email Reply Agent
enable_email_reply = st.sidebar.checkbox("Enable Email Reply Agent")

# Toggle for get_planet_mass Agent
enable_get_planet_mass = st.sidebar.checkbox("Enable Get Planet Mass Tool")

# Toggle for calculate Agent
enable_calculate = st.sidebar.checkbox("Enable Calculate Tool")

# Email agent system prompt
email_agent_system_prompt = """
You are a helpful assistant.
System: 
Full context: 
You are an email responder, I will provide you with an email I received and you respond. My Name is first,last, I work at company, and I am the title person.
Steps:
1. Understand what is wanted in the email received - reference the subject line and the body.
2. Write a response to this email.
Input Format:
Full email where the subject is identified with Subject and the body is identified with Body:
Output Format:
When providing an output, don't use "Subject:" or "Body:", just output the relevant text for each section.
"""

# Decide which system prompt to use based on the toggle
if enable_email_reply:
    system_prompt = email_agent_system_prompt
    st.sidebar.markdown("**Email Agent is enabled.**")
else:
    # Default system prompt for other queries
    system_prompt = """
    You run in a loop of Thought, Action, PAUSE, Observation.
    At the end of the loop you output an Answer...
    """.strip()

st.image("p1.png")  # Displaying the uploaded image in the sidebar
st.title("email reply tool")
# Main layout
if enable_email_reply:
    col1, col2 = st.columns(2)

    with col1:
        st.write("Email Input")
        email_input = st.text_area("Enter email here (Subject: and Body:)", height=600, key="email_input_main")

    with col2:
        st.write("Response")
        if st.button("Send"):
            if email_input:
                if not groq_api_key:
                    st.error("Cannot send query because GROQ_API_KEY is missing.")
                else:
                    # Initialize agent with the selected model and system prompt
                    agent = Agent(client=client, system=system_prompt)
                    response = agent(email_input)
                    st.text_area("Response", value=response, height=600, key="response_email")
            else:
                st.warning("Please enter an email.")
else:
    query = st.text_input("Enter your query here...", key="general_query")

    # Button to send the query
    if st.button("Send"):
        if query:
            if not groq_api_key:
                st.error("Cannot send query because GROQ_API_KEY is missing.")
            else:
                # Check for the Get Planet Mass or Calculate tool, otherwise use normal agent behavior
                if enable_get_planet_mass:
                    st.write(f"Planet Mass: {get_planet_mass(planet_input)}")
                elif enable_calculate:
                    try:
                        st.write(f"Calculation Result: {calculate(calculation_input)}")
                    except Exception as e:
                        st.write(f"Error in calculation: {e}")
                else:
                    # Initialize agent with the selected model and system prompt
                    agent = Agent(client=client, system=system_prompt)
                    response = agent(query)
                    st.text_area("Response", value=response, height=200, key="general_response")
        else:
            st.warning("Please enter a query.")

st.markdown("#### System Prompt")
st.text_area("System Prompt", system_prompt, height=200, key="system_prompt")

# Footer with build details
st.markdown(
    """
    <footer>
        <div style="text-align: center; padding: 10px; background-color: #1e1e1e; color: white;">
            build by dw 9-22-24 &nbsp; | &nbsp; Powered by Groq
        </div>
    </footer>
    """,
    unsafe_allow_html=True
)
