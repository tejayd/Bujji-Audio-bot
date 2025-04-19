import os
import bcrypt
import json
import time
from typing import Optional, Dict
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage
import chromadb

class UserManager:
    def __init__(self, data_dir: str = "user_data"):
        self.data_dir = data_dir
        self.users_dir = os.path.join(data_dir, "users")
        self.chroma_dir = os.path.join(data_dir, "chroma")
        self.ensure_directories()
        
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Initialize ChromaDB client
        self.chroma_client = chromadb.PersistentClient(path=self.chroma_dir)

    def ensure_directories(self):
        """Create necessary directories if they don't exist"""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.users_dir, exist_ok=True)
        os.makedirs(self.chroma_dir, exist_ok=True)

    def create_user(self, username: str, password: str) -> bool:
        """Create a new user with hashed password"""
        user_path = os.path.join(self.users_dir, f"{username}.json")
        if os.path.exists(user_path):
            return False

        # Hash the password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)

        # Initialize vector store for user
        vectorstore = Chroma(
            collection_name=f"{username}_context",
            embedding_function=self.embeddings,
            client=self.chroma_client
        )
        
        # Store user data
        user_data = {
            "username": username,
            "password_hash": hashed.decode('utf-8'),
            "context_summary": "New user profile"
        }

        with open(user_path, 'w') as f:
            json.dump(user_data, f)

        return True

    def authenticate(self, username: str, password: str) -> bool:
        """Authenticate a user"""
        user_path = os.path.join(self.users_dir, f"{username}.json")
        if not os.path.exists(user_path):
            return False

        with open(user_path, 'r') as f:
            user_data = json.load(f)

        return bcrypt.checkpw(
            password.encode('utf-8'),
            user_data['password_hash'].encode('utf-8')
        )

    def get_user_context(self, username: str) -> Optional[Dict]:
        """Get user's conversation history using LangChain's vector store"""
        try:
            # Load vector store
            vectorstore = Chroma(
                collection_name=f"{username}_context",
                embedding_function=self.embeddings,
                client=self.chroma_client
            )
            
            # Get chronological conversations using metadata filter
            collection = self.chroma_client.get_collection(name=f"{username}_context")
            
            # Get all documents and sort by timestamp
            results = collection.get(
                include=['metadatas', 'documents']
            )
            
            # Convert to Document objects and sort by timestamp
            docs = []
            if results and results['documents']:
                for doc, metadata in zip(results['documents'], results['metadatas']):
                    docs.append(Document(
                        page_content=doc,
                        metadata=metadata
                    ))
                # Sort by timestamp
                docs.sort(key=lambda x: x.metadata.get('timestamp', 0))
            
            # Format conversation history with proper message types
            history = []
            for doc in docs[-10:]:  # Get last 10 conversations
                if doc.metadata.get("type") == "human":
                    history.append(HumanMessage(content=doc.page_content))
                elif doc.metadata.get("type") == "ai":
                    history.append(AIMessage(content=doc.page_content))
            
            print(f"Loaded {len(history)} chronological conversations for user {username}")
            
            return {
                "history": [msg.content for msg in history],
                "messages": history,
                "session_start": time.time(),
                "vectorstore": vectorstore
            }
            
        except Exception as e:
            print(f"Creating new context for user {username}")
            vectorstore = Chroma(
                collection_name=f"{username}_context",
                embedding_function=self.embeddings,
                client=self.chroma_client
            )
            return {
                "history": [],
                "messages": [],
                "session_start": time.time(),
                "vectorstore": vectorstore
            }

    def update_user_context(self, username: str, interaction: str, is_human: bool = True):
        """Update user's conversation history using LangChain's vector store"""
        try:
            # Load or create vector store
            vectorstore = Chroma(
                collection_name=f"{username}_context",
                embedding_function=self.embeddings,
                client=self.chroma_client
            )
            
            # Add new interaction
            document = Document(
                page_content=interaction,
                metadata={
                    "timestamp": time.time(),
                    "type": "human" if is_human else "ai",
                    "username": username
                }
            )
            
            vectorstore.add_documents([document])
            # No need to call persist() as PersistentClient handles persistence automatically
            print(f"Successfully added interaction to {username}'s context")
            
        except Exception as e:
            print(f"Error adding interaction to context: {e}")