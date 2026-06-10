"""
command_handler.py — Parses single-line commands from the browser console
and dispatches them to RTKCore methods.
"""

from rtk_core import RTKCore, Paper


class CommandHandler:
    """Handles text commands from the browser console."""

    def __init__(self, core):
        self.core = core
        # Holds the last search/author results for selection
        self._last_results = []
        self._last_result_type = None  # "papers" or "authors"
        self._last_query = None
        self._last_offset = 0
        self._last_total = 0
        self._limit = 10

    def handle(self, command_str, emit):
        """
        Parse and execute a command. 
        emit(str) is called for each line of output to send to the browser.
        """
        parts = command_str.strip().split(None, 1)
        if not parts:
            return

        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if cmd == "help":
            self._help(emit)
        elif cmd == "search":
            self._search_papers(args, emit)
        elif cmd == "author":
            self._search_authors(args, emit)
        elif cmd == "paper":
            self._paper_details(args, emit)
        elif cmd == "select":
            self._select(args, emit)
        elif cmd == "next":
            self._next_page(emit)
        elif cmd == "prev":
            self._prev_page(emit)
        elif cmd == "add":
            self._add_to_graph(args, emit)
        elif cmd == "tags":
            self._set_tags(args, emit)
        elif cmd == "graph":
            self._graph_cmd(args, emit)
        elif cmd == "status":
            self._status(emit)
        else:
            emit(f"\x1b[31mUnknown command: {cmd}\x1b[0m")
            emit("Type \x1b[33mhelp\x1b[0m for available commands.")

    def _help(self, emit):
        emit("")
        emit("\x1b[1;36mResearcher's Toolkit — Commands\x1b[0m")
        emit("  \x1b[33msearch <keywords>\x1b[0m      Search papers by keyword")
        emit("  \x1b[33mauthor <name>\x1b[0m          Search authors by name")
        emit("  \x1b[33mpaper <id>\x1b[0m             Show paper details by ID")
        emit("  \x1b[33mselect <#>\x1b[0m             Select item from last search results")
        emit("  \x1b[33mnext\x1b[0m                   Next page of results")
        emit("  \x1b[33mprev\x1b[0m                   Previous page of results")
        emit("  \x1b[33madd <mode>\x1b[0m             Add last viewed paper to graph")
        emit("                          modes: graph, refs, cites, all")
        emit("                          append 'k' for keywords: graphk, refsk, citesk, allk")
        emit("  \x1b[33mgraph load\x1b[0m             Load and display the graph")
        emit("  \x1b[33mgraph clear\x1b[0m            Clear the graph display")
        emit("  \x1b[33mgraph stats\x1b[0m            Show database node/edge counts")
        emit("  \x1b[33mgraph reset\x1b[0m            Delete ALL data from database")
        emit("  \x1b[33mtags <tag1,tag2,...>\x1b[0m   Set project tags")
        emit("  \x1b[33mstatus\x1b[0m                 Show connection status and current tags")
        emit("")

    def _search_papers(self, keyword, emit):
        if not keyword:
            emit("\x1b[31mUsage: search <keywords>\x1b[0m")
            return

        emit(f"Searching for '{keyword}'...")
        results, total = self.core.search_papers(keyword, offset=0, limit=self._limit)

        if results is None:
            emit(f"\x1b[31m{total}\x1b[0m")  # total contains error string
            return

        if total == 0:
            emit(f"No results for '{keyword}'")
            return

        self._last_results = results
        self._last_result_type = "papers"
        self._last_query = keyword
        self._last_offset = 0
        self._last_total = total
        self._display_paper_results(emit)

    def _search_authors(self, name, emit):
        if not name:
            emit("\x1b[31mUsage: author <name>\x1b[0m")
            return

        emit(f"Searching authors for '{name}'...")
        results, total = self.core.search_authors(name, offset=0, limit=self._limit)

        if results is None:
            emit(f"\x1b[31m{total}\x1b[0m")
            return

        if total == 0:
            emit(f"No results for '{name}'")
            return

        self._last_results = results
        self._last_result_type = "authors"
        self._last_query = name
        self._last_offset = 0
        self._last_total = total
        self._display_author_results(emit)

    def _paper_details(self, paper_id, emit):
        if not paper_id:
            emit("\x1b[31mUsage: paper <paper_id>\x1b[0m")
            return

        emit(f"Fetching paper {paper_id}...")
        paper, error = self.core.get_paper(paper_id.strip())
        if error:
            emit(f"\x1b[31m{error}\x1b[0m")
            return

        self._last_paper = paper
        self._display_paper_detail(paper, emit)

    def _select(self, index_str, emit):
        if not self._last_results:
            emit("\x1b[31mNo results to select from. Run a search first.\x1b[0m")
            return

        try:
            idx = int(index_str)
        except (ValueError, TypeError):
            emit("\x1b[31mUsage: select <number>\x1b[0m")
            return

        local_idx = idx - self._last_offset
        if local_idx < 0 or local_idx >= len(self._last_results):
            emit(f"\x1b[31mInvalid selection: {idx}\x1b[0m")
            return

        item = self._last_results[local_idx]

        if self._last_result_type == "papers":
            paper_id = item.get("paperId")
            if paper_id:
                self._paper_details(paper_id, emit)
        elif self._last_result_type == "authors":
            author_id = item.get("authorId")
            if author_id:
                self._author_details(author_id, emit)

    def _next_page(self, emit):
        if not self._last_query:
            emit("\x1b[31mNo active search to paginate.\x1b[0m")
            return

        new_offset = self._last_offset + self._limit
        if new_offset >= self._last_total:
            emit("No more results.")
            return

        self._last_offset = new_offset
        if self._last_result_type == "papers":
            results, total = self.core.search_papers(self._last_query, offset=new_offset, limit=self._limit)
            if results is None:
                emit(f"\x1b[31m{total}\x1b[0m")
                return
            self._last_results = results
            self._last_total = total
            self._display_paper_results(emit)
        elif self._last_result_type == "authors":
            results, total = self.core.search_authors(self._last_query, offset=new_offset, limit=self._limit)
            if results is None:
                emit(f"\x1b[31m{total}\x1b[0m")
                return
            self._last_results = results
            self._last_total = total
            self._display_author_results(emit)

    def _prev_page(self, emit):
        if not self._last_query:
            emit("\x1b[31mNo active search to paginate.\x1b[0m")
            return

        new_offset = self._last_offset - self._limit
        if new_offset < 0:
            new_offset = 0

        if new_offset == self._last_offset:
            emit("Already at the first page.")
            return

        self._last_offset = new_offset
        if self._last_result_type == "papers":
            results, total = self.core.search_papers(self._last_query, offset=new_offset, limit=self._limit)
            if results is None:
                emit(f"\x1b[31m{total}\x1b[0m")
                return
            self._last_results = results
            self._last_total = total
            self._display_paper_results(emit)
        elif self._last_result_type == "authors":
            results, total = self.core.search_authors(self._last_query, offset=new_offset, limit=self._limit)
            if results is None:
                emit(f"\x1b[31m{total}\x1b[0m")
                return
            self._last_results = results
            self._last_total = total
            self._display_author_results(emit)

    def _add_to_graph(self, mode, emit):
        if not hasattr(self, '_last_paper') or self._last_paper is None:
            emit("\x1b[31mNo paper selected. Use 'paper <id>' or 'select <#>' first.\x1b[0m")
            return

        mode = mode.strip().lower() if mode else "graph"
        add_keywords = mode.endswith("k")
        if add_keywords:
            mode = mode[:-1]

        paper = self._last_paper

        if mode in ("graph", ""):
            emit(f"Adding '{paper.title}' to graph...")
            nodes, rels = self.core.add_paper_to_graph(paper, add_keywords=add_keywords)
            emit(f"\x1b[32mDone! Added {nodes} nodes and {rels} relationships.\x1b[0m")

        elif mode == "all":
            emit(f"Adding '{paper.title}' with citations and references...")
            self.core.add_paper_to_graph(paper, add_keywords=add_keywords)
            nodes, rels = self.core.add_references(paper.id, add_keywords=add_keywords, emit=emit)
            emit(f"\x1b[32mDone! Added {nodes} nodes and {rels} relationships.\x1b[0m")

        elif mode == "cites":
            emit(f"Adding '{paper.title}' with citations...")
            self.core.add_paper_to_graph(paper, add_keywords=add_keywords)
            nodes, rels = self.core.add_references(paper.id, add_keywords=add_keywords, operations=["citations"], emit=emit)
            emit(f"\x1b[32mDone! Added {nodes} nodes and {rels} relationships.\x1b[0m")

        elif mode == "refs":
            emit(f"Adding '{paper.title}' with references...")
            self.core.add_paper_to_graph(paper, add_keywords=add_keywords)
            nodes, rels = self.core.add_references(paper.id, add_keywords=add_keywords, operations=["references"], emit=emit)
            emit(f"\x1b[32mDone! Added {nodes} nodes and {rels} relationships.\x1b[0m")

        else:
            emit(f"\x1b[31mUnknown add mode: {mode}\x1b[0m")
            emit("  Modes: graph, refs, cites, all (append 'k' for keywords)")

    def _set_tags(self, tags_str, emit):
        if not tags_str:
            if self.core.project_tags:
                emit(f"Current tags: {', '.join(self.core.project_tags)}")
            else:
                emit("No tags set. Usage: tags <tag1,tag2,...>")
            return

        tags = self.core.set_tags(tags_str)
        emit(f"\x1b[32mTags set: {', '.join(tags)}\x1b[0m")

    def _graph_cmd(self, args, emit):
        subcmd = args.strip().lower() if args else ""
        if subcmd == "load":
            # The actual loading is done client-side via JS fetch
            emit("__GRAPH_LOAD__")
        elif subcmd == "clear":
            emit("__GRAPH_CLEAR__")
        elif subcmd == "stats":
            emit("__GRAPH_STATS__")
        elif subcmd == "reset":
            emit("__GRAPH_RESET__")
        else:
            emit("\x1b[31mUsage: graph load | graph clear | graph stats | graph reset\x1b[0m")

    def _status(self, emit):
        emit("\x1b[1;36mStatus\x1b[0m")
        try:
            self.core.driver.verify_connectivity()
            emit("  Neo4j: \x1b[32mconnected\x1b[0m")
        except Exception:
            emit("  Neo4j: \x1b[31mdisconnected\x1b[0m")
        emit(f"  API Key: {'set' if self.core.x_api_key else 'not set'}")
        emit(f"  Tags: {', '.join(self.core.project_tags) if self.core.project_tags else '(none)'}")

    def _author_details(self, author_id, emit):
        emit(f"Fetching author {author_id}...")
        author_dict, error = self.core.get_author(author_id)
        if error:
            emit(f"\x1b[31m{error}\x1b[0m")
            return

        emit(f"\x1b[1;36m{author_dict['name']}\x1b[0m")
        emit(f"  Papers: {author_dict.get('paperCount', 0)}")
        emit(f"  Citations: {author_dict.get('citationCount', 0)}")
        emit(f"  URL: {author_dict.get('url', '')}")
        emit(f"  ID: {author_dict.get('authorId', '')}")
        emit("")
        papers = author_dict.get("papers", [])
        if papers:
            emit(f"  Papers ({len(papers)}):")
            for p in papers[:20]:
                year = p.get("year") or "?"
                emit(f"    - {p.get('title', 'Untitled')} ({year})")
            if len(papers) > 20:
                emit(f"    ... and {len(papers) - 20} more")

    # --- Display helpers ---

    def _display_paper_results(self, emit):
        offset = self._last_offset
        total = self._last_total
        emit("")
        emit(f"\x1b[36mShowing papers {offset + 1}-{offset + len(self._last_results)} of {total}:\x1b[0m")
        for i, paper in enumerate(self._last_results):
            title = paper.get("title", "Untitled")
            authors = paper.get("authors", [])
            author = authors[0]["name"] if authors else "unknown"
            year = paper.get("year") or "?"
            emit(f"  \x1b[33m{i + offset}\x1b[0m: {title}, {author}, {year}")
        emit("")
        emit("Use \x1b[33mselect <#>\x1b[0m to view details, \x1b[33mnext\x1b[0m/\x1b[33mprev\x1b[0m to paginate.")

    def _display_author_results(self, emit):
        offset = self._last_offset
        total = self._last_total
        emit("")
        emit(f"\x1b[36mShowing authors {offset + 1}-{offset + len(self._last_results)} of {total}:\x1b[0m")
        for i, author in enumerate(self._last_results):
            name = author.get("name", "Unknown")
            papers = author.get("paperCount", 0)
            cites = author.get("citationCount", 0)
            emit(f"  \x1b[33m{i + offset}\x1b[0m: {name}, {papers} papers, {cites} citations")
        emit("")
        emit("Use \x1b[33mselect <#>\x1b[0m to view details, \x1b[33mnext\x1b[0m/\x1b[33mprev\x1b[0m to paginate.")

    def _display_paper_detail(self, paper, emit):
        emit("")
        emit(f"\x1b[1;36m{paper.title}\x1b[0m")
        emit(f"  Authors: {', '.join(a['name'] for a in paper.authors)}")
        emit(f"  Year: {paper.year}")
        emit(f"  Venue: {paper.venue}")
        emit(f"  Citations: {paper.citation_count}  References: {paper.reference_count}")
        emit(f"  ID: {paper.id}")
        emit(f"  URL: {paper.url}")
        if paper.tldr:
            emit(f"  TLDR: {paper.tldr}")
        if paper.abstract:
            abstract = paper.abstract if len(paper.abstract) <= 300 else paper.abstract[:300] + "..."
            emit(f"  Abstract: {abstract}")
        emit("")
        emit("Use \x1b[33madd <mode>\x1b[0m to add to graph (modes: graph, refs, cites, all; append 'k' for keywords)")
