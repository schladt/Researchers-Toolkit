"""
Researcher's Toolkit
Mike Schladt - 2023
"""

import os
import requests
import hashlib
import html 
from tqdm import tqdm

from ratelimit import limits, RateLimitException
from backoff import on_exception, expo
from concurrent.futures import ProcessPoolExecutor

# prompt_toolkit imports
from prompt_toolkit import PromptSession
from prompt_toolkit import print_formatted_text as print, HTML
from prompt_toolkit.styles import Style

# neo4j imports
from neo4j import GraphDatabase

# nltk imports
import nltk
import string

# Install the necessary NLTK data
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)

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

# paper class
class Paper:
    """
    Class for a paper
    Attributes:
        title (str): the title of the paper
        author (str): the primary author of the paper
        year (int): the year the paper was published
        id (str): the unique id of the paper
        citation_count (int): the number of citations the paper has
        reference_count (int): the number of references the paper has
        venue (str): the venue the paper was published in
        tldr (str): the TLDR of the paper
        abstract (str): the abstract of the paper
        url (str): the url of the paper    
    """

    def __init__(self, paper_dict):
        """ 
        INPUT: paper_dict - a dictionary containing the paper details from Semantic Scholar JSON response
        """

        # parse paper details
        
        # get title
        if 'title' not in paper_dict or paper_dict['title'] is None:
            return # all papers should have a title
        self.title = html.escape(paper_dict['title'])

        # get primary author
        if 'authors' in paper_dict and len(paper_dict['authors']) > 0:
            self.author = html.escape(paper_dict['authors'][0]['name'])
        else:
            self.author = "unknown"

        # get all authors as a list of dicts
        self.authors = []
        for author in paper_dict["authors"]:
            if 'authorId' in author and author['authorId'] is not None:
                author_id = author['authorId']
            elif 'name' in author and author['name'] is not None:
                author_id = self.get_sha1_hash(author['name'])
            else:
                continue # skip this author if there is no id or name
            
            # add name
            if 'name' in author and author['name'] is not None:
                author_name = html.escape(author['name'])
            else:
                author_name = "unknown"

            self.authors.append({"id": author_id, "name": author_name})

        # get paper id
        if 'paperId' in paper_dict and paper_dict['paperId'] is not None:
            self.id = paper_dict['paperId']
        else:
            # create a unique id for the paper if one does not exist
            self.id = self.get_sha1_hash(self.title + self.author)

        # all other attributes are optional
        if 'year' in paper_dict and paper_dict['year'] is not None:
            self.year = paper_dict['year']
        else:
            self.year = 0
        
        if 'venue' in paper_dict and paper_dict['venue'] is not None:
            self.venue = html.escape(paper_dict['venue'])
        else:
            self.venue = ""
        
        if 'abstract' in paper_dict and paper_dict['abstract'] is not None:
            self.abstract = html.escape(paper_dict['abstract'])
        else:
            self.abstract = ""
        
        if "tldr" in paper_dict and paper_dict['tldr'] is not None and 'text' in paper_dict['tldr'] and paper_dict['tldr']['text'] is not None:
            self.tldr = html.escape(paper_dict['tldr']['text'])
        else:
            self.tldr = ""
        
        if 'citationCount' in paper_dict and paper_dict['citationCount'] is not None:
            self.citation_count = paper_dict['citationCount']
        else:
            self.citation_count = 0
        
        if 'referenceCount' in paper_dict and paper_dict['referenceCount'] is not None:
            self.reference_count = paper_dict['referenceCount']
        else:
            self.reference_count = 0

        if 'url' in paper_dict and paper_dict['url'] is not None:
            self.url = paper_dict['url']
        else:
            self.url = ""

    def get_sha1_hash(self, text):
        """Returns the SHA1 hash of the given string."""
        hash_object = hashlib.sha1(text.encode())
        hex_dig = hash_object.hexdigest()
        return hex_dig

    def __repr__(self):
        return f"Paper(title={self.title}, primary author={self.author}, year={self.year}, paperId={self.id}, citation count={self.citation_count}, reference count={self.reference_count}, venue={self.venue}, tldr={self.tldr}, abstract={self.abstract}, url={self.url})"

    def __str__(self):
        return f"Paper(title={self.title}, primary author={self.author}, year={self.year}, paperId={self.id}, citation count={self.citation_count}, reference count={self.reference_count}, venue={self.venue}, tldr={self.tldr}, abstract={self.abstract}, url={self.url})"
    
