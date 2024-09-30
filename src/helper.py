readme_prompt1 = """Generate a README.md file for a repository named {repo_name}.
                Use the provided summaries to create an organized and comprehensive overview of the project and its key components.

                The README should include the following sections:

                Project Title: Display the title of the project.
                Brief Description: Provide a concise overview of the project's purpose and goals in 75 to 100 words.
                Table of Contents: Help users quickly navigate to different sections of the README.
                Project Structure: Explain the organization of files and directories within the repository.
                Installation Instructions: Step-by-step instructions to set up the project locally.
                Usage Examples: Demonstrate how to use the project, including any relevant code snippets or examples.
                Contributing Guidelines: Outline how others can contribute to the project.
                License Information: Specify the license under which the project is released.
                Contact Information: Provide details for users to reach out for support or inquiries.
                Use the following file summaries to inform the structure and details of the README:
                {summaries}
                """

code_doc_prompt = "Generate detailed documentation for the following code file. Include an overview of the file's purpose, any classes or functions defined, and important logic or algorithms:\n\nFile: {file_path}\n\nContent:\n{content}"

summary_prompt1 = "Summarize the following code or text content in a few sentences:\n\n{content}"