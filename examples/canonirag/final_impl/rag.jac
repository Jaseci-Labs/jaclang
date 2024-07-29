import: py from langchain_community.document_loaders, PyPDFDirectoryLoader;
import: py from langchain_text_splitters, RecursiveCharacterTextSplitter;
import: py from langchain.schema.document, Document;
import: py from langchain_community.embeddings.ollama, OllamaEmbeddings;
import: py from langchain_community.vectorstores.chroma, Chroma;
import: py os;

obj rag_engine {
    has file_path:str="books";
    has chroma_path:str = "chroma";

    can postinit {
        documents:list = self.load_documents();
        chunks:list = self.split_documents(documents);
        self.add_to_chroma(chunks);
    }

    can load_documents{
        document_loader = PyPDFDirectoryLoader(self.file_path);
        return document_loader.load();
    }

    can split_documents(documents: list[Document]){
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=800,
        chunk_overlap=80,
        length_function=len,
        is_separator_regex=False);
        return text_splitter.split_documents(documents);
    }

    can get_embedding_function{
        embeddings = OllamaEmbeddings(model='nomic-embed-text');
        return embeddings;
    }

    '''
    This ability will create unique IDs for chunks. 
    Example: "books/Oxford Handbook.pdf:100:2:
    Template: "Page Source:Page Number:Chunk Index"
    '''
    can add_chunk_id(chunks:str){
        last_page_id = None;
        current_chunk_index = 0;
        
        for chunk in chunks{
            source = chunk.metadata.get('source');
            page = chunk.metadata.get('page');
            current_page_id = f'{source}:{page}';

            if current_page_id == last_page_id{
                current_chunk_index +=1;
            }

            else{
                current_chunk_index = 0;
            }

            chunk_id = f'{current_page_id}:{current_chunk_index}';
            last_page_id = current_page_id;

            chunk.metadata['id'] = chunk_id;
        }

        return chunks;
    }

    '''
    Creating/ Updating the Vector Database
    '''
    can add_to_chroma(chunks: list[Document]){
        #Loading the existing database
        db = Chroma(persist_directory=self.chroma_path, embedding_function=self.get_embedding_function()); 
        chunks_with_ids = self.add_chunk_id(chunks);    #Chunk ID Calculation

        #Adding and Updating the documents
        existing_items = db.get(include=[]);
        existing_ids = set(existing_items['ids']);

        #Only adding new documents that does not exist in the database
        new_chunks = [];
        for chunk in chunks_with_ids{
            if chunk.metadata['id'] not in existing_ids{
                new_chunks.append(chunk);
            }
            
        }

        if len(new_chunks){
            print('adding new documents');
            new_chunk_ids = [chunk.metadata['id'] for chunk in new_chunks];
            db.add_documents(new_chunks, ids=new_chunk_ids);
        }

        else{
            print('no new documents to add');
        }
        
    }

    '''
    Retreive the relevent chunks upon a query.
    '''
    can get_from_chroma(query:str,chunck_nos:int=5){
        db = Chroma(persist_directory=self.chroma_path, embedding_function=self.get_embedding_function());
        results = db.similarity_search_with_score(query,k=chunck_nos);
        return results;
    }

}


