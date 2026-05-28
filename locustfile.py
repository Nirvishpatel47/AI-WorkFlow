from locust import HttpUser, task, between
import uuid

class RAGAppUser(HttpUser):
    wait_time = between(2, 5)
    
    def on_start(self):
        """
        Runs automatically when a simulated user is 'born'.
        It generates a unique user, signs up, and saves the token.
        """
        self.auth_token = None
        
        # 1. Generate unique credentials so users don't collide
        unique_id = str(uuid.uuid4())[:8]
        self.user_name = f"BotUser_{unique_id}"
        self.user_email = f"bot_{unique_id}@example.com"
        self.user_password = "SecurePassword123"
        
        # 2. STEP 1: SIGN IN (Create the account)
        signin_data = {
            "name": self.user_name,
            "email": self.user_email,
            "password": self.user_password
        }
        
        print(f"Creating user: {self.user_email}")
        
        with self.client.post("/signin", data=signin_data, catch_response=True) as response:
            if response.status_code == 200:
                res_json = response.json()
                if res_json.get("success"):
                    # Your signin endpoint returns a token! We can grab it right here
                    self.auth_token = res_json.get("token")
                    response.success()
                else:
                    response.failure(f"Sign-in failed: {res_json.get('message')}")
                    return
            else:
                response.failure(f"Sign-in endpoint dead: {response.status_code}")
                return

        # 3. STEP 2: LOGIN (If sign-in didn't already lock down the token)
        if not self.auth_token:
            login_data = {
                "email": self.user_email,
                "password": self.user_password
            }
            with self.client.post("/login", data=login_data, catch_response=True) as response:
                if response.status_code == 200:
                    res_json = response.json()
                    if res_json.get("success"):
                        self.auth_token = res_json.get("token")
                        response.success()
                    else:
                        response.failure("Login failed after successful sign-in")
                else:
                    response.failure("Login endpoint dead")

    def get_auth_header(self):
        return {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}

    # --- The actual user actions that will loop now ---

    @task(3)
    def view_documents(self):
        if not self.auth_token: return
        self.client.post("/show_documents", headers=self.get_auth_header())

    @task(4)
    def ask_ai_chat(self):
        if not self.auth_token: return
        chat_data = {"query": "What is inside my document?"}
        self.client.post("/chat", data=chat_data, headers=self.get_auth_header())

    @task(1)
    def upload_small_document(self):
        if not self.auth_token: return
        file_payload = [
            ('files', ('test.txt', b'Hello world, this is a test RAG document payload.', 'text/plain'))
        ]
        self.client.post("/addDocument", files=file_payload, headers=self.get_auth_header())