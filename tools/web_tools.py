"""
Web tools for Jarvis.

This module provides tools for interacting with the web,
such as searching, retrieving information, and performing web requests.
"""

import os
import sys
import logging
import json
import re
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urlparse, urljoin, quote
from datetime import datetime

try:
    import requests
    from bs4 import BeautifulSoup
    WEB_TOOLS_AVAILABLE = True
except ImportError:
    WEB_TOOLS_AVAILABLE = False

from jarvis.brain.langchain_service import langchain_service
from jarvis.config import settings

# Configure logging
logger = logging.getLogger(__name__)

def get_webpage(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 10) -> Dict[str, Any]:
    """Get the content of a webpage.
    
    Args:
        url: URL of the webpage to retrieve
        headers: Optional request headers
        timeout: Request timeout in seconds
        
    Returns:
        dict: Result containing webpage content
    """
    if not WEB_TOOLS_AVAILABLE:
        return {
            "status": "error", 
            "message": "Web tools dependencies not available. Install requests and beautifulsoup4."
        }
    
    try:
        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            return {
                "status": "error",
                "message": f"Invalid URL: {url}"
            }
            
        # Set default headers if none provided
        if headers is None:
            headers = {
                "User-Agent": "Jarvis Assistant/1.0"
            }
        
        # Make the request
        response = requests.get(url, headers=headers, timeout=timeout)
        
        # Check if request was successful
        if response.status_code != 200:
            return {
                "status": "error",
                "message": f"Request failed with status code {response.status_code}",
                "data": {
                    "status_code": response.status_code,
                    "reason": response.reason
                }
            }
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract page information
        title = soup.title.text.strip() if soup.title else "No title found"
        
        # Extract main content (try different strategies)
        main_content = ""
        
        # Try article or main content
        content_elements = soup.find_all(['article', 'main', 'div'], class_=lambda c: c and any(x in c.lower() for x in ['content', 'article', 'main', 'body']))
        if content_elements:
            main_content = "\n".join([elem.get_text(strip=True, separator=" ") for elem in content_elements])
        
        # If no main content found, use the body
        if not main_content and soup.body:
            main_content = soup.body.get_text(strip=True, separator=" ")
        
        # If still no content, use the entire HTML
        if not main_content:
            main_content = soup.get_text(strip=True, separator=" ")
        
        # Extract links
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Skip empty or javascript links
            if not href or href.startswith('javascript:'):
                continue
                
            # Convert relative URLs to absolute
            if not urlparse(href).netloc:
                href = urljoin(url, href)
            
            links.append({
                "text": link.get_text(strip=True) or "[No text]",
                "url": href
            })
        
        # Limit to top 20 links
        links = links[:20]
        
        # Clean up content (remove excessive whitespace)
        main_content = re.sub(r'\s+', ' ', main_content).strip()
        
        # Truncate content if too long
        if len(main_content) > 5000:
            main_content = main_content[:5000] + "..."
        
        return {
            "status": "success",
            "message": f"Retrieved webpage: {title}",
            "data": {
                "url": url,
                "title": title,
                "content": main_content,
                "links": links,
                "content_length": len(main_content),
                "link_count": len(links)
            }
        }
        
    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "message": f"Request timed out after {timeout} seconds"
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Error retrieving webpage '{url}': {str(e)}")
        return {
            "status": "error",
            "message": f"Error retrieving webpage: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Error processing webpage '{url}': {str(e)}")
        return {
            "status": "error",
            "message": f"Error processing webpage: {str(e)}"
        }

