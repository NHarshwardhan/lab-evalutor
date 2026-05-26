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
    context: str = ""  # Optional context about the exercise

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
# GENERATE BOILERPLATE FOR SINGLE FILE
# =========================================================

@app.post("/generate-boilerplate")
async def generate_boilerplate(data: BoilerplateRequest):
    """
    Generate boilerplate code for a SINGLE FILE ONLY.
    Does not generate code for other files.
    IMPORTANT: No implementation hints, examples, or commented code showing how to solve it.
    Only skeleton structure with TODO comments.
    """

    prompt = f"""
You are an expert software architect.

Generate ONLY starter boilerplate code for THIS FILE ONLY.

CRITICAL RULES:
✓ MUST DO:
- Generate only the basic skeleton structure
- Include necessary imports
- Include empty methods/functions/components
- Add TODO comments explaining what to implement
- Keep code minimal and clean

✗ MUST NOT DO:
- Show ANY implementation code
- Show ANY commented-out example code
- Show how to call other components/functions
- Hint at the solution
- Include variables with actual values
- Include JSX/HTML with element content
- Show "like this" patterns
- Provide any code that shows the answer

========================================
QUESTION
========================================

{data.question}

========================================
REQUIREMENTS
========================================

{json.dumps(data.requirements)}

========================================
FILE INFORMATION
========================================

File Name: {data.file_name}
Language: {data.language}

========================================
BOILERPLATE GENERATION RULES
========================================

1. Generate ONLY the bare minimum skeleton for {data.file_name}
2. Include necessary imports/packages
3. Include class/function/component declaration
4. Include empty methods/functions that need to be filled
5. Mark incomplete parts with: // TODO: [description of what to do]
6. Keep structure clean with no implementation code
7. Must be valid {data.language} code that would compile/run
8. Return ONLY raw code (no markdown, no backticks, no explanations)

========================================
LANGUAGE-SPECIFIC SKELETON EXAMPLES
========================================

REACT/JAVASCRIPT:
import React from 'react';

const ParentComponent = () => {{
  // TODO: Create state
  
  // TODO: Create event handler

  return (
    <div>
      {{/* TODO: Add child component and content */}}
    </div>
  );
}};

export default ParentComponent;

PYTHON:
class Parent:
    def __init__(self):
        # TODO: Initialize attributes
        pass
    
    def process_data(self, data):
        # TODO: Implement data processing
        pass

JAVA:
public class Parent {{
    // TODO: Declare variables
    
    public Parent() {{
        // TODO: Constructor implementation
    }}
    
    public void handleData(String data) {{
        // TODO: Implement handler
    }}
}}

C#:
public class Parent {{
    // TODO: Declare fields
    
    public Parent() {{
        // TODO: Initialize
    }}
    
    public void Process() {{
        // TODO: Implement logic
    }}
}}

TYPESCRIPT:
interface IParent {{
    // TODO: Define interface methods
}}

class Parent implements IParent {{
    // TODO: Implement interface members
}}

========================================
WHAT NOT TO SHOW
========================================

✗ WRONG: Commented code showing how to do it
// TODO: Create state like this:
// const [message, setMessage] = useState('Hello');

✗ WRONG: Example of what to render
{{/* TODO: Render child like this */}}
{{/* <Child message={{message}} onData={{handleData}} /> */}}

✗ WRONG: Implementation hints
// TODO: Use useState to create state for message

✗ WRONG: Variable initialization
const message = "Hello"; // This is implementation
const [count, setCount] = useState(0); // This is implementation

========================================
CONTEXT (Optional)
========================================

{data.context if data.context else "None"}

========================================
GENERATE ONLY THE CODE
========================================

Return ONLY the boilerplate code.
No explanations.
No markdown.
No backticks.
No comments showing implementation.
Just clean skeleton structure with TODO marks.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": "You are a senior software architect. Generate ONLY bare skeleton boilerplate code. NO examples. NO implementation hints. NO commented code showing solutions. Just empty structure with TODO comments."
                },
                {
                    "role": "user",
                    "content": prompt
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

{{{{
  "modules":[
    {{{{
      "module_name":"",
      "exercises":[
        {{{{
          "title":"",
          "difficulty":"Beginner|Intermediate|Advanced",
          "problem":"",
          "requirements":[],
          "steps":[],
          "hint":"",
          "language":"",
          "starter_template":""
        }}}}
      ]
    }}}}
  ]
}}}}

==================================================
RULES FOR ALL LANGUAGES
==================================================

1. Generate:
   - Beginner level exercises
   - Intermediate level exercises
   - Advanced level exercises

2. Every module: 2-3 exercises

3. Generate REAL coding tasks

4. CRITICAL - starter_template RULES (FOR ALL LANGUAGES):

   IMPORTANT: NO IMPLEMENTATION EXAMPLES OR HINTS
   
   ✓ DO INCLUDE:
   - Necessary imports
   - Class/function skeleton
   - Empty methods/functions
   - Basic structure
   - TODO comments for what to implement
   
   ✗ DO NOT INCLUDE:
   - Implementation examples
   - Commented-out code showing how to solve it
   - Hints about the solution
   - "// TODO: Do X like this:" patterns
   - Example function calls or usage
   - Working implementations
   - Any code that shows the answer
   
   TEMPLATE STRUCTURE ONLY - NOTHING MORE
   NO IMPLEMENTATION CODE, NO EXAMPLES, NO HINTS

5. CRITICAL - steps FIELD (MANDATORY FOR EVERY EXERCISE):

   EVERY exercise MUST have a "steps" array with 3-5 actionable steps.
   
   Steps should be:
   - Clear guidance on WHAT to do
   - Progressive order (step 1 → step 2 → step 3)
   - NO code examples or solution hints
   - Actionable but not solution-revealing
   
   Good steps (DO THIS):
   ✓ "Create a new file/component with the required name"
   ✓ "Add necessary imports/dependencies"
   ✓ "Set up the basic structure/skeleton"
   ✓ "Implement each required method/function"
   ✓ "Test your code against all requirements"
   
   Bad steps (DO NOT DO THIS):
   ✗ "Use useState like this: const [x, setX] = useState(0)"
   ✗ "Render JSX like: <div>{data}</div>"
   ✗ "Create a for loop to iterate"
   ✗ Anything that shows HOW to code the solution

6. If exercise needs multiple files:
   - Include file marker in template
   - Each file marked separately with // FILE: filename (or # FILE: for Python, etc)
   - Each file should be ONLY skeleton code
   - NO examples, NO hints, NO implementation
   
   React/JavaScript example:
     // FILE: Parent.jsx
     import React from 'react';
     
     const Parent = () => {{
       "// TODO: Create state"
       
       "// TODO: Create handler"
       
      {{}} return (
         <div>
           {{{{/* TODO: Add content */}}}}
         </div>
       );
     }};
     
     export default Parent;

     // FILE: Child.jsx
     const Child = () => {{
       // TODO: Implement
       
       return <></>;
     }};
     
     export default Child;

   Python example:
     # FILE: parent.py
     class Parent:
         def __init__(self):
             # TODO: Initialize
             pass
         
         def process(self):
             # TODO: Implement
             pass

     # FILE: child.py
     class Child:
         def __init__(self):
             # TODO: Initialize
             pass
   
   Java example:
     // FILE: Parent.java
     public class Parent {{
         // TODO: Declare variables
         
         public Parent() {{
             // TODO: Constructor
         }}
         
         public void handle() {{
             // TODO: Implement
         }}
     }}

     // FILE: Child.java
     public class Child {{
         // TODO: Implement class
     }}

6. Support ANY language/framework dynamically

7. Use enterprise-style architecture

8. Return ONLY RAW JSON (no markdown, no extra text)

9. MANDATORY: Every exercise MUST have a "steps" array with 3-5 items

==================================================
CRITICAL: STEPS ARRAY IS MANDATORY
==================================================

EVERY exercise MUST include a "steps" array.
DO NOT SKIP STEPS. DO NOT LEAVE EMPTY.

Example steps (correct):
"steps": [
  "Create a new component/class/file with the required name",
  "Add the necessary imports at the top",
  "Implement the basic structure from the starter template",
  "Fill in each required method/function",
  "Test your solution against the requirements"
]

==================================================
STUDENT MUST WRITE THE IMPLEMENTATION
==================================================

The boilerplate is just scaffolding.
Students will:
- Fill in the empty methods
- Write the business logic
- Connect components/modules
- Implement the full solution

Your job is ONLY the skeleton.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.7,
            messages=[
                {
                    "role": "system",
                    "content": "You are a senior coding trainer. Generate boilerplate exercises with ONLY skeleton code. NO examples. NO implementation hints. NO commented code showing solutions. Just empty structure with TODO comments. Apply this to ALL languages consistently. CRITICAL: Every exercise MUST include 3-5 clear steps in the 'steps' array. Steps should guide students through what to do without revealing the solution."
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
            "labs": parsed
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
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
                "summary": "No code submitted",
                "feedback": ["Submit some code to be evaluated"]
            }
        }

    prompt = f"""
