import os
import stat
import shutil
import tempfile
import uuid
from pathlib import Path
import subprocess
from typing import List, Dict, Any
import errno
import time

class CodeAnalyzer:
    def __init__(self):
        # Create a unique directory name in the user's temp directory
        self.user_temp = Path(tempfile.gettempdir()) / "startech_vc" / str(uuid.uuid4())
        self.user_temp.parent.mkdir(exist_ok=True)
        self.user_temp.mkdir(exist_ok=True)

    def _run_command(self, command: List[str], cwd: str = None) -> str:
        """Run a command and return its output."""
        try:
            # Use shell=True on Windows to handle permission issues
            is_windows = os.name == 'nt'
            result = subprocess.run(
                command if not is_windows else " ".join(command),
                cwd=cwd,
                capture_output=True,
                text=True,
                shell=is_windows,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Command failed: {e.cmd}")
            print(f"Error output: {e.stderr}")
            return ""

    def _make_writable(self, path: str):
        """Make a file or directory writable."""
        try:
            mode = os.stat(path).st_mode
            os.chmod(path, mode | stat.S_IWRITE)
        except Exception as e:
            print(f"Failed to make path writable: {path}, error: {e}")

    def _remove_readonly_recursive(self, path: str):
        """Recursively remove read-only attribute from all files and directories."""
        if os.path.isdir(path):
            for root, dirs, files in os.walk(path, topdown=False):
                for name in files:
                    self._make_writable(os.path.join(root, name))
                for name in dirs:
                    self._make_writable(os.path.join(root, name))
        self._make_writable(path)

    def clone_repo(self, repo_url: str) -> str:
        """Clone a repository and return the path to the cloned directory."""
        try:
            # Create a new unique directory for this repo
            repo_path = self.user_temp / str(uuid.uuid4())
            repo_path.mkdir(exist_ok=True)

            # Clone the repository
            self._run_command(['git', 'clone', repo_url, str(repo_path)])
            return str(repo_path)
        except Exception as e:
            print(f"Failed to clone repository: {e}")
            return ""

    def analyze_code(self, repo_path: str) -> Dict[str, Any]:
        """Analyze the code in the repository."""
        result = {
            "languages": {},
            "commit_stats": {},
            "complexity": {}
        }

        if not repo_path or not os.path.exists(repo_path):
            print("Repository path does not exist")
            return result

        try:
            # Get language statistics
            try:
                result["languages"] = self._get_language_stats(repo_path)
            except Exception as e:
                print(f"Failed to get language stats: {e}")

            # Get commit statistics
            try:
                result["commit_stats"] = self._get_commit_stats(repo_path)
            except Exception as e:
                print(f"Failed to get commit stats: {e}")

            # Get code complexity metrics
            try:
                result["complexity"] = self._get_code_complexity(repo_path)
            except Exception as e:
                print(f"Failed to get code complexity: {e}")

        except Exception as e:
            print(f"Error during code analysis: {e}")
        finally:
            try:
                self.cleanup()
            except Exception as e:
                print(f"Failed to cleanup, but continuing: {e}")

        return result

    def _get_language_stats(self, repo_path: str) -> Dict[str, float]:
        """Get language statistics using linguist."""
        try:
            output = self._run_command(['github-linguist'], cwd=repo_path)
            languages = {}
            for line in output.split('\n'):
                if line.strip():
                    try:
                        percentage, language = line.strip().split('%')
                        languages[language.strip()] = float(percentage.strip())
                    except ValueError:
                        continue
            return languages
        except Exception as e:
            print(f"Failed to get language stats: {e}")
            return {}

    def _get_commit_stats(self, repo_path: str) -> Dict[str, int]:
        """Get commit statistics."""
        try:
            # Get total number of commits
            commit_count = self._run_command(
                ['git', 'rev-list', '--count', 'HEAD'],
                cwd=repo_path
            ).strip()

            # Get number of contributors
            contributors = self._run_command(
                ['git', 'shortlog', '-s', '-n', '--all'],
                cwd=repo_path
            ).count('\n')

            # Get average commits per week
            weekly_commits = self._run_command(
                ['git', 'log', '--pretty=format:%ct', '--reverse'],
                cwd=repo_path
            ).split('\n')
            
            if len(weekly_commits) > 1:
                first_commit = int(weekly_commits[0])
                last_commit = int(weekly_commits[-1])
                weeks = (last_commit - first_commit) / (7 * 24 * 60 * 60)
                commits_per_week = len(weekly_commits) / max(1, weeks)
            else:
                commits_per_week = 0

            return {
                "total_commits": int(commit_count) if commit_count else 0,
                "contributors": contributors,
                "commits_per_week": round(commits_per_week, 2)
            }
        except Exception as e:
            print(f"Failed to get commit stats: {e}")
            return {}

    def _get_code_complexity(self, repo_path: str) -> Dict[str, Any]:
        """Get code complexity metrics using radon."""
        try:
            # Get cyclomatic complexity
            complexity_output = self._run_command(
                ['radon', 'cc', '.', '-a', '-j'],
                cwd=repo_path
            )

            # Get maintainability index
            mi_output = self._run_command(
                ['radon', 'mi', '.', '-j'],
                cwd=repo_path
            )

            return {
                "cyclomatic_complexity": complexity_output,
                "maintainability_index": mi_output
            }
        except Exception as e:
            print(f"Failed to get code complexity: {e}")
            return {}

    def cleanup(self):
        """Clean up temporary files."""
        def handle_remove_readonly(func, path, exc):
            excvalue = exc[1]
            if func in (os.rmdir, os.remove, os.unlink) and excvalue.errno in (errno.EACCES, errno.EPERM):
                # Make the file writable and try again
                self._remove_readonly_recursive(path)
                try:
                    func(path)
                except Exception as e:
                    # If still failing, try to force close any open handles (Windows)
                    if os.name == 'nt':
                        time.sleep(0.1)  # Small delay to let any file handles close
                        try:
                            if os.path.exists(path):
                                os.chmod(path, stat.S_IWRITE | stat.S_IEXEC | stat.S_IREAD)
                                func(path)
                        except Exception as final_e:
                            print(f"Final attempt to remove {path} failed: {final_e}")
            else:
                raise

        try:
            if self.user_temp.exists():
                # First, try to remove read-only attributes
                self._remove_readonly_recursive(str(self.user_temp))
                
                # If it's a git repo, try to clean it first
                git_dir = os.path.join(str(self.user_temp), '.git')
                if os.path.exists(git_dir):
                    try:
                        self._run_command(['git', 'clean', '-fd'], cwd=str(self.user_temp))
                        self._run_command(['git', 'gc'], cwd=str(self.user_temp))
                    except Exception as e:
                        print(f"Failed to clean git repository: {e}")

                # Now try to remove the directory
                retries = 3
                for i in range(retries):
                    try:
                        shutil.rmtree(str(self.user_temp), onerror=handle_remove_readonly)
                        break
                    except Exception as e:
                        if i == retries - 1:
                            print(f"Failed to cleanup temporary files after {retries} attempts: {e}")
                        else:
                            time.sleep(0.5)  # Wait a bit before retrying
        except Exception as e:
            print(f"Failed to cleanup temporary files: {e}")

    def __del__(self):
        """Ensure cleanup on object destruction."""
        self.cleanup() 