def search_semantic_scholar():
    """Search Semantic Scholar for a paper"""


    context_path = "(Semantic Scholar)"
    prompt_text = [
        ('class:green', f'\n{context_path} >>> '),
    ]

    while (1):

        print(HTML("<blue>What type of search would you like: </blue>"), style=prompt_style)
        print("\t1. Search Semantic Scholar by keyword", style=prompt_style)
        print("\t2. Search Semantic Scholar by author", style=prompt_style)
        print("\t3. Search Semantic Scholar by Paper ID ", style=prompt_style)
        print("\t4. Refresh references for all papers in database ", style=prompt_style)
        print("\t(anything else to return)", style=prompt_style)

        selection = prompt_session.prompt(prompt_text, style=prompt_style)

        if selection == "1":
            search_semantic_scholar_by_keyword()

        elif selection == "2":
            search_semantic_scholar_by_author()

        elif selection == "3":
            paper_id = prompt_session.prompt(HTML("<blue>Enter paper ID: </blue>"), style=prompt_style)
            semantic_scholar_paper_context(paper_id)

        elif selection == "4":
            search_semantic_refresh_references()
            
        else:
            break

def search_semantic_scholar_by_keyword():
    """Search Semantic Scholar for a paper by keyword"""
    global x_api_key

    context_path = "(Semantic Scholar > Search by keyword)"
    prompt_text = [
        ('class:green', f'\n{context_path} >>> '),
    ]

    print(HTML("<blue>What keyword(s) would you like to search?</blue>"), style=prompt_style)
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
        print(HTML(f'<blue>Showing papers {offset+1} to {offset+limit} of {response.json()["total"]}:</blue>'), style=prompt_style)

        results = response.json()["data"]
        i = 0
        for paper in results:
            if 'title' not in paper or paper['title'] is None:
                continue
            if 'authors' in paper and len(paper['authors']) > 0:
                author = paper['authors'][0]['name']
            else:
                author = "unknown"
            if 'year' in paper and paper['year'] is not None:
                year = paper['year']
            else:
                year = 0
            
            display_text = f'<blue>\t{i + offset}:</blue> {html.escape(paper["title"])}, {author}, {year}'
            print(HTML(display_text), style=prompt_style)
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
            semantic_scholar_paper_context(paper['paperId'])

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
    global x_api_key

    context_path = "(Semantic Scholar > Search by Author)"
    prompt_text = [
        ('class:green', f'\n{context_path} >>> '),
    ]

    print(HTML("<blue>Enter author's name to search: </blue>"), style=prompt_style)
    search_term = prompt_session.prompt(prompt_text, style=prompt_style)

    print(f"Searching Semantic Scholar for '{search_term}'...", style=prompt_style)

    offset = 0
    limit = 10 
    requests_session = requests.Session()
    while (1):
        url = "https://api.semanticscholar.org/graph/v1/author/search"
        params = {
            "query": search_term,
            "offset": offset,
            "fields": "authorId,url,name,paperCount,citationCount",
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
            print(f"No results for '{search_term}'", style=prompt_style)
            break

        # show titles of the authors
        print(HTML(f'<blue>Showing authors {offset+1} to {offset+limit} of {response.json()["total"]}:</blue>'), style=prompt_style)

        results = response.json()["data"]
        i = 0
        for author in results:
            print(HTML(f'<blue>\t{i + offset}:</blue> {author["name"]}, {author["paperCount"]} papers, {author["citationCount"]} citations'), style=prompt_style)
            i += 1
        
        # prompt for which author to view
        print(HTML("\n<blue>Select from the following options:</blue>"), style=prompt_style)
        print("\tEnter # to select author above for more details")
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
            author = results[selection - offset]
            semantic_scholar_author_context(author['authorId'])

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

def semantic_scholar_author_context(author_id):
    global driver
    requests_session = requests.Session()
    url = f"https://api.semanticscholar.org/graph/v1/author/{author_id}"
    params = {
        "fields": ("authorId,url,name,paperCount,citationCount,"
                    "papers.title,"
                    "papers.authors,"
                    "papers.year,"
                    "papers.paperId,"
                    "papers.citationCount,"
                    "papers.referenceCount,"
                    "papers.venue,"
                    "papers.abstract")
    }
    # add headers
    headers = {
        "x-api-key": x_api_key,
    }
    print(url)
    response = requests_session.get(url, params=params, headers=headers)

    # check for 200 response
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.reason}", style=prompt_style)
        # close requests session
        requests_session.close()
        return

    author_dict = response.json()
    
    # display author details
    print(HTML(f"<blue>Showing details for author</blue> {author_dict['name']} :"), style=prompt_style)
    print(HTML(f'<blue>\tName:</blue> {author_dict["name"]}'), style=prompt_style)
    print(HTML(f'<blue>\tURL:</blue> {author_dict["url"]}'), style=prompt_style)
    print(HTML(f'<blue>\tPaper Count:</blue> {author_dict["paperCount"]}'), style=prompt_style)
    print(HTML(f'<blue>\tCitation Count:</blue> {author_dict["citationCount"]}'), style=prompt_style)
    print(HTML(f'<blue>\tAuthor ID:</blue> {author_dict["authorId"]}'), style=prompt_style)
    print(HTML(f'<blue>\tPapers:</blue> '), style=prompt_style)
    for paper in author_dict["papers"]:
        print(f'\t\t- {paper["title"]}, {paper["year"]}, {paper["venue"]}', style=prompt_style)
    
    # prompt for what to do next
    context_path = f"(Semantic Scholar > Author > {author_dict['authorId']})"
    prompt_text = [
        ('class:green', f'\n{context_path} >>> '),
    ]
    print(HTML("\n<blue>What would you like to do next?:</blue>"), style=prompt_style)
    print("\tEnter 'g' to add this author and their papers to the graph")
    print(HTML("\tEnter 'a' to add this author, their papers, and all citations and references to graph <red>WARNING: this may take a long time!</red>"), style=prompt_style)
    print("\tEnter 'q' to return to main menu")
    selection = prompt_session.prompt(prompt_text, style=prompt_style)

    # add paper to graph
    if selection.lower() == "g":
        for paper_dict in author_dict["papers"]:
            paper = Paper(paper_dict)
            # create paper node
            add_paper_to_graph(paper)
    elif selection.lower() == "a":
        for paper_dict in author_dict["papers"]:
            paper = Paper(paper_dict)
            # create paper node
            add_paper_to_graph(paper)
            # add citations and references
            add_references(paper.id)
    else:
        pass

    # close requests session
    requests_session.close()