You are an expert senior code reviewer.

Evaluate student code ONLY based on requirement completion.

==================================================
EXERCISE QUESTION
==================================================

{data.question}

==================================================
REQUIREMENTS (Each must be completed)
==================================================

{json.dumps(data.requirements, indent=2)}

==================================================
LANGUAGE
==================================================

{data.language}

==================================================
STUDENT CODE TO EVALUATE
==================================================

{data.student_code}

==================================================
EVALUATION RULES
==================================================

IMPORTANT:
1. Check if EACH requirement is fully implemented
2. Each requirement should be checked independently
3. If student implements ALL requirements correctly → Score is 10/10
4. For EACH missing/incomplete requirement → deduct based on importance
5. DO NOT penalize for:
   - Code style or formatting
   - Comments
   - Variable naming
   - Extra whitespace
   - Optional optimizations
6. ONLY penalize for:
   - Missing required functionality
   - Incomplete implementations
   - Logic errors that break requirements

Scoring Guide:
- All requirements met correctly = 10/10
- 1 minor requirement missing = 8-9/10
- 2 minor requirements missing = 6-8/10
- 1 major requirement missing = 5-7/10
- 2+ major requirements missing = 0-5/10

==================================================
RETURN ONLY JSON (no markdown, no extra text)
==================================================

{{{{
  "passed": true or false,
  "score": 0-10,
  "summary": "1-2 sentence overall evaluation",
  "feedback": [
    "Requirement 1: ✓ or ✗ status",
    "Requirement 2: ✓ or ✗ status",
    "Strength or improvement area"
  ]
}}}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": "You are a senior code reviewer. Evaluate code strictly based on requirement completion. Return ONLY valid JSON."
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