def search_duckduckgo(query: str, num_results: int = 5) -> Dict[str, Any]:
    """Search the web using DuckDuckGo.
    
    Args:
        query: Search query
        num_results: Number of results to return (default: 5)
        
    Returns:
        dict: Search results
    """
    if not WEB_TOOLS_AVAILABLE:
        return {
            "status": "error", 
            "message": "Web tools dependencies not available. Install requests and beautifulsoup4."
        }
    
    try:
        # Encode the query
        encoded_query = quote(query)
        
        # Create the search URL
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        
        # Set headers to avoid being blocked
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # Make the request
        response = requests.get(url, headers=headers, timeout=15)
        
        # Check if request was successful
        if response.status_code != 200:
            return {
                "status": "error",
                "message": f"Search request failed with status code {response.status_code}"
            }
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract search results
        results = []
        result_elements = soup.select('.result')
        
        for element in result_elements[:num_results]:
            # Extract title
            title_element = element.select_one('.result__title')
            title = title_element.get_text(strip=True) if title_element else "No title found"
            
            # Extract URL
            link_element = element.select_one('.result__url')
            link = link_element.get_text(strip=True) if link_element else None
            
            # Extract description
            description_element = element.select_one('.result__snippet')
            description = description_element.get_text(strip=True) if description_element else "No description found"
            
            results.append({
                "title": title,
                "url": link,
                "description": description
            })
        
        return {
            "status": "success",
            "message": f"Found {len(results)} results for '{query}'",
            "data": results
        }
        
    except Exception as e:
        logger.error(f"Error searching DuckDuckGo for '{query}': {str(e)}")
        return {
            "status": "error",
            "message": f"Error performing search: {str(e)}"
        }

def get_weather(location: str) -> Dict[str, Any]:
    """Get current weather information for a location.
    
    Args:
        location: City or location to get weather for
        
    Returns:
        dict: Weather information
    """
    if not WEB_TOOLS_AVAILABLE:
        return {
            "status": "error", 
            "message": "Web tools dependencies not available. Install requests and beautifulsoup4."
        }
    
    try:
        # Create the search URL for weather
        encoded_location = quote(f"weather {location}")
        url = f"https://html.duckduckgo.com/html/?q={encoded_location}"
        
        # Set headers to avoid being blocked
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # Make the request
        response = requests.get(url, headers=headers, timeout=15)
        
        # Check if request was successful
        if response.status_code != 200:
            return {
                "status": "error",
                "message": f"Weather request failed with status code {response.status_code}"
            }
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for weather information
        weather_info = {}
        
        # Try to find the weather module
        weather_module = soup.select_one('.module--weather')
        
        if weather_module:
            # Extract location
            location_element = weather_module.select_one('.module__title')
            weather_info["location"] = location_element.get_text(strip=True) if location_element else "Unknown"
            
            # Extract temperature
            temp_element = weather_module.select_one('.module__temperature')
            weather_info["temperature"] = temp_element.get_text(strip=True) if temp_element else "Unknown"
            
            # Extract conditions
            conditions_element = weather_module.select_one('.module__details')
            weather_info["conditions"] = conditions_element.get_text(strip=True) if conditions_element else "Unknown"
            
            return {
                "status": "success",
                "message": f"Found weather information for {weather_info.get('location', location)}",
                "data": weather_info
            }
        else:
            return {
                "status": "error",
                "message": f"Could not find weather information for '{location}'"
            }
        
    except Exception as e:
        logger.error(f"Error getting weather for '{location}': {str(e)}")
        return {
            "status": "error",
            "message": f"Error retrieving weather information: {str(e)}"
        }

def register_web_tools() -> bool:
    """Register all web tools with the LangChain service.
    
    Returns:
        bool: True if all tools were registered successfully
    """
    if not WEB_TOOLS_AVAILABLE:
        logger.warning("Web tools dependencies not available. Install requests and beautifulsoup4.")
        return False
    
    if not langchain_service.active:
        logger.error("Cannot register web tools: LangChain service not active")
        return False
    
    try:
        # Register each tool
        langchain_service.register_tool(
            name="get_webpage",
            func=get_webpage,
            description="Get the content of a webpage from a URL"
        )
        
        langchain_service.register_tool(
            name="search_web",
            func=search_duckduckgo,
            description="Search the web for information using DuckDuckGo"
        )
        
        langchain_service.register_tool(
            name="get_weather",
            func=get_weather,
            description="Get current weather information for a location"
        )
        
        logger.info("Web tools registered successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error registering web tools: {str(e)}")
        return False 