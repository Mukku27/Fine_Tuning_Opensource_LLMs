from langchain_community.document_loaders.wikipedia import WikipediaLoader

# Initialize the loader with the query
loader = WikipediaLoader(query='Albert Einstein')

# Load the documents
docs = loader.load()

# Check if any documents were loaded
if docs:
    # Display the content of the first document
    print(docs[0].page_content)
else:
    print("No documents found.")


from langchain_text_splitters import CharacterTextSplitter

text=' '.join([pages.page_content.replace('\\t',' ') for pages in docs])
text_splitter=CharacterTextSplitter(
    separator='\\n',
    chunk_size=400,
    chunk_overlap=100,
    length_function=len,
    is_separator_regex=False

)
texts=text_splitter.create_documents([text])
splits=[item.page_content for item in texts]

print(splits[0])
