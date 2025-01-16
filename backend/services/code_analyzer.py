import os
import re
import shutil
import subprocess
import logging

from openai import OpenAI


logger = logging.getLogger(__name__)


class CodeQualityAnalyzer:
    _report: str = None
    _color: int = -1

    def __init__(self, owner: str, repo: str):
        self.owner = owner
        self.repo = repo
        self.local_path = "./temp_repo"

    @property
    def report(self) -> str:
        return self._report

    @property
    def color(self) -> int:
        return self._color

    def clear_local_path(self):
        if os.path.exists(self.local_path):
            shutil.rmtree(self.local_path)

    def download_repo(self):
        """Clones a GitHub repository using git."""
        try:
            # Remove the local path if it already exists to avoid conflicts
            self.clear_local_path()

            # Use git clone to download the repository
            repo_url = f'https://github.com/{self.owner}/{self.repo}'

            subprocess.run(["git", "clone", repo_url, self.local_path], check=True)
            logger.info(f"Repository cloned successfully to {self.local_path}")
            return True
        except subprocess.CalledProcessError as e:
            logger.info(f"Error cloning repository: {e}")
            return False

    def combine_files_to_string(self, max_lines: int = 500, max_chars: int = 100000, max_files: int = 100) -> str:
        """Combines files into a single string with specified limits."""
        combined_string = ""
        index = 0
        for root, _, files in os.walk(self.local_path):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                index += 1
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        if len(lines) > max_lines:
                            lines = lines[:max_lines]
                        file_content = "".join(lines)
                except Exception:
                    continue
                combined_string += file_content
                if len(combined_string) > max_chars or index >= max_files:
                    return combined_string[:max_chars]
        return combined_string

    def assess_code(self, code_snippet: str) -> str:
        """Sends code to GPT-4 mini model for assessment."""
        response = OpenAI().chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an assistant tasked with assessing code quality. "
                        "Rate the code from 1 to 10 and provide a short 1 paragraph explanation for the rating."
                    )
                },
                {
                    "role": "user",
                    "content": code_snippet
                }
            ]
        )
        return response.choices[0].message.content

    def run_analysis(self) -> str:
        """
        Runs the code assessment workflow.
        @return: The assessment report.
        """
        if not self.download_repo():
            return ''
        code_snippet = self.combine_files_to_string()
        self._report = self.assess_code(code_snippet)
        match = re.search(r'\d+', self._report)
        rate = 1
        if match:
            rate = int(match.group())
        if rate <= 3:
            self._color = -1
        elif rate <= 7:
            self._color = 0
        else:
            self._color = 1

        self.clear_local_path()


def main():
    from dotenv import load_dotenv
    load_dotenv()

    assessment = CodeQualityAnalyzer(owner='Sinaptik-AI', repo='pandas-ai').run_analysis()
    # Output assessment
    print("\nAssessment:\n")
    print(assessment)


if __name__ == "__main__":
    main()
