import streamlit as st
import os
import subprocess
import shutil
from fpdf import FPDF
import base64
import tempfile

# Import the RepositoryAnalyzer
from src.tools import RepositoryAnalyzer

def download_github_repo(repo_url, target_directory=None):
    if target_directory is None:
        target_directory = repo_url.split('/')[-1].replace('.git', '')
    
    if os.path.exists(target_directory):
        st.error(f"Error: Directory '{target_directory}' already exists.")
        return False
    
    try:
        subprocess.run(['git', 'clone', repo_url, target_directory], check=True)
        st.success(f"Successfully cloned repository to {target_directory}")
        return True
    except subprocess.CalledProcessError as e:
        st.error(f"Error: Failed to clone repository. {e}")
        return False

def get_binary_file_downloader_html(bin_file, file_label='File'):
    with open(bin_file, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{os.path.basename(bin_file)}">Download {file_label}</a>'
    return href

def markdown_to_pdf(markdown_file, pdf_file):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    with open(markdown_file, 'r', encoding='utf-8') as f:
        for line in f:
            pdf.multi_cell(0, 10, txt=line.encode('latin-1', 'replace').decode('latin-1'))
    
    pdf.output(pdf_file)
class RepoAssistant:
    def __init__(self):
        self.analyzer = RepositoryAnalyzer()

    @staticmethod
    def download_github_repo(repo_url):
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        base_dir = os.path.join(os.getcwd(), "temp_repos")
        os.makedirs(base_dir, exist_ok=True)
        
        target_directory = tempfile.mkdtemp(prefix=f"{repo_name}_", dir=base_dir)
        
        try:
            subprocess.run(['git', 'clone', repo_url, target_directory], check=True)
            st.success(f"Successfully cloned repository to {target_directory}")
            return target_directory
        except subprocess.CalledProcessError as e:
            st.error(f"Error: Failed to clone repository. {e}")
            return None

    def process_repo_input(self, repo_input):
        is_github_url = repo_input.startswith(("http://", "https://")) and "github.com" in repo_input

        if is_github_url:
            st.info("GitHub URL detected. Cloning repository...")
            repo_path = self.download_github_repo(repo_input)
            if not repo_path:
                st.stop()
        else:
            repo_path = repo_input
            if not os.path.isdir(repo_path):
                st.error("The provided path is not a valid directory.")
                st.stop()

        return repo_path, is_github_url

    def analyze_repo(self, repo_path):
        with st.spinner("Analyzing repository..."):
            try:
                file_contents, file_summaries = self.analyzer.analyze_repository(repo_path)
                st.success("Repository analyzed successfully!")
                return file_contents, file_summaries
            except Exception as e:
                st.error(f"Error analyzing repository: {str(e)}")
                st.stop()

    def generate_readme(self, repo_path, file_summaries):
        with st.spinner("Generating README..."):
            try:
                self.analyzer.generate_readme(repo_path, file_summaries)
                readme_path = os.path.join(repo_path, 'README.md')
                
                if os.path.exists(readme_path):
                    st.success("README.md generated successfully!")
                    with open(readme_path, 'r', encoding='utf-8') as f:
                        st.markdown(f.read())
                    
                    st.markdown(get_binary_file_downloader_html(readme_path, 'README.md'), unsafe_allow_html=True)
                else:
                    st.error("README.md was not created. There might be an issue with the generate_readme function.")
            except Exception as e:
                st.error(f"An error occurred while generating README: {str(e)}")

    def generate_code_documentation(self, repo_path, file_contents):
        with st.spinner("Generating code documentation..."):
            try:
                self.analyzer.generate_code_documentation(repo_path, file_contents)
                doc_path = os.path.join(repo_path, 'CODE_DOCUMENTATION.md')
                
                if os.path.exists(doc_path):
                    st.success("CODE_DOCUMENTATION.md generated successfully!")
                    with open(doc_path, 'r', encoding='utf-8') as f:
                        st.markdown(f.read())
                    
                    pdf_file = os.path.join(repo_path, 'CODE_DOCUMENTATION.pdf')
                    markdown_to_pdf(doc_path, pdf_file)
                    
                    st.markdown(get_binary_file_downloader_html(pdf_file, 'Code Documentation (PDF)'), unsafe_allow_html=True)
                else:
                    st.error("CODE_DOCUMENTATION.md was not created. There might be an issue with the generate_code_documentation function.")
            except Exception as e:
                st.error(f"An error occurred while generating code documentation: {str(e)}")

def main():
    st.title("Repository Assistant")

    repo_assistant = RepoAssistant()

    if 'repo_processed' not in st.session_state:
        st.session_state.repo_processed = False
        st.session_state.repo_path = None
        st.session_state.is_github_url = False
        st.session_state.file_contents = None
        st.session_state.file_summaries = None

    repo_input = st.text_input("Enter the path to your local repository or a GitHub URL:")

    if repo_input and not st.session_state.repo_processed:
        st.session_state.repo_path, st.session_state.is_github_url = repo_assistant.process_repo_input(repo_input)
        st.session_state.file_contents, st.session_state.file_summaries = repo_assistant.analyze_repo(st.session_state.repo_path)
        st.session_state.repo_processed = True

    if st.session_state.repo_processed:
        with st.expander("Repository Structure"):
            st.json(st.session_state.file_summaries)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Generate README"):
                repo_assistant.generate_readme(st.session_state.repo_path, st.session_state.file_summaries)

        with col2:
            if st.button("Generate Code Documentation"):
                repo_assistant.generate_code_documentation(st.session_state.repo_path, st.session_state.file_contents)

    st.sidebar.header("Instructions")
    st.sidebar.write("""
    1. Enter the path to your local repository or a GitHub URL.
    2. The repository will be automatically analyzed.
    3. Use 'Generate README' to create a README.md file.
    4. Click 'Generate Code Documentation' for detailed code docs.
    5. Download generated README and Code Documentation using the provided links.
    """)

    if st.button("Reset"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.experimental_rerun()

if __name__ == "__main__":
    main()