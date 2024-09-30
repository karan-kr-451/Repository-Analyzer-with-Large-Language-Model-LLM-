import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Dict, Tuple

from langchain.llms import Ollama
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

# Assuming these are imported from a separate file
from src.helper import readme_prompt1, code_doc_prompt, summary_prompt1

@dataclass
class FileInfo:
    content: str
    summary: str

class RepositoryAnalyzer:
    def __init__(self, model="llama3.2", temperature=0.7):
        self.ollama = Ollama(model=model, temperature=temperature)
        self.file_extensions = ('.py', '.js', '.html', '.css', '.md', '.txt', '.yml', '.yaml')
        self.excluded_folders = {'env', 'venv', '.git', '__pycache__', 'node_modules'}

    def analyze_repository(self, repo_path: str) -> Tuple[Dict[str, str], Dict[str, str]]:
        file_contents = {}
        file_summaries = {}

        with ThreadPoolExecutor() as executor:
            futures = []
            for root, dirs, files in os.walk(repo_path):
                # Remove excluded folders from dirs to prevent os.walk from traversing them
                dirs[:] = [d for d in dirs if d not in self.excluded_folders]
                
                for file in files:
                    if file.endswith(self.file_extensions):
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, repo_path)
                        futures.append(executor.submit(self.process_file, file_path, relative_path))

            for future in as_completed(futures):
                relative_path, file_info = future.result()
                if file_info:
                    file_contents[relative_path] = file_info.content
                    file_summaries[relative_path] = file_info.summary

        return file_contents, file_summaries

    def process_file(self, file_path: str, relative_path: str) -> Tuple[str, FileInfo]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            summary_prompt = PromptTemplate(
                input_variables=["content"],
                template=summary_prompt1
            )
            summary_chain = LLMChain(llm=self.ollama, prompt=summary_prompt)
            summary = summary_chain.run(content=content).strip()

            return relative_path, FileInfo(content, summary)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return relative_path, None


    def generate_readme(self, repo_path: str, file_summaries: Dict[str, str]):
        readme_prompt = PromptTemplate(
            input_variables=["repo_name", "summaries"],
            template=readme_prompt1
        )
        readme_chain = LLMChain(llm=self.ollama, prompt=readme_prompt)
        repo_name = os.path.basename(repo_path)
        summaries_text = json.dumps(file_summaries, indent=2)
        readme_content = readme_chain.run(repo_name=repo_name, summaries=summaries_text)

        with open(os.path.join(repo_path, 'README.md'), 'w', encoding='utf-8') as f:
            f.write(readme_content)

        print("README.md generated successfully.")

    def generate_code_documentation(self, repo_path: str, file_contents: Dict[str, str]):
        doc_prompt = PromptTemplate(
            input_variables=["file_path", "content"],
            template=code_doc_prompt
        )
        doc_chain = LLMChain(llm=self.ollama, prompt=doc_prompt)

        documentation = {}
        for file_path, content in file_contents.items():
            if file_path.endswith(('.py', '.js')):
                doc = doc_chain.run(file_path=file_path, content=content)
                documentation[file_path] = doc.strip()

        doc_file_path = os.path.join(repo_path, 'CODE_DOCUMENTATION.md')
        with open(doc_file_path, 'w', encoding='utf-8') as f:
            for file_path, doc in documentation.items():
                f.write(f"# {file_path}\n\n{doc}\n\n---\n\n")

        print("CODE_DOCUMENTATION.md generated successfully.")

def main(repo_path: str):
    analyzer = RepositoryAnalyzer()
    file_contents, file_summaries = analyzer.analyze_repository(repo_path)
    analyzer.generate_readme(repo_path, file_summaries)
    analyzer.generate_code_documentation(repo_path, file_contents)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python script.py <repo_path>")
        sys.exit(1)
    main(sys.argv[1])