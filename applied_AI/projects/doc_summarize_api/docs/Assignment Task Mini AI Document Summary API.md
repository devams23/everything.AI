# **Assignment Task: Mini AI Document Summary API**

## **Objective**

Build a small Python Fast API application that accepts a .txt file, processes the content, and returns a structured summary using any local LLM.

## **Task Requirements**

API endpoint:

POST 	/summarize

## **Input**

The user will upload one .txt file.

Validation required:

1. File must not be empty.  
2. File extension must be .txt.  
3. File size should not be more than 2 MB.  
4. If validation fails, return a proper error response.

## **Processing Steps**

After receiving the file:

1. Read the file content.  
2. data preprocessing  
3. If the text is very long, split it into smaller chunks.  
4. Summarise the content. (Use an LLM such as Gamma, Llama, Qwen, or any other suitable open-source model.

## **Expected API Response**

The API should return response in this format:

{  
  "status": "success",  
  "filename": "sample.txt",  
  "summary": {  
    "title": "Short title of the document",  
    "summary": "Short summary of the document",  
    "key\_points": \[  
      "Important point 1",  
      "Important point 2",  
      "Important point 3"  
    \]  
  }  
}

For error cases:

{  
  "status": "error",  
  "message": "Only .txt files are allowed"  
}

## **Required Project Structure**

Try to maintain this kind of structure:

* **Root directory:**  
  * main.py  
  * requirements.txt  
  * README.md  
* **services/ directory:**  
  * file\_service.py  
  * llm\_service.py

## **Required Features**

Your project should include:

1. Fast API endpoint for file upload.  
2. File validation.  
3. Text cleaning function.  
4. Text chunking function.  
5. Summary generation function.  
6. Proper exception handling.  
7. Logging for important steps.  
8. Clear README file with setup and runs instructions.

## **Bonus Points**

These are optional but good to add:

1. Add /health endpoint.  
2. Handle long text using chunk-wise summary.

## **Submission**

Submit:

1. Complete source code.  
2. requirements.txt.  
3. README file.