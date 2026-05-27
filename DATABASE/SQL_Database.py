#Run via python -m DATABASE.SQL_Database
from sqlalchemy import create_engine, text
from Security.Advance_Logger import logger
from Security.get_secretes import load_env_from_secret
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

class UserConnection:
    def __init__(self):
        self.engine = create_engine(load_env_from_secret("DATABASE_URL"))
        self.ph = PasswordHasher()
        self.create_table()
        self.create_document_table()
        self.create_chat_history_table()

    # Create users table
    def create_table(self):
        try:
            with self.engine.begin() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        name TEXT NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL
                    )
                """))

                conn.commit()
        except Exception as e:
            logger.error("UserConnection.create_table", e)

    def create_document_table(self):
        try:
            with self.engine.begin() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS documents (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        file_name TEXT NOT NULL,
                        extension TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id)
                            REFERENCES users(id)
                            ON DELETE CASCADE
                    )
                """))
                conn.commit()
            return True
        except Exception as e:
            logger.error(
                f"UserConnection.create_document_table", e
            )
            return False
    
    def create_chat_history_table(self) -> bool:
        """
        Creates the chat_history partition table with indexing constraints for multi-tenant isolation.
        """
        try:
            with self.engine.begin() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS chat_history (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        role TEXT NOT NULL,
                        message TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id)
                            REFERENCES users(id)
                            ON DELETE CASCADE
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_chat_history_user_date 
                    ON chat_history (user_id, created_at DESC);
                """))
                conn.commit()
            return True
        except Exception as e:
            logger.error("UserConnection.create_chat_history_table", e)
            return False

    # Create new user
    def create_user(self, name, email, password):
        try:
            hashed_password = self.ph.hash(password)
            with self.engine.begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO users (
                            name,
                            email,
                            password
                        )
                        VALUES (
                            :name,
                            :email,
                            :password
                        )
                    """),
                    {
                        "name": name,
                        "email": email,
                        "password": hashed_password
                    }
                )

                conn.commit()
                return True
        except Exception as e:
            logger.error("UserConnection.create_user", e)
            return False

    # Get user by email
    def get_user_by_email(self, email):
        try:
            with self.engine.begin() as conn:
                result = conn.execute(
                    text("""
                        SELECT *
                        FROM users
                        WHERE email = :email
                    """),
                    {
                        "email": email
                    }
                )

                return result.fetchone()
        except Exception as e:
            logger.error("UserConnection.get_user_by_email", e)

    # Verify login
    def login_user(self, email: str, password: str) -> dict:
        user = self.get_user_by_email(email)
        if not user:
            return False
        try:
            self.ph.verify(
                user.password,
                password
            )

            return {
                "id": user.id,
                "name": user.name,
                "email": user.email
            }
        except VerifyMismatchError:
            return False
        
    def get_Id_From_email(self, email: str) -> int:
        try:
            with self.engine.begin() as conn:
                result = conn.execute(
                    text("""
                        SELECT id
                        FROM users
                        WHERE email = :email
                    """),
                    {
                        "email": email
                    }
                )

                row = result.fetchone()

                if row:
                    return row.id
                
                return None
        except Exception as e:
            logger.error("UserConnection.get_Id_From_email", e)
            return ""
        
    def add_document( self, user_id: int, file_name: str, extension: str ):
        try:
            with self.engine.begin() as conn:
                result = conn.execute(
                    text("""
                        INSERT INTO documents (
                            user_id,
                            file_name,
                            extension
                        )
                        VALUES (
                            :user_id,
                            :file_name,
                            :extension
                        )
                        RETURNING id
                    """),
                    {
                        "user_id": user_id,
                        "file_name": file_name,
                        "extension": extension
                    }
                )
                document = result.fetchone()
                conn.commit()
                return document.id
            
        except Exception as e:
            logger.error(
                f"UserConnection.add_document", e
            )
            return None
        
    def delete_document(self, user_id: int, document_id: int) -> bool:
        try:
            with self.engine.begin() as conn:
                result=conn.execute(
                    text("""
                        DELETE FROM documents
                        WHERE id=:document_id
                        AND user_id=:user_id
                    """),
                    {
                        "document_id":document_id,
                        "user_id": user_id
                    }
                )
                conn.commit()
                return result.rowcount>0

        except Exception as e:
            logger.error(
                f"UserConnection.delete_document", e
            )
            return False
    
    def get_documents_data_by_userId(self, user_id: int) -> list[dict]:
        try:
            with self.engine.begin() as conn:
                result = conn.execute(
                    text("""
                        SELECT id, file_name, extension, created_at
                        FROM documents
                        WHERE user_id = :user_id
                    """),
                    {"user_id": user_id}
                )

                documents = [dict(row._mapping) for row in result]

                return documents

        except Exception as e:
            logger.error("UserConnection.get_documents_data_by_userID", e)
            return False
        
    def save_chat_turn(self, user_id: int, role: str, message: str) -> bool:
        """
        Inserts a single chat turn metadata payload under explicit user boundary ownership.
        """
        try:
            with self.engine.begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO chat_history (user_id, role, message)
                        VALUES (:user_id, :role, :message)
                    """),
                    {
                        "user_id": user_id,
                        "role": role,
                        "message": message
                    }
                )
                conn.commit()
            return True
        except Exception as e:
            logger.error("UserConnection.save_chat_turn", e)
            return False

    def get_recent_chat_history(self, user_id: int, limit: int = 6) -> list[dict]:
        """
        Retrieves the latest exchanges for a user sorted chronologically (oldest to newest).
        """
        try:
            with self.engine.begin() as conn:
                result = conn.execute(
                    text("""
                        SELECT role, message AS text
                        FROM chat_history
                        WHERE user_id = :user_id
                        ORDER BY created_at DESC
                        LIMIT :limit
                    """),
                    {
                        "user_id": user_id,
                        "limit": limit
                    }
                )
                
                # Convert SQLAlchemy row objects to dictionary mappings
                history = [dict(row._mapping) for row in result]
                
                # Reverse the list in memory to restore proper chronological timeline order: [User, Model, User...]
                history.reverse()
                return history
            
        except Exception as e:
            logger.error("UserConnection.get_recent_chat_history", e)
            return []
        
connect = UserConnection()

if __name__ == "__main__":
    UserConnection().create_document_table()