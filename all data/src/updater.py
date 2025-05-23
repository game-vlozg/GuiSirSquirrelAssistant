import os
import sys
import json
import urllib.request
import urllib.error
import zipfile
import shutil
import logging
import subprocess
import platform
import threading
import fnmatch
import configparser  # Add this import for config modification
from datetime import datetime

# Configure logging
logger = logging.getLogger("updater")

# Define exclusions - files/directories that should never be updated
EXCLUDED_PATHS = [
    "config/",     # All user settings/configurations  
    "backups/",    # Backup directory
    "_temp/",      # Temporary files
    "*.log"        # Any log files (including Pro_Peepol's.log)
]

class Updater:
    """Class for checking and applying updates from a GitHub repository"""
    
    def __init__(self, repo_owner, repo_name, current_version_file="version.json", 
                 backup_folder="backups", temp_folder="_temp", api_url=None):
        """Initialize the updater with repository information"""
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.current_version_file = current_version_file
        self.backup_folder = backup_folder
        self.temp_folder = temp_folder
        self.exclusions = EXCLUDED_PATHS
        
        # Default GitHub API URL if none provided
        if api_url is None:
            self.api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        else:
            self.api_url = api_url
            
        # Determine base path and set up correct directory structure
        if getattr(sys, 'frozen', False):
            # Running as compiled exe
            self.base_path = os.path.dirname(sys.executable)
        else:
            # Running as script
            script_path = os.path.abspath(__file__)
            self.base_path = os.path.dirname(script_path)
        
        # Determine parent directories structure
        if os.path.basename(self.base_path) == "src":
            # We're in src folder inside all data
            # src > all data > parent_dir
            self.all_data_dir = os.path.dirname(self.base_path)
            self.parent_dir = os.path.dirname(self.all_data_dir)
        elif os.path.basename(self.base_path) == "all data":
            # We're directly in all_data
            self.all_data_dir = self.base_path
            self.parent_dir = os.path.dirname(self.all_data_dir)
        else:
            # We're in some other location, assume it's the parent directory
            self.parent_dir = self.base_path
            self.all_data_dir = os.path.join(self.parent_dir, "all data")
        
        # Create full paths
        self.version_file_path = os.path.join(self.parent_dir, current_version_file)
        
        # Put backup folder in parent directory (same level as 'all data')
        self.backup_path = os.path.join(self.parent_dir, backup_folder)
        
        # Temp directory in parent directory (same level as 'all data')
        self.temp_path = os.path.join(self.parent_dir, temp_folder)
        
        # Ensure directories exist
        os.makedirs(self.backup_path, exist_ok=True)
        os.makedirs(self.temp_path, exist_ok=True)
        
        logger.info(f"Updater initialized for {repo_owner}/{repo_name}")
        logger.info(f"Parent directory: {self.parent_dir}")
        logger.info(f"All data directory: {self.all_data_dir}")
        logger.info(f"Backup path: {self.backup_path}")
        logger.info(f"Temp path: {self.temp_path}")
        
    def get_current_version(self):
        """Get the current version from the local version file"""
        try:
            if os.path.exists(self.version_file_path):
                with open(self.version_file_path, 'r') as f:
                    version = f.read().strip()
                    return version if version else 'v0'
            return 'v0'  # Default version if file doesn't exist
        except Exception as e:
            logger.error(f"Error reading version file: {e}")
            return 'v0'
            
    def get_latest_version(self):
        """Check the GitHub API for the latest version from version.json file"""
        try:
            # First try to get the latest release
            release_url = f"{self.api_url}/releases/latest"
            
            try:
                with urllib.request.urlopen(release_url) as response:
                    if response.getcode() == 200:
                        release_data = json.loads(response.read().decode())
                        return release_data['tag_name'], release_data['zipball_url']
            except urllib.error.HTTPError as e:
                # If no releases found (404), check the version.json file directly
                if e.code != 404:
                    raise
                    
            # Fall back to checking version.json file in the repository
            version_file_url = f"https://raw.githubusercontent.com/{self.repo_owner}/{self.repo_name}/main/version.json"
            
            try:
                with urllib.request.urlopen(version_file_url) as response:
                    if response.getcode() == 200:
                        repo_version = response.read().decode().strip()
                        logger.info(f"Repository version.json content: '{repo_version}'")
                        if repo_version:
                            # Use the zipball URL for the main branch
                            download_url = f"{self.api_url}/zipball/main"
                            return repo_version, download_url
            except Exception as e:
                logger.warning(f"Could not read version.json from repository: {e}")
                    
            # Final fallback to latest commit on main branch
            commits_url = f"{self.api_url}/commits/main"
            with urllib.request.urlopen(commits_url) as response:
                commit_data = json.loads(response.read().decode())
                commit_hash = commit_data['sha']
                # Generate a version number based on the commit date
                commit_date = commit_data['commit']['committer']['date'].split('T')[0].replace('-', '.')
                download_url = f"{self.api_url}/zipball/{commit_hash}"
                return f"commit-{commit_date}", download_url
                
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return None, None
    
    def check_for_updates(self):
        """Check if updates are available"""
        current_version = self.get_current_version()
        latest_version, download_url = self.get_latest_version()
        
        if latest_version is None:
            logger.warning("Failed to retrieve latest version information")
            return False, None, None
        
        # Clean up versions for comparison (remove any whitespace)
        current_clean = current_version.strip() if current_version else ""
        latest_clean = latest_version.strip() if latest_version else ""
        
        # Debug logging
        logger.info(f"Current version: '{current_clean}' (length: {len(current_clean)})")
        logger.info(f"Latest version: '{latest_clean}' (length: {len(latest_clean)})")
        logger.info(f"Versions equal: {current_clean == latest_clean}")
            
        # Check if we need to update (simple string comparison)
        if current_clean != latest_clean:
            logger.info(f"Update available: {current_clean} -> {latest_clean}")
            return True, latest_clean, download_url
        else:
            logger.info(f"Already up to date: {current_clean}")
            return False, latest_clean, None

    def should_exclude(self, file_path):
        """Check if a file should be excluded from updates"""
        # Convert to Unix-style path for consistent matching
        normalized_path = file_path.replace("\\", "/")
        
        # Explicitly exclude anything in the config directory
        if normalized_path.startswith("all data/config/") or normalized_path == "all data/config":
            return True
            
        # Explicitly exclude backup and temp folders
        if normalized_path.startswith(f"{self.backup_folder}/") or normalized_path == self.backup_folder:
            return True
            
        if normalized_path.startswith(f"{self.temp_folder}/") or normalized_path == self.temp_folder:
            return True
        
        for pattern in self.exclusions:
            # Exact match
            if normalized_path == pattern:
                return True
                
            # Directory match (ends with /)
            if pattern.endswith("/") and normalized_path.startswith(pattern):
                return True
                
            # Wildcard match (using glob patterns)
            if "*" in pattern and fnmatch.fnmatch(normalized_path, pattern):
                return True
        
        return False
    
    def download_update(self, download_url):
        """Download the update file"""
        # Clear temp directory if it exists (but don't recreate it)
        try:
            # Just clear contents of temp directory without removing it
            for item in os.listdir(self.temp_path):
                item_path = os.path.join(self.temp_path, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
            logger.info(f"Cleared temp directory {self.temp_path}")
        except Exception as e:
            logger.warning(f"Error clearing temp directory: {e}")
        
        try:
            # Ensure temp directory exists
            os.makedirs(self.temp_path, exist_ok=True)
            
            # Download the zip file
            zip_path = os.path.join(self.temp_path, 'update.zip')
            logger.info(f"Downloading update from {download_url}")
            
            with urllib.request.urlopen(download_url) as response, open(zip_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
                
            logger.info(f"Download completed: {zip_path}")
            return zip_path
        except Exception as e:
            logger.error(f"Error downloading update: {e}")
            return None
    
    def modify_backup_config(self, backup_dir):
        """
        Modify the backup's config to disable auto-update, preventing update loops.
        IMPORTANT: This only modifies the BACKUP config, not the current/real config!
        """
        # Possible locations for gui_config.txt in the backup
        possible_config_paths = [
            os.path.join(backup_dir, "all data", "config", "gui_config.txt"),
            os.path.join(backup_dir, "config", "gui_config.txt"),
        ]
        
        # Search for gui_config.txt in the backup directory if not found in expected locations
        config_path = None
        for path in possible_config_paths:
            if os.path.exists(path):
                config_path = path
                break
        
        # If not found in expected locations, search the entire backup directory
        if not config_path:
            for root, dirs, files in os.walk(backup_dir):
                if "gui_config.txt" in files:
                    config_path = os.path.join(root, "gui_config.txt")
                    break
        
        if not config_path or not os.path.exists(config_path):
            logger.warning(f"Could not find gui_config.txt in backup directory {backup_dir}")
            logger.info("This is not critical - backup will work normally, just won't prevent update loops")
            return False
        
        try:
            logger.info(f"Modifying backup config at: {config_path}")
            
            # Load the backup's config file (NOT the current one!)
            config = configparser.ConfigParser()
            config.read(config_path)
            
            # Ensure Settings section exists
            if 'Settings' not in config:
                config['Settings'] = {}
            
            # Get current values for logging
            old_auto_update = config.get('Settings', 'auto_update', fallback='Unknown')
            old_notifications = config.get('Settings', 'update_notifications', fallback='Unknown')
            
            # Disable auto-update and notifications in the BACKUP ONLY
            config.set('Settings', 'auto_update', 'False')
            config.set('Settings', 'update_notifications', 'False')
            
            # Add a note to indicate this is a backup (optional)
            config.set('Settings', '_backup_version', 'True')
            
            # Write the modified config back to the BACKUP location only
            with open(config_path, 'w') as configfile:
                config.write(configfile)
            
            logger.info(f"[SUCCESS] Successfully modified backup config:")
            logger.info(f"   - auto_update: {old_auto_update} -> False")
            logger.info(f"   - update_notifications: {old_notifications} -> False")
            logger.info(f"   - Location: {config_path}")
            logger.info("   - Original config remains unchanged!")
            
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Error modifying backup config: {e}")
            logger.info("Backup creation will continue, but update loop prevention failed")
            return False
    
    def backup_current_version(self):
        """Create a backup of the current version"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}"
        backup_dir = os.path.join(self.backup_path, backup_name)
        
        logger.info(f"Creating backup at {backup_dir}")
        
        try:
            # Make sure backup directory exists
            try:
                # Create parent directory first, then the specific backup directory
                os.makedirs(self.backup_path, exist_ok=True)
                os.makedirs(backup_dir, exist_ok=True)
                logger.info(f"Successfully created backup directory at {backup_dir}")
            except Exception as e:
                logger.error(f"Failed to create backup directory at {backup_dir}: {e}")
                return None
            
            # We want to back up the parent directory that contains 'all data'
            source_dir = self.parent_dir
            logger.info(f"Backing up contents from {source_dir}")
            
            # Count files for logging
            file_count = 0
            dir_count = 0
            
            # Copy all files and directories from parent_dir to backup_dir
            # excluding the backup, _temp, and extracted folders
            for item in os.listdir(source_dir):
                item_path = os.path.join(source_dir, item)
                backup_item_path = os.path.join(backup_dir, item)
                
                # Skip backup, _temp, and extracted folders
                if item == self.backup_folder or item == self.temp_folder or item == "extracted":
                    logger.info(f"Skipping {item} folder from backup")
                    continue
                
                try:
                    if os.path.isdir(item_path):
                        # For directories, use copytree with ignore function
                        def ignore_func(src, names):
                            return [n for n in names if 
                                    n == self.backup_folder or 
                                    n == self.temp_folder or 
                                    n == "extracted" or
                                    n.endswith('.log')]
                                
                        shutil.copytree(item_path, backup_item_path, 
                                      ignore=ignore_func)
                        dir_count += 1
                        logger.info(f"Backed up directory: {item}")
                    else:
                        # Skip log files
                        if item.endswith('.log'):
                            logger.info(f"Skipping log file: {item}")
                            continue
                            
                        shutil.copy2(item_path, backup_item_path)
                        file_count += 1
                        logger.info(f"Backed up file: {item}")
                except Exception as e:
                    logger.error(f"Failed to backup {item}: {e}")
                    # Continue with other files instead of failing completely
            
            logger.info(f"Backup completed successfully: {file_count} files and {dir_count} directories")
            
            # IMPORTANT: Now modify the backup's config to prevent update loops
            # This ONLY affects the backup, NOT the current config!
            logger.info("Modifying backup config to prevent update loops...")
            self.modify_backup_config(backup_dir)
            
            return backup_dir
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return None
    
    def apply_update(self, zip_path):
        """Extract and apply the update"""
        if not zip_path or not os.path.exists(zip_path):
            logger.error("Invalid zip file path")
            return False
            
        try:
            # Extract the zip file directly to _temp directory
            # We'll use the _temp directory directly instead of creating a new "extracted" folder
            logger.info(f"Extracting update to {self.temp_path}")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.temp_path)
                
            # GitHub zip files contain a top-level folder with the repo name and commit hash
            # We need to get the name of this folder
            subdirs = [d for d in os.listdir(self.temp_path) if os.path.isdir(os.path.join(self.temp_path, d)) and d != "extracted"]
            if not subdirs:
                logger.error("No repository directories found in extracted zip")
                return False
                
            repo_dir = os.path.join(self.temp_path, subdirs[0])
            logger.info(f"Found repository directory: {repo_dir}")
            
            # Now copy files to the PARENT directory, NOT just all_data
            # This is the key change - we're updating the parent directory structure
            self._copy_directory_with_exclusions(repo_dir, self.parent_dir)
            
            # Handle deleted files in the parent directory
            self._handle_deleted_files(repo_dir)
            
            logger.info("Update applied successfully")
            return True
        except Exception as e:
            logger.error(f"Error applying update: {e}")
            return False
    
    def _copy_directory_with_exclusions(self, src_dir, dest_dir):
        """Recursively copy a directory while respecting exclusions"""
        # Create the destination directory if it doesn't exist
        os.makedirs(dest_dir, exist_ok=True)
        
        file_count = 0
        dir_count = 0
        
        # Walk through the source directory
        for root, dirs, files in os.walk(src_dir):
            # Calculate the relative path from the source directory
            rel_path = os.path.relpath(root, src_dir)
            
            # Skip excluded directories
            if rel_path != "." and self.should_exclude(rel_path.replace("\\", "/")):
                logger.info(f"Skipping excluded directory: {rel_path}")
                
                # Remove from dirs to prevent descending into it
                for excluded_dir in list(dirs):
                    if self.should_exclude(os.path.join(rel_path, excluded_dir).replace("\\", "/")):
                        dirs.remove(excluded_dir)
                continue
                
            # Process files
            for file in files:
                # Get the path relative to the repository root
                if rel_path == ".":
                    file_rel_path = file
                else:
                    file_rel_path = os.path.join(rel_path, file).replace("\\", "/")
                
                # Skip if this file should be excluded
                if self.should_exclude(file_rel_path):
                    logger.info(f"Skipping excluded file: {file_rel_path}")
                    continue
                
                # Copy the file
                src_file = os.path.join(root, file)
                dest_file = os.path.join(dest_dir, rel_path, file)
                
                # Create parent directories if needed
                os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                
                try:
                    # Skip self - don't update our own script if running from the directory being updated
                    if os.path.samefile(src_file, __file__) if os.path.exists(dest_file) else False:
                        logger.info(f"Skipping update to self: {file_rel_path}")
                        continue
                        
                    # Remove existing file if any
                    if os.path.exists(dest_file):
                        os.remove(dest_file)
                    
                    # Copy the file
                    shutil.copy2(src_file, dest_file)
                    file_count += 1
                    logger.debug(f"Updated file: {file_rel_path}")
                except Exception as e:
                    logger.error(f"Failed to update file {file_rel_path}: {e}")
        
        logger.info(f"Update copied {file_count} files")
    
    def _handle_deleted_files(self, extracted_repo_dir):
        """Remove files that have been deleted in the repository"""
        # Get list of all files in the extracted repository (excluding excluded paths)
        repo_files = set()
        for root, dirs, files in os.walk(extracted_repo_dir):
            # Skip excluded directories to prevent descending into them
            dirs_to_remove = []
            for d in dirs:
                rel_path = os.path.relpath(os.path.join(root, d), extracted_repo_dir).replace("\\", "/")
                if self.should_exclude(rel_path):
                    dirs_to_remove.append(d)
            
            # Remove excluded directories from the dirs list
            for d in dirs_to_remove:
                dirs.remove(d)
                
            for file in files:
                # Get path relative to repo root
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, extracted_repo_dir)
                
                # Normalize path
                normalized_path = rel_path.replace("\\", "/")
                
                # Skip excluded paths
                if not self.should_exclude(normalized_path):
                    repo_files.add(normalized_path)
        
        # Get list of all files in the parent directory
        app_files = set()
        for root, dirs, files in os.walk(self.parent_dir):
            # Skip excluded directories
            rel_root = os.path.relpath(root, self.parent_dir).replace("\\", "/")
            if self.should_exclude(rel_root):
                # Skip this directory
                dirs[:] = []  # Clear dirs list to prevent descending
                continue
                
            for file in files:
                # Get path relative to app root
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, self.parent_dir)
                
                # Normalize path
                normalized_path = rel_path.replace("\\", "/")
                
                # Skip excluded paths
                if not self.should_exclude(normalized_path):
                    app_files.add(normalized_path)
        
        # Find files that exist in app but not in repo
        deleted_files = app_files - repo_files
        
        # Remove these files (but never touch excluded paths)
        deleted_count = 0
        for file_path in deleted_files:
            # Check exclusions one more time for safety
            if self.should_exclude(file_path):
                logger.info(f"Protected excluded file from deletion: {file_path}")
                continue
                
            full_path = os.path.join(self.parent_dir, file_path)
            try:
                # Skip self - don't delete our own script
                if os.path.samefile(full_path, __file__) if os.path.exists(full_path) else False:
                    logger.info(f"Skipping deletion of self: {file_path}")
                    continue
                    
                os.remove(full_path)
                deleted_count += 1
                logger.info(f"Removed deleted file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to remove deleted file {file_path}: {e}")
        
        logger.info(f"Removed {deleted_count} deleted files")
        
        # Also remove empty directories (but never excluded ones)
        for root, dirs, files in os.walk(self.parent_dir, topdown=False):
            # Skip excluded directories completely
            rel_path = os.path.relpath(root, self.parent_dir).replace("\\", "/")
            if self.should_exclude(rel_path):
                continue
                
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                rel_dir_path = os.path.relpath(dir_path, self.parent_dir).replace("\\", "/")
                
                # Skip excluded directories
                if self.should_exclude(rel_dir_path):
                    continue
                    
                # Try to remove if empty
                try:
                    if not os.listdir(dir_path):
                        os.rmdir(dir_path)  # This only removes if directory is empty
                        logger.info(f"Removed empty directory: {rel_dir_path}")
                except OSError as e:
                    # Directory not empty or other error
                    logger.debug(f"Could not remove directory {rel_dir_path}: {e}")
    
    def update_version_file(self, version):
        """Update the version file with the new version information"""
        try:
            with open(self.version_file_path, 'w') as f:
                f.write(version)
                
            logger.info(f"Version file updated to {version}")
            return True
        except Exception as e:
            logger.error(f"Error updating version file: {e}")
            return False
    
    def clean_temp_files(self):
        """Clean up temporary files"""
        if os.path.exists(self.temp_path):
            try:
                # Instead of removing the directory, just clean its contents
                for item in os.listdir(self.temp_path):
                    item_path = os.path.join(self.temp_path, item)
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
                logger.info("Temporary files cleaned up")
            except Exception as e:
                logger.error(f"Error cleaning up temporary files: {e}")
    
    def restart_application(self):
        """Restart the application"""
        try:
            logger.info("Restarting application")
            
            # Create temp directory if it doesn't exist
            os.makedirs(self.temp_path, exist_ok=True)
            
            # Get the command to restart
            if getattr(sys, 'frozen', False):
                # If running as exe, use the executable path
                if platform.system() == "Windows":
                    cmd = [os.path.join(self.all_data_dir, "gui_launcher.exe")]
                else:
                    cmd = [os.path.join(self.all_data_dir, "gui_launcher")]
            else:
                # If running as script, use the Python interpreter
                gui_launcher_path = os.path.join(self.all_data_dir, "gui_launcher.py")
                cmd = [sys.executable, gui_launcher_path]
            
            # Create a restart helper script
            restart_script_path = os.path.join(self.temp_path, "restart.py")
            
            with open(restart_script_path, "w") as f:
                f.write(f"""
import os
import sys
import time
import subprocess

# Wait a moment to ensure files are fully written
time.sleep(1)

# Launch the application
cmd = {repr(cmd)}
print(f"Launching application with command: {{cmd}}")

try:
    subprocess.Popen(cmd)
    print("Application launched successfully")
except Exception as e:
    print(f"Error launching application: {{e}}")
""")
            
            # Launch the restart script
            if platform.system() == "Windows":
                # Use CREATE_NEW_PROCESS_GROUP to detach on Windows
                subprocess.Popen([sys.executable, restart_script_path], 
                              creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            else:
                # Use subprocess.DEVNULL to detach on Unix
                subprocess.Popen([sys.executable, restart_script_path], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL, 
                             stdin=subprocess.DEVNULL,
                             start_new_session=True)
            
            # Exit the current process
            logger.info("New process started, exiting current process")
            os._exit(0)
            
        except Exception as e:
            logger.error(f"Error restarting application: {e}")
            return False
    
    def perform_update(self, create_backup=True, auto_restart=True):
        """Perform the complete update process"""
        # SAFETY: Always create backup regardless of parameter (for safety)
        # If create_backup is True, we'll keep the backup
        # If create_backup is False, we'll delete it after successful update
        backup_path = self.backup_current_version()
        if not backup_path:
            return False, "Failed to create safety backup"
            
        # Check for updates
        update_available, latest_version, download_url = self.check_for_updates()
        
        if not update_available or download_url is None:
            logger.info("No updates available or failed to get update information")
            # Clean up backup if not requested
            if not create_backup and backup_path and os.path.exists(backup_path):
                try:
                    shutil.rmtree(backup_path)
                    logger.info("Cleaned up unnecessary backup")
                except:
                    pass
            return False, "No updates available"
        
        # Download the update
        zip_path = self.download_update(download_url)
        if not zip_path:
            return False, "Failed to download update"
        
        # Apply the update
        if not self.apply_update(zip_path):
            return False, "Failed to apply update"
        
        # Update the version file
        self.update_version_file(latest_version)
        
        # Clean up backup if not requested (but we made one for safety)
        if not create_backup and backup_path and os.path.exists(backup_path):
            try:
                shutil.rmtree(backup_path)
                logger.info("Cleaned up unwanted backup after successful update")
            except:
                pass
                
        # Clean up
        self.clean_temp_files()
        
        # Restart if requested
        if auto_restart:
            self.restart_application()
        
        return True, f"Successfully updated to {latest_version}"
    
    def check_and_update_async(self, callback=None, create_backup=True, auto_restart=True):
        """Check for updates and apply them asynchronously"""
        def update_thread():
            result, message = self.perform_update(create_backup, auto_restart)
            if callback:
                callback(result, message)
        
        thread = threading.Thread(target=update_thread)
        thread.daemon = True
        thread.start()
        return thread

# Helper function to run the updater
def check_for_updates(repo_owner, repo_name, callback=None):
    """
    Check for updates and notify if available
    
    Args:
        repo_owner (str): GitHub repository owner
        repo_name (str): GitHub repository name
        callback (function): Callback function to call with (success, message, is_update_available)
    
    Returns:
        bool: True if update is available, False otherwise
    """
    try:
        updater = Updater(repo_owner, repo_name)
        update_available, version, download_url = updater.check_for_updates()
        
        if update_available:
            message = f"Update available: {version}"
            logger.info(message)
            
            if callback:
                callback(True, message, True)
            return True
        else:
            message = "You have the latest version"
            if callback:
                callback(True, message, False)
            return False
    except Exception as e:
        logger.error(f"Error checking for updates: {e}")
        if callback:
            callback(False, f"Error: {e}", False)
        return False

def auto_update(repo_owner, repo_name, create_backup=True, callback=None):
    """
    Automatically update the application
    
    Args:
        repo_owner (str): GitHub repository owner
        repo_name (str): GitHub repository name
        create_backup (bool): Whether to create a backup before updating
        callback (function): Callback function to call with (success, message)
    
    Returns:
        threading.Thread: The thread performing the update
    """
    try:
        updater = Updater(repo_owner, repo_name)
        return updater.check_and_update_async(callback, create_backup)
    except Exception as e:
        logger.error(f"Error starting auto-update: {e}")
        if callback:
            callback(False, f"Error: {e}")
        return None

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Example usage
    check_for_updates("Kryxzort", "GuiSirSquirrelAssistant")