
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

4. starter_template MUST:
- contain realistic code
- contain TODO sections

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
            model="gpt-4.1-mini",
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

    prompt = f"""
You are an expert coding evaluator.

QUESTION:
{data.question}

REQUIREMENTS:
{json.dumps(data.requirements)}

LANGUAGE:
{data.language}

STUDENT CODE:
{data.student_code}

==================================================
RETURN FORMAT
==================================================

Return ONLY valid JSON.

{{
  "passed": true,
  "score": 8,
  "feedback":[
    "Good state handling",
    "Validation missing"
  ]
}}

==================================================
RULES
==================================================

1. Check:
- syntax
- logic
- implementation
- requirements

2. Give realistic feedback

3. Do not be overly strict

4. Return ONLY RAW JSON
"""

    try:

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            temperature=0,
            messages=[
                {
                    "role":"system",
                    "content":"You are a senior coding evaluator."
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
            "evaluation":parsed
        }

    except Exception as e:

        return {
            "success":False,
            "error":str(e)
        }