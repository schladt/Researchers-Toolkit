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

driver = None
x_api_key = None

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
    global x_api_key

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
            "fields": "title,authors,year,paperId",
            "limit": limit,  
        }
        # add headers
        headers = {
            "x-api-key": x_api_key,
        }
        response = requests_session.get(url, params=params, headers=headers)

        # check for 200 response
        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.reason}", style=prompt_style)
            break

        # check for no results
        if response.json()["total"] == 0:
            print(f"No results for '{keyword}'", style=prompt_style)
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
            paper = results[selection - offset]
            semantic_scholar_paper_context(paper)

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
    global driver
    requests_session = requests.Session()
    url = f"https://api.semanticscholar.org/graph/v1/paper/{paper['paperId']}"
    params = {
        "fields": "title,authors,year,citationCount,referenceCount,venue,paperId,tldr,abstract,url,references,citations",
    }
    # add headers
    headers = {
        "x-api-key": x_api_key,
    }
    response = requests_session.get(url, params=params, headers=headers)

    # check for 200 response
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.reason}", style=prompt_style)
        # close requests session
        requests_session.close()
        return

    paper = response.json()
    print(f"Showing details for paper {paper['title']}:", style=prompt_style)
    print(f'\tTitle: {paper["title"]}', style=prompt_style)
    print(f'\tURL: {paper["url"]}', style=prompt_style)
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

    # prompt for what to do next
    context_path = f"(Semantic Scholar > {paper['paperId']})"
    prompt_text = [
        ('class:green', f'\n{context_path} >>> '),
    ]
    print(HTML("\n<blue>What would you like to do next?:</blue>"), style=prompt_style)
    print("\tEnter 'g' to add this paper to the graph")
    print("\tEnter 'q' to return to main menu")
    selection = prompt_session.prompt(prompt_text, style=prompt_style)

    # add paper to graph
    if selection.lower() == "g":

        # create paper node
        add_paper_to_graph(paper)

        # get citations for paper
        citations = []
        offset = 0
        while (1):
            url = f"https://api.semanticscholar.org/graph/v1/paper/{paper['paperId']}/citations"
            params = {
                "fields": "title,authors,year,venue,paperId,abstract,url",
                "limit": 100,
                "offset": offset
            }
            # add headers
            headers = {
                "x-api-key": x_api_key,
            }
            response = requests_session.get(url, params=params, headers=headers)

            # check if the response is valid
            if response.status_code != 200:
                print(response.json())
                break

            # add the citations to the list
            citations.extend(response.json()["data"])

            # check if there are more citations
            if 'next' not in response.json():
                break    

            offset += 100

        # add each citation to the graph
        for citation in citations:
            add_paper_to_graph(citation["citingPaper"])

        # create relationship between paper and citations
        for citation in citations:
            if 'paperId' in citation["citingPaper"]:
                query_text = (
                    "MATCH (p:Paper {id: $paperId}) "
                    "MATCH (c:Paper {id: $citationId}) "
                    "MERGE (p)-[:CITED_BY]->(c)"
                )
                summary = driver.execute_query(query_text, paperId=paper['paperId'], citationId=citation["citingPaper"]['paperId'])            
            elif 'title' in citation["citingPaper"]:
                query_text = (
                    "MATCH (p:Paper {id: $paperId}) "
                    "MATCH (c:Paper {Title: $citationTitle}) "
                    "MERGE (p)-[:CITED_BY]->(c)"
                )
                summary = driver.execute_query(query_text, paperId=paper['paperId'], citationTitle=citation["citingPaper"]['title'])
            else:
                continue

        # create citation nodes 

        # create reference nodes

        # create keyword nodes

        # create year node



        

        # create relationship between paper and references

        # create relationship between paper and keywords

        # create relationship between paper and year

    else:
        pass

    # close requests session
    requests_session.close()

