"""Environment variable loading utilities."""

import os
import logging
from pathlib import Path
from typing import Dict

logger = logging.getLogger("spade_llm.utils")

def load_env_vars(env_file: str = ".env") -> Dict[str, str]:
    """
    Load environment variables from a .env file.
    
    Args:
        env_file (str): Path to the .env file, relative to project root
        
    Returns:
        Dict[str, str]: Dictionary of environment variables loaded
    """
    # Try to import dotenv, but fall back to manual parsing if not available
    try:
        from dotenv import load_dotenv
        # Try to load from current directory and parent directories
        env_paths = [
            Path(env_file),  # Current directory
            Path.cwd() / env_file,  # Explicit cwd
            Path(__file__).parents[2] / env_file,  # Project root (2 levels up from utils)
        ]
        
        # Try each path
        for env_path in env_paths:
            if env_path.exists():
                load_dotenv(dotenv_path=env_path)
                logger.info(f"Loaded environment variables from {env_path}")
                return {key: value for key, value in os.environ.items() 
                       if key in _get_env_file_variables(env_path)}
    except ImportError:
        logger.warning("python-dotenv not installed, falling back to manual .env parsing")
        # Fall back to manual parsing
        return _manual_load_env(env_file)
    
    logger.warning(f"Could not find .env file in any location. Tried: {env_paths}")
    return {}

def _manual_load_env(env_file: str) -> Dict[str, str]:
    """
    Manually parse a .env file and set environment variables.
    
    Args:
        env_file (str): Path to the .env file
        
    Returns:
        Dict[str, str]: Dictionary of loaded variables
    """
    loaded_vars = {}
    env_paths = [
        Path(env_file),
        Path.cwd() / env_file,
        Path(__file__).parents[2] / env_file,
    ]
    
    for env_path in env_paths:
        if not env_path.exists():
            continue
            
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                    
                os.environ[key] = value
                loaded_vars[key] = value
                
        logger.info(f"Manually loaded environment variables from {env_path}")
        return loaded_vars
        
    logger.warning(f"Could not find .env file in any location.")
    return {}

def _get_env_file_variables(env_path: Path) -> Dict[str, str]:
    """
    Extract variable names from a .env file.
    
    Args:
        env_path (Path): Path to the .env file
        
    Returns:
        Dict[str, str]: Dictionary of variable names to their values
    """
    variables = {}
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            
            # Remove quotes if present
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
                
            variables[key] = value
            
    return variables
