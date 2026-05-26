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
    steps: list[str] = []  # Optional: for aligned feedback


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

    # Format requirements for clarity
    requirements_text = ""
    for i, req in enumerate(data.requirements, 1):
        requirements_text += f"{i}. {req}\n"

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
QUESTION / EXERCISE
========================================

{data.question}

========================================
REQUIREMENTS TO IMPLEMENT
========================================

{requirements_text}

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
  // TODO: Create state for the message
  
  // TODO: Create a handler function to update the message
  
  // TODO: Pass the message to the Child component as a prop

  return (
    <div>
      {{/* TODO: Render the Child component with props */}}
    </div>
  );
}};

export default ParentComponent;

PYTHON:
class Parent:
    def __init__(self):
        # TODO: Initialize message attribute
        pass
    
    def send_message(self):
        # TODO: Implement message sending logic
        pass

JAVA:
public class Parent {{
    // TODO: Declare message variable
    
    public Parent() {{
        // TODO: Constructor implementation
    }}
    
    public void sendMessage() {{
        // TODO: Implement message logic
    }}
}}

C#:
public class Parent {{
    // TODO: Declare message field
    
    public Parent() {{
        // TODO: Initialize
    }}
    
    public void SendMessage() {{
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
                    "content": "You are a senior software architect. Generate ONLY bare skeleton boilerplate code. NO examples. NO implementation hints. NO commented code showing solutions. Just empty structure with TODO comments. For component communication exercises, create empty component files with TODO comments for props, state, and handlers."
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
ALIGNMENT RULE (MOST CRITICAL - READ FIRST)
==================================================

⚠️ STEPS, REQUIREMENTS, and BOILERPLATE MUST ALIGN

Steps = WHAT student does (actions/tasks)
Requirements = WHAT must be implemented (outcomes)
Boilerplate TODOs = Specific code skeleton for each step

RULE: For each step, create exactly one requirement.
      For each step, create one TODO in the starter_template.

EXAMPLE OF PROPER ALIGNMENT:

Step 1: "Create a new Parent component file"
→ Requirement 1: "Parent component file created"
→ Boilerplate TODO: [Already provided - import React; const Parent = () => {...}]

Step 2: "Add useState hook for message state"
→ Requirement 2: "State variable created with useState"
→ Boilerplate TODO: // TODO: Create state variable using useState

Step 3: "Create handler to update the message"
→ Requirement 3: "Event handler function implemented"
→ Boilerplate TODO: // TODO: Create handler function

Step 4: "Import Child component"
→ Requirement 4: "Child component imported"
→ Boilerplate TODO: // TODO: Import Child component

Step 5: "Render Child with message prop"
→ Requirement 5: "Child rendered with message prop passed"
→ Boilerplate TODO: // TODO: Render Child component and pass message

⚠️ FAILURE EXAMPLES (DO NOT DO THIS):
✗ Step 1, 2, 3 but Requirement 1 about something from Step 5
✗ Too many TODOs that don't match steps
✗ Steps that don't have corresponding requirements

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
                    "content": "You are a senior coding trainer. CRITICAL: steps, requirements, and boilerplate TODOs MUST align perfectly. For each step, create exactly one matching requirement. For each requirement, create one TODO in starter_template. NO mismatches. NEVER create unaligned steps/requirements. Generate skeleton code only - NO examples, NO hints. Each TODO must correspond to exactly one step."
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

    # Format requirements and steps for clarity in evaluation
    requirements_text = ""
    for i, req in enumerate(data.requirements, 1):
        step_ref = ""
        if data.steps and i <= len(data.steps):
            step_ref = f"\n   (This step: {data.steps[i-1]})"
        requirements_text += f"{i}. {req}{step_ref}\n"

    steps_text = ""
    if data.steps:
        steps_text = "\n==================================================\nSTEPS (What student should do)\n==================================================\n\n"
        for i, step in enumerate(data.steps, 1):
            steps_text += f"{i}. {step}\n"

    prompt = f"""
You are an expert senior code reviewer.

Evaluate student code STRICTLY based on requirement completion.

These requirements are ALIGNED 1:1 with exercise steps.
- Step 1 ↔ Requirement 1
- Step 2 ↔ Requirement 2
- etc.

==================================================
EXERCISE QUESTION
==================================================

{data.question}
{steps_text}

==================================================
REQUIREMENTS TO CHECK (Each must be completed)
==================================================

{requirements_text}

==================================================
LANGUAGE
==================================================

{data.language}

==================================================
STUDENT CODE TO EVALUATE
==================================================

{data.student_code}

==================================================
EVALUATION INSTRUCTIONS
==================================================

CRITICAL: Each requirement aligns with a step.
Your feedback should reference BOTH the step and requirement.

EXAMPLE:
"Step 1 / Requirement 1: ✓ Parent component file created successfully"
"Step 2 / Requirement 2: ✗ useState hook not implemented"

STEP 1: Read requirements carefully
- Understand exactly what EACH requirement asks for
- Match it to the corresponding step
- Be specific about what counts as "implemented"

STEP 2: Analyze the student code
- Check if the code exists and is not commented out
- Verify if it actually implements the requirement
- Look for functional implementation, not just structure

STEP 3: Rate each requirement (✓ = Complete, ✗ = Missing/Incomplete)
- ✓ Only if FULLY implemented and functional
- ✗ If missing, incomplete, or non-functional

STEP 4: Calculate score
- Count how many requirements are ✓
- If ALL requirements are ✓ → Score is 10/10
- If some are ✗ → Deduct 2-3 points per missing major requirement, 1-2 per minor
- Minimum score: 0, Maximum score: 10

STEP 5: DO NOT PENALIZE for:
- Code style or formatting (spacing, indentation)
- Comments or lack thereof
- Variable naming conventions
- Extra whitespace or blank lines
- Different coding approaches (as long as they work)
- Minor syntax variations
- Optional optimizations

STEP 6: ONLY PENALIZE for:
- Missing functionality from requirements
- Incomplete or partially-implemented requirements
- Code that doesn't work or has logic errors
- Missing key components or methods

==================================================
RETURN ONLY VALID JSON (no markdown, no extra text)
==================================================

{{{{
  "passed": true or false (true only if score >= 8),
  "score": 0-10,
  "summary": "1-2 sentence overall evaluation",
  "feedback": [
    "Step 1 / Requirement 1: ✓ or ✗ with brief explanation",
    "Step 2 / Requirement 2: ✓ or ✗ with brief explanation",
    "Step N / Requirement N: ✓ or ✗ with brief explanation",
    "Additional feedback on strengths or improvements needed"
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
                    "content": "You are a strict but fair senior code reviewer. Evaluate code objectively based on requirement completion. Check if each requirement is ACTUALLY IMPLEMENTED, not just structured. Return ONLY valid JSON. Be precise about what is working and what is missing."
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