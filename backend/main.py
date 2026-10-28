from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "Welcome to CodeGenesis API"
    }


@app.get("/hello")
def hello():
    return {
        "message": "Hello from the CodeGenesis backend!"
    }


@app.post("/generate-lesson")
def generate_lesson():
    return {
        "steps": [
            {
                "title": "Create the Node",
                "explanation": "A binary tree is made of individual nodes.",
                "code": "class Node {"
            },
            {
                "title": "Add the data",
                "explanation": "Each node needs to store a value.",
                "code": "int data;"
            },
            {
                "title": "Add child pointers",
                "explanation": "The left and right pointers connect the node to its children.",
                "code": "Node* left;\nNode* right;"
            }
        ]
    }