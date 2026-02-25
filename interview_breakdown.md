## More to Give Interview

### Problem decomposition

Data engineering/Data preparation:
- Metadata from foundations and NGOs (scraped from the web and updated regularly)
- Contextual annotation
- Embedded and stored in a vector DB

Draft generation:
- Agentic RAG architecture: The agent receives a user query and interacts with the knowledge base to fetch relevant data iteratively

Validation/Fine Tuning:
- Iterations with the user with new calls to the LLM to improve the draft 


Python libraries for AI agent development (e.g. LangGraph, Strands, crew.ai)
Tools to evaluate AI agents (e.g. Arize Phoenix, LangFuse)
 

### Proposed Architecture

The output should be in a format that the users can interact with, ideally better than a chat interface (a word document, for example)

In Spinnable, they start with the best models so that they can isolate problems elsewhere, given their complicated architecture.  
My initial intuition was the opposite, starting with a smaller model to reduce cost, but given the relatively small scale the first tests could be with a powerful model for the same reasons as Spinnable.

### Hard problems

Is the data from foundations and NGOs mostly text or are there other forms like video also relevant?
Some embedding models are multimodal by nature


### Roadmap



#### RAG strategies
Improve the architecture with RAG strategies:
- Context Aware chunking: On the data preparation phase, split the documents intelligently instead of in fixe-sized chunks
- Late chunking: First create an embedding of the whole document to preserve context and only then group the tokens into chunks
- Reranking (pass the retrieved chunks through another LLM to get only the best ones)
- Query expansion: use an LLM (or hard coded context) to improve the query before hitting the knowledge base
- Fine-tune embedding model: Fine-tune a model (already pretrained) on custom data to do the embeddings (implies having large data volume and maintenance of this custom model)

### Validation Approach
Work together with pilot end users (NGO representatives who normally write these applications) to make sure the quality of proprosed drafts is satisfiable.
Quantify improvements in time spent drafting applications.


### Potential difficulties
Danish is a small subset of training data, models might have less performance than with English.
This product risks being a thin wrapper around an API call to a LLM.
Proprietary data and context (organisational data/context not available publicly) should be relevant for the outcome of the draft
Incorporating feedback loops so that the model learns from past interactions would provide an advantage. 
There is two big competition risks: a big provider releasing this feature natively (whoever is already using ChatGPT won't change to More To Give); a kid building a similar product in one week that is cheaper. Potential advantages are having specific context that makes it difficult for the big providers to have as good a feature and having lock-in with a good product that makes it unappealing to change to someone else that is cheaper (advantage of integrating the full lifecycle)


### Questions
How do you update the metadata you already have?  
Do you have some kind of automated regular polling?  
Or is it a manual job?

How regularly do users need to draft such applications? Daily/Weekly/Monthly? 