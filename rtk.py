"""
Researcher's Toolkit
Mike Schladt - 2023
"""

import os

# prompt_toolkit imports
from prompt_toolkit import PromptSession
from prompt_toolkit import print_formatted_text as print, HTML
from prompt_toolkit.styles import Style

# neo4j imports
from neo4j import GraphDatabase


# set up the prompt session and style
prompt_session = PromptSession()
prompt_style = Style.from_dict({
    'red': '#ff0066',
    'green': '#44ff00', 
    'blue': '#00aaff',
    'u': '#aa00ff underline',
})


# main menu
welcome_text = "\n<blue>--------------------------------------------------------\n" \
                + "Welcome to the Researcher's Toolkit!\n" \
                + "--------------------------------------------------------\n</blue>"

print(HTML(welcome_text), style=prompt_style)

# connect to database
print(HTML('<green>Connecting to database...</green>'), style=prompt_style)

# get password and connection string from environment variables
neo4j_password = os.environ.get("NEO4J_PASSWORD")
if neo4j_password is None:
    print(HTML('<red>ERROR: NEO4J_PASSWORD environment variable not set</red>'), style=prompt_style)
    exit()
neo4j_connection_string = os.environ.get("NEO4J_CONNECTION_STRING")
if neo4j_connection_string is None:
    print(HTML('<red>ERROR: NEO4J_CONNECTION_STRING environment variable not set</red>'), style=prompt_style)
    exit()
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", neo4j_password))

try:
    driver.verify_connectivity()
except Exception as e:
    print(HTML(f'<red>ERROR: {e}</red>'), style=prompt_style)
    exit()

print(HTML('<green>Connected to database!</green>'), style=prompt_style)


# main loop
print()
print("What would you like to do?", style=prompt_style)
print()
print("\t1. Search Semantic Scholar", style=prompt_style)
print("\t2. Search local database", style=prompt_style)
print("\t3. Manually modify database (advanced)", style=prompt_style)
print("\t4. Quit (or type 'quit' / 'exit')", style=prompt_style)

context_path = ""
prompt_text = [
    ('class:green', f'\n{context_path}>>> '),
]

text = ""
while text.lower() not in ["quit", "exit", "4"]: 
    text = prompt_session.prompt(prompt_text, style=prompt_style)
    print(HTML(f'You entered: <green><u>{text}</u></green>'))

print(HTML('<red>GoodBye!</red>'), style=prompt_style)

