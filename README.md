# Researchers-Toolkit

A powerful command-line tool for organizing and exploring academic research using connected knowledge graphs. Built with Python, Neo4j, and the Semantic Scholar API, this toolkit helps researchers discover, analyze, and visualize relationships between papers, authors, and research concepts.

## Features

### 🔍 **Paper Discovery & Search**
- **Keyword Search**: Find papers by research topics and keywords
- **Author Search**: Discover papers by specific researchers
- **Paper ID Lookup**: Direct access to papers via Semantic Scholar IDs
- **Field-specific Search**: Filter results by academic disciplines

### 📊 **Knowledge Graph Construction**
- **Automatic Graph Building**: Create connected graphs of papers, authors, and venues
- **Citation Networks**: Map citation and reference relationships between papers
- **Author Networks**: Track collaborations and research connections
- **Venue Analysis**: Organize papers by publication venues

### 🏷️ **Research Organization**
- **Project Tagging**: Organize research into custom project categories
- **Keyword Extraction**: Automatically extract and link research keywords
- **Abstract Analysis**: Process paper abstracts for semantic connections
- **Batch Operations**: Refresh and update entire research collections

### 🔗 **Relationship Mapping**
- **Citation Analysis**: Track how papers reference each other
- **Author Collaborations**: Visualize research partnerships
- **Topic Clustering**: Group related research by keywords and concepts
- **Venue Networks**: Understand publication patterns across journals/conferences

## Installation

### Prerequisites

1. **Python 3.8+**
2. **Neo4j Database** (Community or Enterprise Edition)
3. **Semantic Scholar API Key** (optional, but recommended for higher rate limits)

### Step 1: Install Neo4j

#### Option A: Neo4j Desktop (Recommended for beginners)
1. Download [Neo4j Desktop](https://neo4j.com/download/)
2. Install and create a new database
3. Set username: `neo4j` and password: `neo4j` (or your preferred credentials)
4. Start the database (default URL: `bolt://localhost:7687`)

#### Option B: Neo4j Community Server
```bash
# Ubuntu/Debian
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable 4.4' | sudo tee /etc/apt/sources.list.d/neo4j.list
sudo apt update
sudo apt install neo4j

# macOS with Homebrew
brew install neo4j

# Start Neo4j service
sudo systemctl start neo4j
# or
neo4j start
```

#### Option C: Docker
```bash
docker run \
    --name neo4j-research \
    -p 7474:7474 -p 7687:7687 \
    -d \
    -v $HOME/neo4j/data:/data \
    -v $HOME/neo4j/logs:/logs \
    -v $HOME/neo4j/import:/var/lib/neo4j/import \
    -v $HOME/neo4j/plugins:/plugins \
    --env NEO4J_AUTH=neo4j/neo4j \
    neo4j:latest
```

### Step 2: Install Python Dependencies

1. **Clone the repository**:
```bash
git clone https://github.com/schladt/Researchers-Toolkit.git
cd Researchers-Toolkit
```

2. **Create a virtual environment** (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

Create a `.env` file in the project root or set environment variables:

```bash
# Required: Neo4j Database Connection
export NEO4J_URL=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=neo4j

# Optional: Semantic Scholar API Key (for higher rate limits)
export S2_API_KEY=your_semantic_scholar_api_key_here
```

#### Getting a Semantic Scholar API Key (Optional)
1. Visit [Semantic Scholar API](https://www.semanticscholar.org/product/api)
2. Sign up for a free account
3. Generate an API key
4. Add it to your environment variables

**Note**: The tool works without an API key but with lower rate limits.

## Usage

### Starting the Application

```bash
python rtk.py
```

### Basic Workflow

1. **Start with a Search**:
   - Choose option 1 for keyword search
   - Choose option 2 for author search
   - Choose option 3 for direct paper lookup

2. **Add Papers to Graph**:
   - Use 'g' to add individual papers
   - Use 'a' to add papers with all citations and references (slower but comprehensive)
   - Use 'gk' or 'ak' to include keyword extraction

3. **Set Project Tags**:
   - Use option 5 to set project tags for organizing your research

4. **Build Citation Networks**:
   - Use option 4 to refresh references for all papers in your database

### Example Session

```
>>> 1  # Search by keyword
>>> machine learning transformers  # Enter search term
>>> 0  # Select first paper
>>> gk  # Add paper with keywords to graph

>>> 5  # Set project tags
>>> deep learning, nlp, transformers  # Set tags

>>> 4  # Refresh all references (builds citation network)
```

## Graph Schema

The tool creates a rich knowledge graph with the following node types and relationships:

### Node Types
- **Paper**: Research papers with metadata (title, abstract, year, citation count, etc.)
- **Author**: Researchers and their information
- **Venue**: Journals, conferences, and publication venues
- **Keyword**: Extracted terms from abstracts and titles
- **Tag**: Custom project organization tags

### Relationships
- **REFERENCES**: Paper A references Paper B
- **AUTHORED_BY**: Paper written by Author
- **PUBLISHED_IN**: Paper published in Venue
- **HAS_KEYWORD**: Paper contains Keyword
- **TAGGED**: Entity belongs to project Tag

## Advanced Features

### Batch Processing
- Refresh all paper references automatically
- Extract keywords from existing papers
- Update citation counts and metadata

### Text Processing
- Automatic tokenization and lemmatization
- Stop word removal
- Keyword extraction from abstracts and titles

### Rate Limiting
- Built-in rate limiting for API calls
- Exponential backoff for error handling
- Concurrent processing for efficiency

## Data Sources

- **Primary**: [Semantic Scholar API](https://www.semanticscholar.org/product/api) - Comprehensive academic paper database
- **Coverage**: 200+ million papers across computer science, biomedical sciences, and more
- **Data**: Abstracts, citations, author information, venue details, and paper metrics

## Dependencies

### Core Dependencies
- **neo4j**: Graph database driver
- **requests**: HTTP library for API calls
- **nltk**: Natural language processing
- **prompt-toolkit**: Interactive command-line interface
- **python-dotenv**: Environment variable management

### Processing & Utilities
- **tqdm**: Progress bars
- **ratelimit**: API rate limiting
- **backoff**: Retry logic with exponential backoff

See `requirements.txt` for complete dependency list with versions.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Troubleshooting

### Common Issues

1. **Neo4j Connection Error**:
   - Ensure Neo4j is running
   - Check connection URL and credentials
   - Verify firewall settings for port 7687

2. **API Rate Limiting**:
   - Get a Semantic Scholar API key for higher limits
   - The tool includes automatic retry logic

3. **Memory Issues with Large Graphs**:
   - Use project tags to organize research
   - Consider processing papers in smaller batches

### Support

For issues and questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Refer to Neo4j and Semantic Scholar documentation

## Roadmap

- [ ] Advanced graph analytics and visualization
- [ ] Export functionality (GraphML, CSV, etc.)
- [ ] Local database search and filtering
- [ ] Paper recommendation system
- [ ] Integration with reference managers
- [ ] Web interface for graph exploration

---

**Author**: Mike Schladt (2025)  
**Repository**: [https://github.com/schladt/Researchers-Toolkit](https://github.com/schladt/Researchers-Toolkit)
