'''
from typing import Dict, List, Any
import re

class QueryProcessor:
    def __init__(self):
        self.action_keywords = {
            'show': 'retrieve',
            'display': 'retrieve',
            'find': 'retrieve',
            'get': 'retrieve',
            'search': 'retrieve',
            'list': 'retrieve'
        }
        
        self.document_types = {
            'resume': 'resume',
            'cv': 'resume',
            'document': 'document',
            'file': 'document',
            'report': 'document'
        }

    def process_query(self, query: str) -> Dict[str, Any]:
        """Process natural language query and extract structured information"""
        query = query.lower().strip()
        result = {
            'original_query': query,
            'action': None,
            'document_type': None,
            'target': None,
            'search_terms': [],
            'is_list_all': False
        }

        # Detect action
        for keyword, action in self.action_keywords.items():
            if keyword in query:
                result['action'] = action
                break

        # Check for "all documents" type queries
        if any(phrase in query for phrase in [
            "all documents", 
            "available documents", 
            "documents available", 
            "show documents",
            "list documents"
        ]):
            result['is_list_all'] = True
            result['document_type'] = 'document'
            return result

        # Detect document type
        for keyword, doc_type in self.document_types.items():
            if keyword in query:
                result['document_type'] = doc_type
                break

        # Extract potential names (assuming they're capitalized in the original query)
        original_words = query.split()
        potential_names = []
        
        # If looking for a resume, try to extract name
        if result['document_type'] == 'resume':
            # Look for patterns like "show mayuresh khot resume"
            name_pattern = r'(?:show|find|get|display)\s+([a-z]+(?:\s+[a-z]+)?)\s+resume'
            name_match = re.search(name_pattern, query)
            if name_match:
                potential_names = name_match.group(1).split()
                result['target'] = ' '.join(potential_names)
                result['search_terms'].extend(potential_names)
                result['search_terms'].append('resume')

        # Add any remaining relevant terms
        for word in query.split():
            if (len(word) > 2 and 
                word not in self.action_keywords and 
                word not in self.document_types and
                word not in result['search_terms']):
                result['search_terms'].append(word)

        return result

    def generate_search_query(self, processed_query: Dict[str, Any]) -> str:
        """Generate optimized search query from processed information"""
        if processed_query['is_list_all']:
            return "document content"

        search_terms = []
        
        # Add target (e.g., name) if present
        if processed_query['target']:
            search_terms.append(processed_query['target'])
        
        # Add document type if present
        if processed_query['document_type']:
            search_terms.append(processed_query['document_type'])
        
        # Add remaining search terms
        search_terms.extend([term for term in processed_query['search_terms'] 
                           if term not in ' '.join(search_terms)])
        
        return ' '.join(search_terms)
'''