def semantic_scholar_paper_context(paper_id):
    global driver
    requests_session = requests.Session()
    url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}"
    params = {
        "fields": "title,authors,year,citationCount,referenceCount,venue,paperId,tldr,abstract,url",
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

    paper_dict = response.json()
    
    # create paper object and display details
    paper = Paper(paper_dict)
    print(HTML(f"<blue>Showing details for paper</blue> \"{paper.title}\" :"), style=prompt_style)
    print(HTML(f'<blue>\tTitle:</blue> {paper.title}'), style=prompt_style)
    print(HTML(f'<blue>\tURL:</blue> {paper.url}'), style=prompt_style)
    print(HTML(f'<blue>\tAuthors:</blue> '), style=prompt_style)
    for author in paper.authors:
        print(f'\t\t{author["name"]}', style=prompt_style)
    print(HTML(f'<blue>\tYear:</blue> {paper.year}'), style=prompt_style)
    print(HTML(f'<blue>\tCitation Count:</blue> {paper.citation_count}'), style=prompt_style)
    print(HTML(f'<blue>\tVenue:</blue> {paper.venue}'), style=prompt_style)
    print(HTML(f'<blue>\tPaper ID:</blue> {paper.id}'), style=prompt_style)
    print(HTML(f'<blue>\tTLDR:</blue> {paper.tldr}'), style=prompt_style)
    print(HTML(f'<blue>\tAbstract:</blue> {paper.abstract}'), style=prompt_style)
    
    # prompt for what to do next
    context_path = f"(Semantic Scholar > Paper > {paper.id})"
    prompt_text = [
        ('class:green', f'\n{context_path} >>> '),
    ]
    print(HTML("\n<blue>What would you like to do next?:</blue>"), style=prompt_style)
    print("\tEnter 'g' to add this paper to the graph")
    print(HTML("\tEnter 'a' to this paper along with citations and references to graph <red>WARNING: this may take a long time!</red>"), style=prompt_style)
    print("\tEnter 'q' to return to main menu")
    selection = prompt_session.prompt(prompt_text, style=prompt_style)

    # add paper to graph
    if selection.lower() == "g":
        # create paper node
        add_paper_to_graph(paper)

    elif selection.lower() == "a":
        # create paper node
        add_paper_to_graph(paper)

        # add citations and references
        add_references(paper.id)
    else:
        pass

    # close requests session
    requests_session.close()

def search_semantic_refresh_references():
    """Refresh the references for all papers in the graph database"""
    global driver

    print("Refreshing references for all papers in the graph database...", style=prompt_style)

    # get all paper ids
    query_text = (
        "MATCH (p:Paper) "
        "RETURN p.PaperId"
    )
    records, _, _ = driver.execute_query(query_text)
    paper_ids = [record["p.PaperId"] for record in records]
    print(f"Found {len(paper_ids)} papers in the graph database", style=prompt_style)

    with ProcessPoolExecutor(10) as executor:
        list(tqdm(executor.map(add_references, paper_ids), total=len(paper_ids)))


    # for paper_id in tqdm(paper_ids):
    #     add_references(paper_id, verbose=False)    

    print("Done!", style=prompt_style)

@on_exception(expo, RateLimitException, max_tries=8)
@limits(calls=5000, period=60)
def add_references(paper_id, verbose=False):
    """
    Add citations and references to the graph database
    INPUT: paper_id - the id of the paper to add references for
    """
    global driver
    requests_session = requests.Session()

    num_nodes = 0
    num_relationships = 0

    # get references for paper
    for operation in ["citations", "references"]:
        references = [] # also used for citations
        offset = 0
        while (1):
            url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}/{operation}"
            params = {
                "fields": "title,authors,year,venue,paperId,abstract,url,citationCount,referenceCount",
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

            # add the references to the list
            references.extend(response.json()["data"])

            # check if there are more references
            if 'next' not in response.json():
                break    

            offset += 100

        # add each reference to the graph and create relationship
        for reference in references:
            if operation == "citations":
                ref_paper = Paper(reference["citingPaper"])
                add_paper_to_graph(ref_paper, verbose=False)

                # create relationship between paper and references
                query_text = (
                        "MATCH (p:Paper {PaperId: $paperId}) "
                        "MATCH (r:Paper {PaperId: $refId}) "
                        "MERGE (p)<-[:REFERENCES]-(r)"
                    )
                summary = driver.execute_query(query_text, paperId=paper_id, refId=ref_paper.id)
                num_nodes += summary.summary.counters.nodes_created
                num_relationships += summary.summary.counters.relationships_created   

            else:
                ref_paper = Paper(reference["citedPaper"])
                add_paper_to_graph(ref_paper, verbose=False)

                # create relationship between paper and references
                query_text = (
                        "MATCH (p:Paper {PaperId: $paperId}) "
                        "MATCH (r:Paper {PaperId: $refId}) "
                        "MERGE (p)-[:REFERENCES]->(r)"
                    )
                summary = driver.execute_query(query_text, paperId=paper_id, refId=ref_paper.id)
                num_nodes += summary.summary.counters.nodes_created
                num_relationships += summary.summary.counters.relationships_created
    if verbose:
        print(f"Added {num_nodes} nodes and {num_relationships} relationships to the graph!", style=prompt_style)      

@on_exception(expo, RateLimitException, max_tries=8)
@limits(calls=5000, period=60)
def add_paper_to_graph(paper, verbose=False, add_keywords=False):
    """
    Add a paper to the graph database. Also adds authors, venues, and keywords along with relationships.
    INPUT: paper - Paper class object
    """
    global driver

    num_nodes = 0
    num_relationships = 0
    if verbose:
        print("Adding paper to graph...", style=prompt_style)

    # create paper node
    query_text = (
        "MERGE (p:Paper {PaperId: $paperId}) "
        "SET p.Title=$title "
        "SET p.Year = $year "
        "SET p.Venue = $venue "
        "SET p.PrimaryAuthor = $author "
        "SET p.URL = $url "
        "SET p.TLDR = $tldr "
        "SET p.Abstract = $abstract "
        "SET p.CitationCount = $citationCount "
        "SET p.ReferenceCount = $referenceCount "
    )

    summary = driver.execute_query(query_text, 
                                paperId = paper.id,
                                title = paper.title,
                                year = paper.year,
                                venue = paper.venue,
                                author = paper.author,
                                url = paper.url,
                                tldr = paper.tldr,
                                abstract = paper.abstract,
                                citationCount = paper.citation_count,
                                referenceCount = paper.reference_count
                            )
    num_nodes += summary.summary.counters.nodes_created
    num_relationships += summary.summary.counters.relationships_created

    # create author nodes and relationship to paper
    for author in paper.authors:
        author_id = author["id"]
        author_name = author["name"]
        
        query_text = (
            "MERGE (a:Author {AuthorId: $authorId}) "
            "SET a.Name = $name "
        )

        summary = driver.execute_query(query_text, authorId=author_id, name=author_name)
        num_nodes += summary.summary.counters.nodes_created
        num_relationships += summary.summary.counters.relationships_created

        query_text = (
            "MATCH (p:Paper {PaperId: $paperId}) "
            "MATCH (a:Author {AuthorId: $authorId}) "
            "MERGE (p)-[:AUTHORED_BY]->(a) "
        )
        summary = driver.execute_query(query_text,
                                authorId = author_id,
                                paperId = paper.id
                            )
        num_nodes += summary.summary.counters.nodes_created
        num_relationships += summary.summary.counters.relationships_created

    # create venue node and relationship to paper
    if paper.venue != "":
        query_text = (
            "MERGE (v:Venue {Name: $name}) "
        )
        summary = driver.execute_query(query_text, name=paper.venue)
        num_nodes += summary.summary.counters.nodes_created
        num_relationships += summary.summary.counters.relationships_created

        query_text = (
            "MATCH (v:Venue {Name: $name}) "
            "MATCH (p:Paper {PaperId: $paperId}) "
            "MERGE (p)-[:PUBLISHED_IN]->(v) "
        )
        summary = driver.execute_query(query_text, name=paper.venue, paperId=paper.id)
        num_nodes += summary.summary.counters.nodes_created
        num_relationships += summary.summary.counters.relationships_created

    if add_keywords:    
        # create keyword nodes from abstract, title, and tldr
        # tokenize the text
        tokens = text_tokenization(paper.abstract + " " + paper.title + " " + paper.tldr)

        # create keyword nodes and add relationships
        for token in tokens:
            query_text = (
                "MERGE (k:Keyword {Value: $token}) "
            )
            summary = driver.execute_query(query_text, token=token)
            num_nodes += summary.summary.counters.nodes_created
            num_relationships += summary.summary.counters.relationships_created
            query_text = (
                "MATCH (k:Keyword {Value: $token}) "
                "MATCH (p:Paper {PaperId: $paperId}) "
                "MERGE (p)-[:HAS_KEYWORD]->(k) "
            )
            summary = driver.execute_query(query_text, token=token, paperId=paper.id)
            num_nodes += summary.summary.counters.nodes_created
            num_relationships += summary.summary.counters.relationships_created    

    if verbose:
        print(f"Added {num_nodes} nodes and {num_relationships} relationships to the graph!", style=prompt_style)

def text_tokenization(text):
    """
    Tokenize text
    INPUT: text - a string of text to be tokenized
    OUTPUT: filtered_tokens - a list of tokens that have been tokenized, lemmatized, and filtered for stop words
    """
    # Get the list of stopwords
    stopwords = nltk.corpus.stopwords.words("english")

    # Create a lemmatizer object
    lemmatizer = nltk.WordNetLemmatizer()


    # Create a translation table that maps punctuation characters to None
    table = str.maketrans('', '', string.punctuation)

    # Translate the text, replacing all punctuation characters with empty strings
    translated_text = text.translate(table)

    # Tokenize the text
    tokens = nltk.word_tokenize(translated_text)

    # Lemmatize the tokens
    tokens = [lemmatizer.lemmatize(token.lower(), 'v') for token in tokens]
    tokens = [lemmatizer.lemmatize(token.lower(), 'n') for token in tokens]
    tokens = [lemmatizer.lemmatize(token.lower(), 'a') for token in tokens]
    tokens = [lemmatizer.lemmatize(token.lower(), 's') for token in tokens]

    # Remove stop words from the tokens
    filtered_tokens = [token.lower() for token in tokens if token not in stopwords]

    # remove duplicates
    filtered_tokens = list(set(filtered_tokens))

    return filtered_tokens

def search_local_database():
    """Search the local database for a paper or any other entity"""
    print(HTML('<red>Not implemented yet!</red>'), style=prompt_style)

def modify_database():
    """Manually modify the local database (add notes, delete nodes, etc.))"""
    print(HTML('<red>Not implemented yet!</red>'), style=prompt_style)

def main_menu():
    # main loop - this is mostly a placeholder until we have more functionality. For now it just calls search_semantic_scholar()
    selection = ""
    while selection.lower() not in ["quit", "exit", "4"]: 

        context_path = ""
        prompt_text = [
            ('class:green', f'\n{context_path} >>> '),
    ]
        print()
        search_semantic_scholar()
        break
        # print()
        # print(HTML("<blue>What would you like to do?</blue>"), style=prompt_style)
        # print()
        
        # print("\t1. Search Semantic Scholar", style=prompt_style)
        # print("\t2. Search local database", style=prompt_style)
        # print("\t3. Manually modify database (advanced)", style=prompt_style)
        # print("\t4. 'q' (or anything else) to exit", style=prompt_style)


        # selection = prompt_session.prompt(prompt_text, style=prompt_style)
        
        # if selection == "1":
        #     search_semantic_scholar()
        # elif selection == "2":
        #     search_local_database()
        # elif selection == "3":
        #     modify_database()
        # else:
        #     break

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
