import streamlit as st
import os
import requests
from groq import Groq

# Load environment variables
groq_api_key = os.getenv("GROQ_API_KEY")
serpapi_key = os.getenv("SERPAPI_KEY")

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
            model=model_choice,
            temperature=temperature_setting,
            messages=self.messages
        )
        return completion.choices[0].message.content

# Define the SerpApi Web Search Agent
def search_web(query):
    search_url = f"https://serpapi.com/search"
    params = {
        "q": query,
        "api_key": serpapi_key
    }
    response = requests.get(search_url, params=params)
    if response.status_code == 200:
        return response.json()["organic_results"]  # Assuming 'organic_results' contains the search results
    else:
        return f"Error: Unable to complete search (Status code: {response.status_code})"

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
st.sidebar.image("p2.png")
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
    list(model_dict.keys())
)

# Get the selected model's ID from the dictionary
model_choice = model_dict[model_choice_label]

# Slider for temperature setting
temperature_setting = st.sidebar.slider(
    "Set Model Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.01
)

# Toggles for enabling tools
enable_email_reply = st.sidebar.checkbox("Enable Email Reply Agent")
enable_get_planet_mass = st.sidebar.checkbox("Enable Get Planet Mass Tool")
enable_calculate = st.sidebar.checkbox("Enable Calculate Tool")
enable_web_search = st.sidebar.checkbox("Enable Web Search Agent")

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

# System prompt based on toggle
system_prompt = email_agent_system_prompt if enable_email_reply else """
    You run in a loop of Thought, Action, PAUSE, Observation.
    At the end of the loop you output an Answer...
    """.strip()

st.image("p1.png")
st.write("Email Reply Tool & Web Search Agent")

# Main layout logic
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
                    # Initialize agent
                    agent = Agent(client=client, system=system_prompt)
                    response = agent(email_input)
                    st.text_area("Response", value=response, height=600, key="response_email")
            else:
                st.warning("Please enter an email.")
elif enable_web_search:
    st.write("Web Search")
    search_query = st.text_input("Enter your search query here...", key="search_query")
    
    if st.button("Search"):
        if search_query:
            search_results = search_web(search_query)
            if isinstance(search_results, str):
                st.error(search_results)
            else:
                st.write("Search Results:")
                for idx, result in enumerate(search_results, start=1):
                    st.write(f"{idx}. [{result['title']}]({result['link']})")
                    st.write(result.get("snippet", "No description available"))
        else:
            st.warning("Please enter a search query.")
else:
    query = st.text_input("Enter your query here...", key="general_query")

    if enable_get_planet_mass:
        planet_input = st.text_input("Enter planet name:", key="planet_input")
    
    if enable_calculate:
        calculation_input = st.text_input("Enter calculation:", key="calculation_input")

    if st.button("Send"):
        if query:
            if not groq_api_key:
                st.error("Cannot send query because GROQ_API_KEY is missing.")
            else:
                if enable_get_planet_mass:
                    st.write(f"Planet Mass: {get_planet_mass(planet_input)}")
                elif enable_calculate:
                    try:
                        st.write(f"Calculation Result: {calculate(calculation_input)}")
                    except Exception as e:
                        st.write(f"Error in calculation: {e}")
                else:
                    agent = Agent(client=client, system=system_prompt)
                    response = agent(query)
                    st.text_area("Response", value=response, height=200, key="general_response")
        else:
            st.warning("Please enter a query.")

st.markdown("#### System Prompt")
st.text_area("System Prompt", system_prompt, height=200, key="system_prompt")

# Footer
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
