#Run via python -m DATABASE.SQL_Database
from sqlalchemy import create_engine, text
from Security.Advance_Logger import AdvancedLogger
from Security.get_secretes import load_env_from_secret
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

logger = AdvancedLogger()

class UserConnection:
    def __init__(self):
        self.engine = create_engine(load_env_from_secret("DATABASE_URL"))
        self.ph = PasswordHasher()
        self.create_table()

    # Create users table
    def create_table(self):
        try:
            with self.engine.connect() as conn:
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
            with self.engine.connect() as conn:
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

    # Create new user
    def create_user(self, name, email, password):
        try:
            hashed_password = self.ph.hash(password)
            with self.engine.connect() as conn:
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
            with self.engine.connect() as conn:
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
            with self.engine.connect() as conn:
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
            with self.engine.connect() as conn:
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
        
    def delete_document(self, document_id: int) -> bool:
        try:
            with self.engine.connect() as conn:
                result=conn.execute(
                    text("""
                        DELETE FROM documents
                        WHERE id=:document_id
                    """),
                    {
                        "document_id":document_id
                    }
                )
                conn.commit()
                return result.rowcount>0

        except Exception as e:
            logger.error(
                f"UserConnection.delete_document", e
            )
            return False
        
if __name__ == "__main__":
    UserConnection().create_document_table()