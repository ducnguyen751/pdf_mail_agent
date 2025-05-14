from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.prompts import PromptTemplate, ChatPromptTemplate
import json

# 1) Load & split PDF

def load_and_split(pdf_path):
    loader = UnstructuredPDFLoader(pdf_path)
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
    return splitter.split_documents(docs)

# 2) Build vector store

def build_vector_store(docs):
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    from chromadb import Client as ChromaClient
    client = ChromaClient()
    collection = client.create_collection(name="pdf_collection")
    texts = [d.page_content for d in docs]
    vectors = embeddings.embed_documents(texts)
    collection.add(documents=texts, embeddings=vectors)
    return collection

# 3) RAG analyze: summarize + identify roles

def rag_analyze(pdf_path):
    docs = load_and_split(pdf_path)
    vs = build_vector_store(docs)
    retriever = vs.as_retriever()
    retriever.search_kwargs = {"k": 5}

    # Summarization chain
    llm = ChatOllama(model="llama2-70b")
    sum_prompt = PromptTemplate(
        input_variables=["context"],
        template="""
        Summarize into 3–5 bullet points, highlight any actionable instructions:
        {context}
        """
    )
    sum_chain = (
        retriever
        | ChatPromptTemplate.from_template(sum_prompt)
        | llm
    )
    # Call with empty query to get top chunks
    contexts = retriever.get_relevant_documents("")
    full_context = "\n\n".join([d.page_content for d in contexts])
    summary = sum_chain.invoke({"context": full_context})

    # Role identification chain
    role_prompt = PromptTemplate(
        input_variables=["context"],
        template="""
        Identify organizational roles/departments to receive this document. Return a JSON list:
        {context}
        """
    )
    role_chain = (
        retriever
        | ChatPromptTemplate.from_template(role_prompt)
        | llm
    )
    roles_json = role_chain.invoke({"context": full_context})
    roles = json.loads(roles_json)

    return summary, roles

# Wrapper

def process_pdf(pdf_path):
    return rag_analyze(pdf_path)