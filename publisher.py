"""
Publisher component for the Obsidian News Digest application.
Writes the formatted digest to an Obsidian vault.
"""
import os
from typing import Optional


def publish_to_obsidian(content: str, vault_path: str, output_folder: str, filename: str) -> str:
    """
    Publish the formatted digest to Obsidian vault.
    
    Args:
        content: Formatted markdown content
        vault_path: Path to the Obsidian vault
        output_folder: Folder within the vault to save the digest
        filename: Filename for the digest
        
    Returns:
        Path to the created file
    """
    # Create path to the output folder in the vault
    folder_path = os.path.join(vault_path, output_folder)
    
    # Create folder if it doesn't exist
    os.makedirs(folder_path, exist_ok=True)
    
    # Create file path
    file_path = os.path.join(folder_path, filename)
    
    # Write content to file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    return file_path