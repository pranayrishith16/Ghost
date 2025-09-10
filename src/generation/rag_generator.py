import logging
import time
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.interfaces.retriever_interface import RetrieverInterface
from src.interfaces.llm_provider_interface import LLMProviderInterface
from config.settings import get_config

class RAGGenerator:
    """Legal RAG generator that combines retrieved context with LLM for answers"""
    
    def __init__(self, retriever: RetrieverInterface, llm_provider: LLMProviderInterface):
        self.config = get_config()
        self.retriever = retriever
        self.llm_provider = llm_provider
        self.logger = logging.getLogger(__name__)
        
        # Load prompt templates
        self.prompt_templates = self._load_prompt_templates()
        
        # Generation statistics
        self.stats = {
            'total_queries': 0,
            'avg_generation_time': 0.0,
            'total_context_tokens': 0,
            'avg_response_length': 0.0
        }
        
    def generate_response(self, query: str, query_type: str = "legal_analysis", 
                         k: int = 10, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate a legal response using RAG
        
        Args:
            query: The legal question/query
            query_type: Type of query ("legal_analysis", "case_summary", "precedent_search")
            k: Number of documents to retrieve
            filters: Optional metadata filters for retrieval
            
        Returns:
            Dict containing response, sources, metadata
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Generating response for query: {query[:100]}...")
            
            # Step 1: Retrieve relevant documents
            retrieved_docs = self.retriever.retrieve(query, k=k, filters=filters)
            print(retrieved_docs)
            
            if not retrieved_docs:
                return self._handle_no_results(query)
            
            # Step 2: Process and rank retrieved documents
            processed_context = self._process_retrieved_docs(retrieved_docs, query)
            
            # Step 3: Build prompt with context
            prompt = self._build_prompt(query, processed_context, query_type)
            
            # Step 4: Generate response using LLM
            response = self._generate_with_llm(prompt, query_type)
            
            # Step 5: Post-process response
            final_response = self._post_process_response(response, processed_context, query)
            
            # Step 6: Update statistics
            generation_time = time.time() - start_time
            self._update_stats(generation_time, len(processed_context), len(final_response['answer']))
            
            self.logger.info(f"Generated response in {generation_time:.3f}s using {len(processed_context)} sources")
            
            return final_response
            
        except Exception as e:
            self.logger.error(f"Generation failed for query '{query[:50]}...': {str(e)}")
            raise Exception(f"Response generation failed: {str(e)}")
    
    def _process_retrieved_docs(self, docs: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Process and enhance retrieved documents"""
        processed_docs = []
        
        for i, doc in enumerate(docs):
            processed_doc = {
                'rank': i + 1,
                'text': doc.get('text', ''),
                'metadata': doc.get('metadata', {}),
                'score': doc.get('similarity_score', 0.0),
                'chunk_id': doc.get('chunk_id', ''),
                'legal_context': doc.get('legal_context', {}),
                'query_relevance': self._assess_query_relevance(doc.get('text', ''), query)
            }
            
            # Add citation information
            processed_doc['citation_info'] = self._extract_citation_info(processed_doc)
            
            processed_docs.append(processed_doc)
        
        return processed_docs
    
    def _build_prompt(self, query: str, context_docs: List[Dict[str, Any]], query_type: str) -> str:
        """Build the prompt for the LLM with context"""
        
        # Get the appropriate template
        template = self.prompt_templates.get(query_type, self.prompt_templates['legal_analysis'])
        
        # Build context section
        context_sections = []
        for doc in context_docs[:self._get_max_context_docs()]:
            context_section = f"[Source {doc['rank']}]\n"
            context_section += f"Document: {doc['metadata'].get('filename', 'Unknown')}\n"
            
            # Add legal metadata if available
            legal_ctx = doc.get('legal_context', {})
            if legal_ctx.get('case_number'):
                context_section += f"Case: {legal_ctx.get('case_number')}\n"
            if legal_ctx.get('court'):
                context_section += f"Court: {legal_ctx.get('court')}\n"
                
            context_section += f"Content: {doc['text']}\n"
            context_sections.append(context_section)
        
        context_text = "\n---\n".join(context_sections)
        
        # Fill in the template
        prompt = template.format(
            query=query,
            context=context_text,
            current_date=time.strftime("%Y-%m-%d")
        )
        
        return prompt
    
    def _generate_with_llm(self, prompt: str, query_type: str) -> str:
        """Generate response using the LLM provider"""
        
        # Check token limits
        estimated_tokens = self.llm_provider.estimate_tokens(prompt)
        max_context = self.config.llm.max_context_length
        
        if estimated_tokens > max_context:
            self.logger.warning(f"Prompt too long ({estimated_tokens} tokens), truncating...")
            prompt = self._truncate_prompt(prompt, max_context)
        
        # Generate response
        response = self.llm_provider.generate_with_context(
            question=prompt.split("Query: ")[-1].split("\n")[0],  # Extract just the query
            context=[prompt],  # Full prompt as context
            max_tokens=self.config.llm.max_tokens
        )
        
        # Validate response
        if not self.llm_provider.validate_response(response):
            raise Exception("Generated response failed validation")
            
        return response
    
    def _post_process_response(self, response: str, context_docs: List[Dict[str, Any]], 
                              query: str) -> Dict[str, Any]:
        """Post-process the generated response"""
        
        # Clean up the response
        cleaned_response = self._clean_response(response)
        
        # Add citations if enabled
        if self.config.llm.enable_citations:
            response_with_citations = self._add_citations(cleaned_response, context_docs)
        else:
            response_with_citations = cleaned_response
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence(cleaned_response, context_docs, query)
        
        # Build final response
        final_response = {
            'answer': response_with_citations,
            'confidence_score': confidence_score,
            'sources': self._format_sources(context_docs),
            'metadata': {
                'query_type': self._detect_query_type(query),
                'sources_count': len(context_docs),
                'legal_areas': self._extract_legal_areas_from_context(context_docs),
                'timestamp': time.time(),
                'model_used': self.llm_provider.get_model_info().get('model_name', 'unknown')
            }
        }
        
        return final_response
    
    def _load_prompt_templates(self) -> Dict[str, str]:
        """Load prompt templates from files"""
        templates = {}
        template_dir = Path(__file__).parent / "prompt_templates"
        
        template_files = {
            'legal_analysis': 'legal_analysis.txt',
            'case_summary': 'case_summary.txt', 
        }
        
        for template_name, filename in template_files.items():
            template_path = template_dir / filename
            if template_path.exists():
                try:
                    with open(template_path, 'r', encoding='utf-8') as f:
                        templates[template_name] = f.read().strip()
                    self.logger.info(f"Loaded template: {template_name}")
                except Exception as e:
                    self.logger.error(f"Failed to load template {filename}: {str(e)}")
                    templates[template_name] = self._get_fallback_template(template_name)
            else:
                self.logger.warning(f"Template file not found: {filename}, using fallback")
                templates[template_name] = self._get_fallback_template(template_name)
        
        return templates
    
    def _get_fallback_template(self, template_name: str) -> str:
        """Get fallback template if file loading fails"""
        return """You are a legal research assistant. Analyze the following query using the provided legal context.

Query: {query}

Legal Context:
{context}

Instructions:
1. Provide a comprehensive legal analysis based on the provided context
2. Cite relevant sources using [Source X] format
3. Structure your response with clear legal reasoning
4. If context is insufficient, state what additional information would be needed

Analysis:"""
    
    # Helper methods
    def _assess_query_relevance(self, text: str, query: str) -> float:
        """Assess how relevant a text is to the query"""
        query_words = set(query.lower().split())
        text_words = set(text.lower().split())
        
        if not query_words:
            return 0.0
            
        overlap = len(query_words.intersection(text_words))
        return overlap / len(query_words)
    
    def _get_max_context_docs(self) -> int:
        """Get maximum number of context documents to use"""
        return min(10, self.config.llm.max_context_length // 200)  # Rough estimate
    
    def _truncate_prompt(self, prompt: str, max_tokens: int) -> str:
        """Truncate prompt to fit within token limits"""
        estimated_chars_per_token = 4
        max_chars = max_tokens * estimated_chars_per_token * 0.8  # Safety margin
        
        if len(prompt) <= max_chars:
            return prompt
            
        return prompt[:max_chars] + "\n...[Prompt truncated]"
    
    def _clean_response(self, response: str) -> str:
        """Clean and normalize the generated response"""
        response = response.strip()
        
        # Remove common LLM artifacts
        artifacts_to_remove = [
            "I'll analyze", "Let me analyze", "Based on the provided context"
        ]
        
        for artifact in artifacts_to_remove:
            if response.startswith(artifact):
                first_sentence_end = response.find('.', len(artifact))
                if first_sentence_end != -1:
                    response = response[first_sentence_end + 1:].strip()
                    
        return response
    
    def _add_citations(self, response: str, context_docs: List[Dict[str, Any]]) -> str:
        """Add proper legal citations to the response"""
        # Simple citation addition - add citations to legal statements
        sentences = response.split('. ')
        cited_response = []
        
        for sentence in sentences:
            if sentence.strip():
                # Add citation to sentences that reference legal concepts
                if any(keyword in sentence.lower() for keyword in 
                      ['court held', 'ruling', 'decision', 'precedent', 'holding']):
                    # Find most relevant source
                    best_source = max(context_docs, key=lambda x: x.get('score', 0)) if context_docs else None
                    if best_source:
                        citation = f"[Source {best_source['rank']}]"
                        sentence = f"{sentence} {citation}"
                
                cited_response.append(sentence)
        
        return '. '.join(cited_response)
    
    def _calculate_confidence(self, response: str, context_docs: List[Dict[str, Any]], query: str) -> float:
        """Calculate confidence score for the response"""
        confidence = 0.5  # Base confidence
        
        # Factor in number and quality of sources
        if len(context_docs) >= 3:
            confidence += 0.2
        elif len(context_docs) >= 1:
            confidence += 0.1
            
        # Factor in average source relevance
        if context_docs:
            avg_score = sum(doc.get('score', 0) for doc in context_docs) / len(context_docs)
            confidence += min(avg_score * 0.3, 0.2)
        
        # Factor in response length (substantial responses)
        if len(response.split()) > 50:
            confidence += 0.1
            
        return min(confidence, 1.0)
    
    def _format_sources(self, context_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format sources for the final response"""
        formatted_sources = []
        
        for doc in context_docs:
            metadata = doc.get('metadata', {})
            
            source = {
                'rank': doc['rank'],
                'filename': metadata.get('filename', 'Unknown'),
                'relevance_score': doc.get('score', 0.0),
                'excerpt': doc['text'][:200] + "..." if len(doc['text']) > 200 else doc['text']
            }
            
            # Add legal metadata if available
            legal_ctx = doc.get('legal_context', {})
            if legal_ctx.get('case_number'):
                source['case_number'] = legal_ctx.get('case_number')
            if legal_ctx.get('court'):
                source['court'] = legal_ctx.get('court')
                
            formatted_sources.append(source)
            
        return formatted_sources
    
    def _detect_query_type(self, query: str) -> str:
        """Detect the type of legal query"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['summarize', 'summary', 'overview']):
            return 'case_summary'
        elif any(word in query_lower for word in ['precedent', 'similar case', 'case law']):
            return 'precedent_search'
        else:
            return 'legal_analysis'
    
    def _extract_legal_areas_from_context(self, context_docs: List[Dict[str, Any]]) -> List[str]:
        """Extract legal areas mentioned in the context"""
        all_areas = set()
        for doc in context_docs:
            legal_areas = doc.get('legal_context', {}).get('legal_areas', [])
            if isinstance(legal_areas, list):
                all_areas.update(legal_areas)
        return list(all_areas)
    
    def _extract_citation_info(self, doc: Dict[str, Any]) -> Dict[str, str]:
        """Extract citation information from a document"""
        legal_ctx = doc.get('legal_context', {})
        metadata = doc.get('metadata', {})
        
        return {
            'case_number': legal_ctx.get('case_number', 'N/A'),
            'court': legal_ctx.get('court', 'N/A'),
            'document_type': legal_ctx.get('document_type', 'N/A'),
            'filename': metadata.get('filename', 'N/A')
        }
    
    def _handle_no_results(self, query: str) -> Dict[str, Any]:
        """Handle case when no documents are retrieved"""
        return {
            'answer': f"I couldn't find any relevant legal documents for your query: '{query}'. "
                     f"Please try rephrasing your question or using different legal terminology.",
            'confidence_score': 0.0,
            'sources': [],
            'metadata': {
                'query_type': self._detect_query_type(query),
                'sources_count': 0,
                'legal_areas': [],
                'timestamp': time.time(),
                'model_used': self.llm_provider.get_model_info().get('model_name', 'unknown'),
                'status': 'no_results'
            }
        }
    
    def _update_stats(self, generation_time: float, context_count: int, response_length: int):
        """Update generation statistics"""
        self.stats['total_queries'] += 1
        self.stats['total_context_tokens'] += context_count
        
        # Update averages
        total_time = self.stats['avg_generation_time'] * (self.stats['total_queries'] - 1)
        self.stats['avg_generation_time'] = (total_time + generation_time) / self.stats['total_queries']
        
        total_length = self.stats['avg_response_length'] * (self.stats['total_queries'] - 1)
        self.stats['avg_response_length'] = (total_length + response_length) / self.stats['total_queries']
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """Get generation performance statistics"""
        return {
            **self.stats,
            'retriever_stats': self.retriever.get_retrieval_stats(),
            'llm_model': self.llm_provider.get_model_info()
        }
