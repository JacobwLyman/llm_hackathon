from langchain_community.document_loaders import DirectoryLoader, UnstructuredMarkdownLoader
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import MarkdownHeaderTextSplitter
from langchain_openai import OpenAIEmbeddings

# Read all md files
markdown_path = "./docs"
loader = DirectoryLoader(markdown_path, glob='**/*.md', loader_cls=UnstructuredMarkdownLoader, recursive=True)
markdown_documents = loader.load()

# Split documents by headers
doc_splits = []
markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=[
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
])

for doc in markdown_documents:
    doc_splits.extend(doc.page_content for doc in markdown_splitter.split_text(doc.page_content))

# Write docs in DB
vectorstore = Chroma(persist_directory="rag_db", embedding_function=OpenAIEmbeddings())
vectorstore.add_texts(doc_splits)
