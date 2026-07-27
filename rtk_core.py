"""
rtk_core.py — Reusable business logic extracted from rtk.py
Provides Paper class, API wrappers, graph operations, and text processing.
"""

import os
import hashlib
import html
import time
import string

import requests
import nltk
from ratelimit import limits, RateLimitException
from backoff import on_exception, expo
from dotenv import load_dotenv

from graph_store import GraphStore

# Ensure NLTK data is available
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)


# --- Rate-limited API wrapper ---

class S2ServerError(Exception):
    """Raised when Semantic Scholar returns a transient 500 error."""
    pass


@on_exception(expo, (RateLimitException, S2ServerError), max_tries=8)
@limits(calls=1, period=1)
def s2_api_get(session, url, params, headers):
    """Rate-limited wrapper for all Semantic Scholar API GET requests (1 req/sec)."""
    response = session.get(url, params=params, headers=headers)
    if response.status_code == 429:
        raise RateLimitException("API returned 429", period_remaining=1)
    if response.status_code == 500:
        raise S2ServerError("API returned 500")
    return response


# --- Paper class ---

class Paper:
    """Represents a paper from Semantic Scholar."""

    def __init__(self, paper_dict):
        if 'title' not in paper_dict or paper_dict['title'] is None:
            self.title = None
            return
        self.title = html.escape(paper_dict['title'])

        # primary author
        if 'authors' in paper_dict and len(paper_dict['authors']) > 0:
            self.author = html.escape(paper_dict['authors'][0]['name'])
        else:
            self.author = "unknown"

        # all authors
        self.authors = []
        for author in paper_dict.get("authors", []):
            if 'authorId' in author and author['authorId'] is not None:
                author_id = author['authorId']
            elif 'name' in author and author['name'] is not None:
                author_id = self._sha1(author['name'])
            else:
                continue
            author_name = html.escape(author['name']) if author.get('name') else "unknown"
            self.authors.append({"id": author_id, "name": author_name})

        # paper id
        if 'paperId' in paper_dict and paper_dict['paperId'] is not None:
            self.id = paper_dict['paperId']
        else:
            self.id = self._sha1(self.title + self.author)

        # optional fields
        self.year = paper_dict.get('year') or 0
        self.venue = html.escape(paper_dict['venue']) if paper_dict.get('venue') else ""
        self.abstract = html.escape(paper_dict['abstract']) if paper_dict.get('abstract') else ""
        self.url = paper_dict.get('url') or ""
        self.citation_count = paper_dict.get('citationCount') or 0
        self.reference_count = paper_dict.get('referenceCount') or 0

        if paper_dict.get('tldr') and paper_dict['tldr'].get('text'):
            self.tldr = html.escape(paper_dict['tldr']['text'])
        else:
            self.tldr = ""

    def _sha1(self, text):
        return hashlib.sha1(text.encode()).hexdigest()

    def __repr__(self):
        return f"Paper(title={self.title}, author={self.author}, year={self.year}, id={self.id})"


# --- RTK Core Engine ---

