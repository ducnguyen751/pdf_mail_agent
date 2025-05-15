import os, json, shutil, tempfile, logging
from typing import Any, Tuple
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.chat_models import ChatOllama
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.schema.runnable import RunnablePassthrough

PERSIST_DIRECTORY = os.path.join('data','vectors')
logger = logging.getLogger(__name__)
SAMPLE_ROLES = [
    "HR", "Finance", "IT", "Legal", "Sales", "Marketing",
    "Customer Service", "Product", "Engineering", "Operations"
]
def create_vector_db(file_path: str) -> Chroma:
    temp = tempfile.mkdtemp()
    loader = UnstructuredPDFLoader(file_path)
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=7500, chunk_overlap=100)
    chunks = splitter.split_documents(docs)
    emb = OllamaEmbeddings(model='nomic-embed-text')
    col = Chroma.from_documents(
        documents=chunks,
        embedding=emb,
        persist_directory=PERSIST_DIRECTORY,
        collection_name=f"pdf_{hash(file_path)}"
    )
    shutil.rmtree(temp)
    return col

def process_pdf(pdf_path: str) -> Tuple[str, list]:
    vector_db = create_vector_db(pdf_path)

    llm = ChatOllama(model='gemma3:latest')

    retr = vector_db.as_retriever()
    retr.search_kwargs = {'k': 5}

    docs = retr.get_relevant_documents("")
    context = '\n\n'.join([doc.page_content for doc in docs])

    sum_prompt_str = "Summarize into 3-5 bullets, highlight instructions:\n{context}"
    sum_prompt = ChatPromptTemplate.from_template(sum_prompt_str)
    sum_chain = sum_prompt | llm
    summary = sum_chain.invoke({"context": context}).content

    role_prompt_str = """
    You are an assistant that identifies relevant roles or departments from a given list based on a document.

    Only return those roles from the list below that are clearly relevant to the document content.
    DO NOT return the full list unless all roles are clearly mentioned or implied.

    Respond with a JSON list (no explanations).

    List of available roles:
    {available_roles}

    Document:
    {context}
    """

    role_prompt = ChatPromptTemplate.from_template(role_prompt_str)
    role_chain = role_prompt | llm

    roles_response = role_chain.invoke({
        "context": context,
        "available_roles": ", ".join(SAMPLE_ROLES)
    })

    try:
        #roles = json.loads(roles_response.content)
        roles = roles_response.content
    except json.JSONDecodeError:
        roles = []

    return summary, roles
