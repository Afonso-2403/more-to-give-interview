## More to Give Interview

### Problem decomposition

**Data preparation and Knowledge Base:**
- Structured Metadata from foundations (scraped from the web and updated regularly). 
- Structured Metadata from NGOs (past applications, org history, project descriptions).
- Unstructured Data (Past successful applications, annual reports, strategic focus of foundation, etc). 

**Context retrieval:**
- Given an (NGO, foundation, project) tuple, retrieve the most relevant context: foundation requirements, similar past applications, org facts, successful examples. 

**Draft generation:**
- Agentic RAG architecture: The agent receives a user query and interacts with the knowledge base to fetch relevant data iteratively. 

**Validation/Fine Tuning:**
- Make sure all of the requirements are met, iterate again if not. 
- Iterations with the user with new calls to the LLM to improve the draft. 

**User Interface:**
- The front-end where the user selects org + foundation + project, reviews the draft and edits. 
- Ideally edits are incorporated to improve the model (if fine-tuning our own model). 
 

### Proposed Architecture

Ref. Excalidraw for visual representation of the architecture. 

The output should be in a format that the users can interact with, ideally better than a chat interface (a word document, for example)

In Spinnable, they start with the best models so that they can isolate problems elsewhere, given their complicated architecture.  
My initial intuition was the opposite, starting with a smaller model to reduce cost, but given the relatively small scale the first tests could be with a powerful model for the same reasons as Spinnable.

### Hard problems

**Hallucination:**
- Flag claims that are not backed by context (with the validator model, or other LLM)
- Inject critical numbers into the text without generating them
- Have a confidence score per section to flag the more important ones for review

**Generic writing sounding artificial:**
- Using past applications as context might help with style
- Structuring that context and adding a style guide as org metadata
- Human reviewers need to adapt the draft

**Organizations with very little data:**
- Have a more detailed onboarding asking them to produce a style guide, or have a per-sector fallback
- Use successful applications from other NGOs as context (if possible due to privacy concerns)

**Danish is a small subset of training data**
Models might have less performance than with English.

**This product risks being a thin wrapper around an API call to a LLM.**
Proprietary data and context (organisational data/context not available publicly) should be relevant for the outcome of the draft
Incorporating feedback loops so that the model learns from past interactions would provide an advantage. 

**There are two big competition risks:** 
A big provider releasing this feature natively (whoever is already using ChatGPT won't change to More To Give); a kid building a similar product in one week that is cheaper. Potential advantages are having specific context that makes it difficult for the big providers to have as good a feature and having lock-in with a good product that makes it unappealing to change to someone else that is cheaper (advantage of integrating the full lifecycle)


### Roadmap

**MVP**
- Hand curated golden dataset of foundations with concrete requirements
- Prompts are hand drafted per foundation
- No unstructured data storage, just the existing SQL DB
- Structured inputs from the NGOs
- One-shot generation of the document
- Validator model being a simple automation checking all sections are present, output is within limits
- Simple Web UI where users edit to add style



### Validation Approach
- Validator model for compliance on quantifiable metrics (all sections present, budget adds up, timeline is correct, etc)
- Work together with pilot end users (NGO representatives who normally write these applications) to score quality of drafts.
- Use an LLM as a judge to score applications on specific dimensions.
- Ask the system to generate an application for a past successful example and have human reviewers do a blind test
- Quantify improvements in time spent drafting applications.



### RAG strategies

Improve the architecture with RAG strategies:
- **Context Aware chunking:** On the data preparation phase, split the documents intelligently instead of in fixe-sized chunks
- **Late chunking:** First create an embedding of the whole document to preserve context and only then group the tokens into chunks
- **Reranking:** (pass the retrieved chunks through another LLM to get only the best ones)
- **Query expansion:** use an LLM (or hard coded context) to improve the query before hitting the knowledge base
- **Fine-tune embedding model:** Fine-tune a model (already pretrained) on custom data to do the embeddings (implies having large data volume and maintenance of this custom model)

### Questions
How do you update the metadata you already have?  
Do you have some kind of automated regular polling?  
Or is it a manual job?

How regularly do users need to draft such applications? Daily/Weekly/Monthly? 