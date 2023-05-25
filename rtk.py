"""
Researcher's Toolkit
Mike Schladt - 2023
"""

import os
import requests

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


def search_semantic_scholar():
    """Search Semantic Scholar for a paper"""


    context_path = "(Semantic Scholar)"
    prompt_text = [
        ('class:green', f'\n{context_path} >>> '),
    ]

    while (1):

        print(HTML("<blue>What type of search would you like: </blue>"), style=prompt_style)
        print("\t1. Search by keyword", style=prompt_style)
        print("\t2. Search by author", style=prompt_style)
        print("\t3. 'q' to return ", style=prompt_style)

        selection = prompt_session.prompt(prompt_text, style=prompt_style)

        if selection == "1":
            search_semantic_scholar_by_keyword()

        elif selection == "2":
            search_semantic_scholar_by_author()

        elif selection.lower()[0] == "q":
            break

def search_semantic_scholar_by_keyword():
    """Search Semantic Scholar for a paper by keyword"""

    context_path = "(Semantic Scholar > Search by keyword)"
    prompt_text = [
        ('class:green', f'\n{context_path} >>> '),
    ]

    print("What keyword would you like to search for?", style=prompt_style)
    keyword = prompt_session.prompt(prompt_text, style=prompt_style)

    print(f"Searching Semantic Scholar for '{keyword}'...", style=prompt_style)

    offset = 0
    limit = 10 
    requests_session = requests.Session()
    while (1):
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": keyword,
            "offset": offset,
            "fields": "title,authors,year,citationCount,venue,paperId,tldr",
            "limit": limit,  
        }
        response = requests_session.get(url, params=params)

        # check for 200 response
        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.reason}", style=prompt_style)
            break

        # show titles of the papers
        print(f'Showing papers {offset+1} to {offset+limit} of {response.json()["total"]}:', style=prompt_style)

        results = response.json()["data"]
        i = 0
        for paper in results:
            print(f'\t{i + offset} {paper["title"]}, {paper["authors"][0]["name"]}, {paper["year"]}', style=prompt_style)
            i += 1
        
        # prompt for which paper to view
        print(HTML("\n<blue>Select from the following options:</blue>"), style=prompt_style)
        print("\tEnter # to select paper above for more details")
        print("\tEnter 'n' to see the next page of results")
        print("\tEnter 'p' to see the previous page of results")
        print("\tEnter 'q' to return")
        selection = prompt_session.prompt(prompt_text, style=prompt_style)

        # attempt to convert selection to int
        try:
            selection = int(selection)
        except ValueError:
            pass

        if selection in range(offset, offset + limit):
            # show paper details 
            print(f"Showing details for paper {selection}:", style=prompt_style)
            paper = results[selection - offset]
            print(f'\tTitle: {paper["title"]}', style=prompt_style)
            print(f'\tAuthors: ', style=prompt_style)
            for author in paper["authors"]:
                print(f'\t\t{author["name"]}', style=prompt_style)
            print(f'\tYear: {paper["year"]}', style=prompt_style)
            print(f'\tCitation Count: {paper["citationCount"]}', style=prompt_style)
            print(f'\tVenue: {paper["venue"]}', style=prompt_style)
            print(f'\tPaper ID: {paper["paperId"]}', style=prompt_style)
            if 'text' in paper['tldr']:
                print(f'\tTLDR: {paper["tldr"]["text"]}', style=prompt_style)

            # show more details or return to main menu
            print(HTML("\n<blue>Would you like to select this paper?:</blue>"), style=prompt_style)
            print("\tEnter 'y' to switch context to this paper (show more details, add to graph, add notes, etc.)") 
            print("\tEnter anything else to return to results")
            selection = prompt_session.prompt(prompt_text, style=prompt_style)
            if selection.lower() == "y":
                print("Switching context to paper...", style=prompt_style)
                semantic_scholar_paper_context(paper)
                break
            
            else:
                continue

        elif type(selection) == int and selection not in range(offset, offset + limit):
            print(f"Invalid selection: {selection}", style=prompt_style)
            break 

        # get next
        elif selection.lower() == "n":
            offset += limit

        # get previous
        elif selection.lower() == "p":
            offset -= limit
            if offset < 0:
                offset = 0
                
        # break to return to main menu
        else:
            break

    # close requests session
    requests_session.close()

def search_semantic_scholar_by_author(): 
    """Search Semantic Scholar for a paper by author"""

    context_path = "(Semantic Scholar > Search by author)"
    prompt_text = [
        ('class:green', f'\n{context_path} >>> '),
    ]

    print("What author would you like to search for?", style=prompt_style)
    author = prompt_session.prompt(prompt_text, style=prompt_style)

    print(f"Searching Semantic Scholar for '{author}'...", style=prompt_style)

def semantic_scholar_paper_context(paper):
    requests_session = requests.Session()
    url = f"https://api.semanticscholar.org/graph/v1/paper/{paper['paperId']}"
    params = {
        "fields": "title,authors,year,citationCount,venue,paperId,tldr,abstract",
    }
    response = requests_session.get(url, params=params)

    # check for 200 response
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.reason}", style=prompt_style)
        # close requests session
        requests_session.close()
        return
    
    paper = response.json()
    print(f"Showing details for paper {paper['title']}:", style=prompt_style)
    print(f'\tTitle: {paper["title"]}', style=prompt_style)
    print(f'\tAuthors: ', style=prompt_style)
    for author in paper["authors"]:
        print(f'\t\t{author["name"]}', style=prompt_style)
    print(f'\tYear: {paper["year"]}', style=prompt_style)
    print(f'\tCitation Count: {paper["citationCount"]}', style=prompt_style)
    print(f'\tVenue: {paper["venue"]}', style=prompt_style)
    print(f'\tPaper ID: {paper["paperId"]}', style=prompt_style)
    if 'text' in paper['tldr']:
        print(f'\tTLDR: {paper["tldr"]["text"]}', style=prompt_style)
    print(f'\tAbstract: {paper["abstract"]}', style=prompt_style)

    # close requests session
    requests_session.close()

def search_local_database():
    """Search the local database for a paper or any other entity"""
    print(HTML('<red>Not implemented yet!</red>'), style=prompt_style)

def modify_database():
    """Manually modify the local database (add notes, delete nodes, etc.))"""
    print(HTML('<red>Not implemented yet!</red>'), style=prompt_style)

def main_menu():
        
    # main loop
    selection = ""
    while selection.lower() not in ["quit", "exit", "4"]: 

        context_path = ""
        prompt_text = [
            ('class:green', f'\n{context_path} >>> '),
    ]

        print()
        print(HTML("<blue>What would you like to do?</blue>"), style=prompt_style)
        print()
        print("\t1. Search Semantic Scholar", style=prompt_style)
        print("\t2. Search local database", style=prompt_style)
        print("\t3. Manually modify database (advanced)", style=prompt_style)
        print("\t4. 'q' (or anything else) to exit", style=prompt_style)


        selection = prompt_session.prompt(prompt_text, style=prompt_style)
        
        if selection == "1":
            search_semantic_scholar()
        elif selection == "2":
            search_local_database()
        elif selection == "3":
            modify_database()
        else:
            break

    print(HTML('<red>GoodBye!</red>'), style=prompt_style)

def main():

    # Welcome message
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

    # call main menu
    main_menu()

if __name__ == "__main__":
    main()