class RTKCore:
    """Core engine that holds state (graph store, API key, tags) and provides operations."""

    def __init__(self):
        load_dotenv()
        self.graph = GraphStore()
        self.x_api_key = os.environ.get("S2_API_KEY")
        self.project_tags = []

    def close(self):
        pass

    # --- Search operations ---

    def search_papers(self, keyword, field_of_study=None, offset=0, limit=10):
        """Search Semantic Scholar by keyword. Returns (results_list, total_count) or error string."""
        session = requests.Session()
        try:
            url = "https://api.semanticscholar.org/graph/v1/paper/search"
            params = {
                "query": keyword,
                "offset": offset,
                "fields": "title,authors,year,paperId,fieldsOfStudy",
                "limit": limit
            }
            if field_of_study:
                params["fieldsOfStudy"] = field_of_study
            headers = {"x-api-key": self.x_api_key}
            try:
                response = s2_api_get(session, url, params, headers)
            except S2ServerError:
                return None, "Error: Semantic Scholar server error (500). Try again in a moment."

            if response.status_code != 200:
                return None, f"Error: {response.status_code} - {response.reason} - {response.text}"

            data = response.json()
            return data.get("data", []), data.get("total", 0)
        finally:
            session.close()

    def search_authors(self, name, offset=0, limit=10):
        """Search Semantic Scholar by author name. Returns (results_list, total_count) or error string."""
        session = requests.Session()
        try:
            url = "https://api.semanticscholar.org/graph/v1/author/search"
            params = {
                "query": name,
                "offset": offset,
                "fields": "authorId,url,name,paperCount,citationCount",
                "limit": limit,
            }
            headers = {"x-api-key": self.x_api_key}
            try:
                response = s2_api_get(session, url, params, headers)
            except S2ServerError:
                return None, "Error: Semantic Scholar server error (500). Try again in a moment."

            if response.status_code != 200:
                return None, f"Error: {response.status_code} - {response.reason} - {response.text}"

            data = response.json()
            return data.get("data", []), data.get("total", 0)
        finally:
            session.close()

    def get_paper(self, paper_id):
        """Get paper details by ID. Returns Paper object or error string."""
        session = requests.Session()
        try:
            url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}"
            params = {"fields": "title,authors,year,citationCount,referenceCount,venue,paperId,tldr,abstract,url"}
            headers = {"x-api-key": self.x_api_key}
            try:
                response = s2_api_get(session, url, params, headers)
            except S2ServerError:
                return None, "Error: Semantic Scholar server error (500). Try again in a moment."

            if response.status_code != 200:
                return None, f"Error: {response.status_code} - {response.reason} - {response.text}"

            paper = Paper(response.json())
            if paper.title is None:
                return None, "Paper has no title"
            return paper, None
        finally:
            session.close()

    def get_author(self, author_id):
        """Get author details by ID. Returns author dict or error string."""
        session = requests.Session()
        try:
            url = f"https://api.semanticscholar.org/graph/v1/author/{author_id}"
            params = {
                "fields": ("authorId,url,name,paperCount,citationCount,"
                           "papers.title,papers.authors,papers.year,papers.paperId,"
                           "papers.citationCount,papers.referenceCount,papers.venue,papers.abstract")
            }
            headers = {"x-api-key": self.x_api_key}
            try:
                response = s2_api_get(session, url, params, headers)
            except S2ServerError:
                return None, "Error: Semantic Scholar server error (500). Try again in a moment."

            if response.status_code != 200:
                return None, f"Error: {response.status_code} - {response.reason} - {response.text}"

            return response.json(), None
        finally:
            session.close()

    # --- Graph operations ---

    def add_paper_to_graph(self, paper, add_keywords=False, emit=None):
        """Add a paper (and its authors, venue, tags, keywords) to the graph."""
        num_nodes = 0
        num_rels = 0

        # Paper node
        paper_id = paper.id
        created = self.graph.merge_node(paper_id, "Paper", {
            "PaperId": paper.id,
            "Title": paper.title,
            "Year": paper.year,
            "Venue": paper.venue,
            "PrimaryAuthor": paper.author,
            "URL": paper.url,
            "TLDR": paper.tldr,
            "Abstract": paper.abstract,
            "CitationCount": paper.citation_count,
            "ReferenceCount": paper.reference_count,
        })
        if created:
            num_nodes += 1

        # Tags
        for tag in self.project_tags:
            tag_id = "tag:" + tag
            if self.graph.merge_node(tag_id, "Tag", {"Tag": tag}):
                num_nodes += 1
            if self.graph.merge_edge(paper_id, tag_id, "TAGGED"):
                num_rels += 1

        # Authors
        for author in paper.authors:
            author_id = author["id"]
            if self.graph.merge_node(author_id, "Author", {"AuthorId": author["id"], "Name": author["name"]}):
                num_nodes += 1
            if self.graph.merge_edge(paper_id, author_id, "AUTHORED_BY"):
                num_rels += 1
            for tag in self.project_tags:
                tag_id = "tag:" + tag
                if self.graph.merge_edge(author_id, tag_id, "TAGGED"):
                    num_rels += 1

        # Venue
        if paper.venue:
            venue_id = "venue:" + paper.venue
            if self.graph.merge_node(venue_id, "Venue", {"Name": paper.venue}):
                num_nodes += 1
            if self.graph.merge_edge(paper_id, venue_id, "PUBLISHED_IN"):
                num_rels += 1
            for tag in self.project_tags:
                tag_id = "tag:" + tag
                if self.graph.merge_edge(venue_id, tag_id, "TAGGED"):
                    num_rels += 1

        # Keywords
        if add_keywords:
            tokens = text_tokenization(paper.abstract + " " + paper.title + " " + paper.tldr)
            for token in tokens:
                kw_id = "kw:" + token
                self.graph.merge_node(kw_id, "Keyword", {"Value": token})
                self.graph.merge_edge(paper_id, kw_id, "HAS_KEYWORD")

        return num_nodes, num_rels

    def add_references(self, paper_id, add_keywords=False, operations=None, emit=None):
        """
        Fetch citations/references from S2 API and add to graph.
        emit: optional callback(str) to send progress messages.
        """
        if operations is None:
            operations = ["citations", "references"]

        session = requests.Session()
        total_nodes = 0
        total_rels = 0

        try:
            for operation in operations:
                references = []
                offset = 0
                if emit:
                    emit(f"Getting {operation} for paper {paper_id}...")

                while True:
                    url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}/{operation}"
                    params = {
                        "fields": "title,authors,year,venue,paperId,abstract,url,citationCount,referenceCount",
                        "limit": 100,
                        "offset": offset
                    }
                    headers = {"x-api-key": self.x_api_key}
                    try:
                        response = s2_api_get(session, url, params, headers)
                    except S2ServerError:
                        if emit:
                            emit(f"Server error fetching {operation}. Retries exhausted.")
                        break

                    if response.status_code != 200:
                        if emit:
                            emit(f"Error: {response.status_code} - {response.reason} - {response.text}")
                        break

                    response_json = response.json()
                    response_data = response_json.get("data")
                    if response_data is None:
                        if emit:
                            emit(f"No {operation} data available for paper {paper_id}")
                        break

                    references.extend(response_data)
                    if 'next' not in response_json:
                        break
                    offset += 100
                    if emit:
                        emit(f"Received {offset} {operation}, fetching next batch...")
                    time.sleep(1)

                # Add to graph
                for i, reference in enumerate(references):
                    try:
                        if operation == "citations":
                            ref_paper = Paper(reference["citingPaper"])
                        else:
                            ref_paper = Paper(reference["citedPaper"])

                        if ref_paper.title is None:
                            continue

                        n, r = self.add_paper_to_graph(ref_paper, add_keywords=add_keywords)
                        total_nodes += n
                        total_rels += r

                        if operation == "citations":
                            if self.graph.merge_edge(ref_paper.id, paper_id, "REFERENCES"):
                                total_rels += 1
                        else:
                            if self.graph.merge_edge(paper_id, ref_paper.id, "REFERENCES"):
                                total_rels += 1
                    except (KeyError, TypeError):
                        continue

                    if emit and (i + 1) % 20 == 0:
                        emit(f"Added {i + 1}/{len(references)} {operation}...")

                if emit:
                    emit(f"Done adding {len(references)} {operation}.")
        finally:
            session.close()

        return total_nodes, total_rels

    def set_tags(self, tags_str):
        """Set project tags from comma-separated string."""
        self.project_tags = [t.strip() for t in tags_str.split(",") if t.strip()]
        return self.project_tags


# --- Text processing ---

def text_tokenization(text):
    """Tokenize, lemmatize, and filter stopwords from text."""
    stopwords = nltk.corpus.stopwords.words("english")
    lemmatizer = nltk.WordNetLemmatizer()
    table = str.maketrans('', '', string.punctuation)
    translated = text.translate(table)
    tokens = nltk.word_tokenize(translated)

    tokens = [lemmatizer.lemmatize(t.lower(), 'v') for t in tokens]
    tokens = [lemmatizer.lemmatize(t.lower(), 'n') for t in tokens]
    tokens = [lemmatizer.lemmatize(t.lower(), 'a') for t in tokens]
    tokens = [lemmatizer.lemmatize(t.lower(), 's') for t in tokens]

    filtered = [t for t in tokens if t not in stopwords]
    return list(set(filtered))