def add_paper_to_graph(paper):
    """Add a paper to the graph database"""
    global driver
    print("Adding paper to graph...", style=prompt_style)

    # create paper node
    if 'paperId' in paper and paper['paperId'] is not None:
        query_text = (
            "MERGE (p:Paper {id: $paper_id}) "
            "SET p.Title=$title "
            "SET p.Year = $year "
            "SET p.Venue = $venue "
            "SET p.PrimaryAuthor = $author "
            "SET p.URL = $url "
        )
        if 'authors' in paper and len(paper['authors']) > 0:
            author = paper['authors'][0]['name']
        else:
            author = "Unknown"
        summary = driver.execute_query(query_text, 
                                    paper_id = paper['paperId'],
                                    title = paper['title'],
                                    year = paper['year'],
                                    venue = paper['venue'],
                                    author = author,
                                    url = paper['url'],
                                    database_="neo4j"
                                )
        print(f'created {summary.summary.counters.nodes_created} nodes and {summary.summary.counters.relationships_created} relationships')
    elif 'title' in paper and paper['title'] is not None:

        query_text = (
            "MERGE (p:Paper {Title: $title}) "
            "SET p.Year = $year "
            "SET p.Venue = $venue "
            "SET p.PrimaryAuthor = $author "
            "SET p.URL = $url "
        )
        if 'authors' in paper and len(paper['authors']) > 0:
            author = paper['authors'][0]['name']
        else:
            author = "Unknown"
        summary = driver.execute_query(query_text, 
                                    title = paper['title'],
                                    year = paper['year'],
                                    venue = paper['venue'],
                                    author = author,
                                    url = paper['url']
                                )
        print(f'created {summary.summary.counters.nodes_created} nodes and {summary.summary.counters.relationships_created} relationships')

    # create author nodes
    for author in paper["authors"]:
        if 'authorId' in author and author['authorId'] is not None:
            query_text = (
                "MERGE (a:Author {id: $authorId}) "
                "SET a.Name=$name "
            )
            summary = driver.execute_query(query_text,
                                    authorId = author['authorId'],
                                    name = author['name']
                                )
            print(f'created {summary.summary.counters.nodes_created} nodes and {summary.summary.counters.relationships_created} relationships')
        elif 'name' in author and author['name'] is not None:
            query_text = (
                "MERGE (a:Author {name: $name}) "
            )
            summary = driver.execute_query(query_text, name=author['name'])
        
            print(f'created {summary.summary.counters.nodes_created} nodes and {summary.summary.counters.relationships_created} relationships')

    # create relationships between paper and authors
    for author in paper["authors"]:
        if 'authorId' in author and author['authorId'] is not None:
            query_text = (
                "MATCH (p:Paper {id: $paperId}) "
                "MATCH (a:Author {id: $authorId}) "
                "MERGE (p)-[:AUTHORED_BY]->(a) "
            )
            summary = driver.execute_query(query_text, paperId=paper['paperId'], authorId=author['authorId'])
            print(f'created {summary.summary.counters.nodes_created} nodes and {summary.summary.counters.relationships_created} relationships')
        elif 'name' in author and author['name'] is not None:
            query_text = (
                "MATCH (p:Paper {id: $paperId}) "
                "MATCH (a:Author {name: $name}) "
                "MERGE (p)-[:AUTHORED_BY]->(a) "
            )
            summary = driver.execute_query(query_text, paperId=paper['paperId'], name=author['name'])
            print(f'created {summary.summary.counters.nodes_created} nodes and {summary.summary.counters.relationships_created} relationships')


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
    global driver
    global x_api_key

    # Welcome message
    welcome_text = "\n<blue>--------------------------------------------------------\n" \
                    + "Welcome to the Researcher's Toolkit!\n" \
                    + "--------------------------------------------------------\n</blue>"

    print(HTML(welcome_text), style=prompt_style)

    # connect to database
    print(HTML('<green>Connecting to database...</green>'), style=prompt_style)

    # get neo4j user, password, and connection string from environment variables
    neo4j_user = os.environ.get("NEO4J_USER")
    if neo4j_user is None:
        print(HTML('<red>ERROR: NEO4J_USER environment variable not set</red>'), style=prompt_style)
        exit()
    neo4j_password = os.environ.get("NEO4J_PASSWORD")
    if neo4j_password is None:
        print(HTML('<red>ERROR: NEO4J_PASSWORD environment variable not set</red>'), style=prompt_style)
        exit()
    neo4j_url = os.environ.get("NEO4J_URL")
    if neo4j_url is None:
        print(HTML('<red>ERROR: NEO4J_CONNECTION_STRING environment variable not set</red>'), style=prompt_style)
        exit()
    
    # get semantic scholar api key from environment variable
    x_api_key = os.environ.get("S2_API_KEY")

    # connect to neo4j database
    driver = GraphDatabase.driver(neo4j_url, auth=("neo4j", neo4j_password))
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
