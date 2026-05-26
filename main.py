
# ================================================
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from openai import OpenAI
from dotenv import load_dotenv

import os
import json
import re

# =========================================================
# LOAD ENV
# =========================================================

load_dotenv()

# =========================================================
# FASTAPI
# =========================================================

app = FastAPI()

# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# OPENAI
# =========================================================

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

# =========================================================
# REQUEST MODELS
# =========================================================

class TopicRequest(BaseModel):
    topic: str

class BoilerplateRequest(BaseModel):
    file_name: str
    language: str
    question: str
    requirements: list[str]

class EvaluationRequest(BaseModel):
    question: str
    requirements: list[str]
    student_code: str
    language: str


# =========================================================
# CLEAN JSON
# =========================================================

def clean_json(text):

    text = re.sub(r"```json", "", text)
    text = re.sub(r"```", "", text)

    return text.strip()


# =========================================================
# ROOT
# =========================================================

@app.get("/")
async def root():

    return {
        "status": "running",
        "message": "AI Lab Platform Running"
    }


# =========================================================
# GENERATE BOILERPLATE
# =========================================================

@app.post("/generate-boilerplate")
async def generate_boilerplate(data: BoilerplateRequest):

    prompt = f"""
You are an expert software architect.

Generate ONLY starter boilerplate code.

========================================
QUESTION
========================================

{data.question}

========================================
REQUIREMENTS
========================================

{json.dumps(data.requirements)}

========================================
FILE NAME
========================================

{data.file_name}

========================================
LANGUAGE
========================================

{data.language}

========================================
RULES
========================================

1. Generate ONLY starter structure
2. Add TODO comments
3. DO NOT implement final logic
4. DO NOT solve the exercise
5. Must match framework/language
6. Must look enterprise-grade
7. Return ONLY raw code
"""

    try:

        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            temperature=0.3,
            messages=[
                {
                    "role":"system",
                    "content":"You are a senior software architect."
                },
                {
                    "role":"user",
                    "content":prompt
                }
            ]
        )

        code = response.choices[0].message.content

        return {
            "success": True,
            "code": code
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }

# =========================================================
# GENERATE LABS
# =========================================================

@app.post("/generate-labs")
async def generate_labs(data: TopicRequest):

    prompt = f"""
You are an elite enterprise coding trainer.

Generate enterprise coding labs.

TOPIC:
{data.topic}

==================================================
RETURN FORMAT
==================================================

Return ONLY valid JSON.

{{
  "modules":[
    {{
      "module_name":"",
      "exercises":[
        {{
          "title":"",
          "difficulty":"",
          "problem":"",
          "requirements":[],
          "steps":[],
          "hint":"",
          "language":"",
          "starter_template":""
        }}
      ]
    }}
  ]
}}

==================================================
RULES
==================================================

1. Generate:
- Beginner
- Intermediate
- Advanced

2. Every module:
- 2 exercises

3. Generate REAL coding tasks

4. starter_template RULE (VERY STRICT):

- MUST be ONLY a starter scaffold
- MUST contain structure only (boilerplate)
- MUST include TODO comments for ALL logic
- MUST NOT include full solution logic
- MUST NOT contain final working implementation
- MUST NOT solve the exercise

Allowed:
- empty functions
- class structure
- component skeleton
- API route skeleton
- placeholders

NOT allowed:
- business logic
- final working code
- full UI implementation

- NOT be blank
- match language/framework automatically

5. Support ANY language/framework dynamically

6. Use enterprise-style architecture

7. Return ONLY RAW JSON

==================================================
GOOD TEMPLATE EXAMPLE
==================================================

import React, {{ useState }} from "react";

const LoginForm = () => {{

  // TODO: Create state

  const handleSubmit = (e) => {{
    e.preventDefault();

    // TODO: Add submit logic
  }}

  return (
    <form onSubmit={{handleSubmit}}>

      <input
        type="email"

        // TODO: Bind value

        // TODO: Add onChange
      />

    </form>
  )
}}

export default LoginForm;
"""

    try:

        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            temperature=0.7,
            messages=[
                {
                    "role":"system",
                    "content":"You are a senior coding trainer."
                },
                {
                    "role":"user",
                    "content":prompt
                }
            ]
        )

        result = response.choices[0].message.content

        cleaned = clean_json(result)

        parsed = json.loads(cleaned)

        return {
            "success":True,
            "labs":parsed
        }

    except Exception as e:

        return {
            "success":False,
            "error":str(e)
        }


# =========================================================
# EVALUATE
# =========================================================
@app.post("/evaluate")
async def evaluate(data: EvaluationRequest):

    if not data.student_code or data.student_code.strip() == "":
        return {
            "success": True,
            "evaluation": {
                "passed": False,
                "score": 0,
                "feedback": ["No code submitted"]
            }
        }

    prompt = f"""
Evaluate ONLY based on requirement completion.

==================================================
QUESTION
==================================================

{data.question}

==================================================
REQUIREMENTS
==================================================

{json.dumps(data.requirements)}

==================================================
LANGUAGE
==================================================

{data.language}

==================================================
STUDENT CODE
==================================================

{data.student_code}

==================================================
EVALUATION RULES
==================================================
Rules:
- Each completed requirement gets equal weight.
- If all requirements are completed correctly, score MUST be 10.
- Do NOT deduct marks for comments, formatting, best practices, or optional improvements.
- Suggestions should not reduce score.
==================================================
RETURN ONLY JSON
==================================================

{{
  "passed": true,
  "score": 10,
  "summary": "Short overall evaluation",
  "feedback": [
    "Issue 1",
    "Issue 2",
    "Good point"
  ]
}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": "You are a senior code reviewer providing evaluation feedback."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        result = response.choices[0].message.content
        cleaned = clean_json(result)
        parsed = json.loads(cleaned)

        return {
            "success": True,
            "evaluation": parsed
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }