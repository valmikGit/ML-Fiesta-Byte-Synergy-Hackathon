from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from urllib.parse import quote_plus
from pymongo import MongoClient
from langchain_community.embeddings.huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import MongoDBAtlasVectorSearch
from langchain_community.document_loaders import DirectoryLoader
from transformers import pipeline
import os

# MongoDB setup
username = quote_plus("valmik0000000")
password = quote_plus("valmik@mongo7")  # Replace with your actual password

uri = f"mongodb+srv://{username}:{password}@valmikcluster0.hdqee.mongodb.net/?retryWrites=true&w=majority&appName=ValmikCluster0"
client = MongoClient(uri, server_api=ServerApi('1'), tls=True)

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

# Database and collection
dbName = "ML_Fiesta"
collectionName = "translations"
collection = client[dbName][collectionName]

# Hugging Face token (optional if required for private models)
# hf_token = "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"

# Define the embedding model
embedding_model_name = "sentence-transformers/all-MiniLM-L6-v2"
embeddings = HuggingFaceEmbeddings(model_name=embedding_model_name)

# Check if the data already exists in the vector store
if collection.estimated_document_count() == 0:
    print("No data found in the vector store. Loading documents and creating the vector store.")
    # Document loader
    loader = DirectoryLoader(
        r"/content/drive/MyDrive/ML_Fiesta_Mongo_DB_Vectorization/refined_data",
        glob="./*.txt",
        show_progress=True
    )
    data = loader.load()

    # Load documents into the vector store
    vectorStore = MongoDBAtlasVectorSearch.from_documents(data, collection=collection, embedding=embeddings)
else:
    print("Data already exists in the vector store. Connecting to existing vector store.")
    vectorStore = MongoDBAtlasVectorSearch(collection=collection, embedding=embeddings)

# Define the language model using transformers pipeline
# llm_pipeline = pipeline("text-generation", model="tiiuae/falcon-7b-instruct", tokenizer="tiiuae/falcon-7b-instruct", device=0)
# llm_pipeline = pipeline("text-generation", model="tiiuae/falcon-3b", tokenizer="tiiuae/falcon-3b", device=0)
# llm_pipeline = pipeline("text-generation", model="google/flan-t5-small", tokenizer="google/flan-t5-small", device=0)

# Define the question-answering pipeline
qa_pipeline = pipeline("question-answering", model="distilbert-base-uncased-distilled-squad", tokenizer="distilbert-base-uncased-distilled-squad", device=0)

def query_data(query) -> str:
    """
    Querying data loaded in Mongo DB.
    """
    # Use the vector store's retriever to find relevant documents
    retriever = vectorStore.as_retriever(search_kwargs={"K": 20})
    retrieved_docs = retriever.get_relevant_documents(query)

    # Combine retrieved documents as context for the model
    context = " ".join([doc.page_content for doc in retrieved_docs])
    # Update prompt to explicitly ask for the answer
    # prompt = f"Based on the following context, answer the question.\n\nContext: {context}\n\nQuestion: {query}"

    # response = llm_pipeline(prompt, max_length=200, do_sample=True)
    # print(response)
    # print(response[0])
    # return response[0]['generated_text']

    # Ask the question with the context
    prompt = f"Context: {context}\n\nQuestion: {query}"

    # Use the question-answering pipeline to get the answer
    response = qa_pipeline(question=query, context=context)
    
    print(response)
    return response['answer']
    

# Query example
queries = [
    "Where have the blood moon thieves been active?", 
    "What is the name of the group involved in illicit activities?", 
    "Which government body has been formed to combat the blood moon thieves?", 
    "Where is the stronghold of the blood moon thieves?",
    "Who does Baba obtain contact information for?",
    "Where does Baba try to meet Somwara Siguna?"
]
try:
    print(query_data(query=queries[5]))
except Exception as e:
    print(e)