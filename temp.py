import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional

class USCXMLProcessor:
    """Process US Code XML files and return structured chunks for RAG systems"""
    
    def __init__(self):
        self.namespace = {'ns': 'http://xml.house.gov/schemas/uslm/1.0'}
    
    def extract_text(self, element, with_tags=False) -> str:
        """Extract text from an XML element"""
        if element is None:
            return ""
            
        if with_tags:
            return ET.tostring(element, encoding='unicode', method='xml')
        else:
            text = element.text or ""
            for child in element:
                text += self.extract_text(child, with_tags)
                if child.tail:
                    text += child.tail
            return text.strip()
    
    def process_meta(self, meta_element) -> Dict[str, Any]:
        """Process metadata section"""
        meta = {}
        if meta_element is not None:
            meta['title'] = meta_element.findtext('ns:dc:title', '', self.namespace)
            meta['type'] = meta_element.findtext('ns:dc:type', '', self.namespace)
            meta['doc_number'] = meta_element.findtext('ns:docNumber', '', self.namespace)
            meta['publication_name'] = meta_element.findtext('ns:docPublicationName', '', self.namespace)
            meta['publisher'] = meta_element.findtext('ns:dc:publisher', '', self.namespace)
            meta['created'] = meta_element.findtext('ns:dcterms:created', '', self.namespace)
            meta['creator'] = meta_element.findtext('ns:dc:creator', '', self.namespace)
        return meta
    
    def process_notes(self, notes_element) -> List[Dict[str, Any]]:
        """Process notes section"""
        notes = []
        if notes_element is not None:
            for note in notes_element.findall('ns:note', self.namespace):
                note_data = {
                    'type': note.get('topic', ''),
                    'role': note.get('role', ''),
                    'heading': note.findtext('ns:heading', '', self.namespace),
                    'content': self.extract_text(note.find('ns:p', self.namespace))
                }
                notes.append(note_data)
        return notes
    
    def process_section(self, section_element, chapter_info: Dict[str, Any]) -> Dict[str, Any]:
        """Process an individual legal section"""
        section_id = section_element.get('identifier', '')
        section_num = section_element.findtext('ns:num', '', self.namespace)
        heading = section_element.findtext('ns:heading', '', self.namespace)
        
        content_element = section_element.find('ns:content', self.namespace)
        content = self.extract_text(content_element) if content_element else ""
        
        source_credit = section_element.findtext('ns:sourceCredit', '', self.namespace)
        notes = self.process_notes(section_element.find('ns:notes', self.namespace))
        
        return {
            'id': section_id,
            'type': 'section',
            'title': f"Title {chapter_info['title_number']} §{section_num}",
            'section_number': section_num,
            'heading': heading,
            'content': content,
            'source_credit': source_credit,
            'notes': notes,
            'chapter_number': chapter_info['chapter_number'],
            'chapter_heading': chapter_info['heading'],
            'title_number': chapter_info['title_number']
        }
    
    def process_chapter(self, chapter_element, title_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process a chapter and return all its sections as chunks"""
        chapter_chunks = []
        
        chapter_num = chapter_element.findtext('ns:num', '', self.namespace)
        heading = chapter_element.findtext('ns:heading', '', self.namespace)
        
        chapter_info = {
            'chapter_number': chapter_num,
            'heading': heading,
            'title_number': title_info['number']
        }
        
        # Process all sections in this chapter
        for section in chapter_element.findall('ns:section', self.namespace):
            section_chunk = self.process_section(section, chapter_info)
            chapter_chunks.append(section_chunk)
        
        return chapter_chunks
    
    def process_xml_file(self, xml_file_path: str) -> List[Dict[str, Any]]:
        """
        Main method: Process XML file and return list of chunks
        
        Args:
            xml_file_path (str): Path to the XML file
            
        Returns:
            List[Dict[str, Any]]: List of chunk dictionaries
            
        Raises:
            FileNotFoundError: If XML file doesn't exist
            ET.ParseError: If XML is malformed
            Exception: For other processing errors
        """
        # Parse XML
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        
        chunks = []
        
        # Process metadata
        meta_element = root.find('ns:meta', self.namespace)
        meta = self.process_meta(meta_element)
        
        chunks.append({
            'id': 'metadata',
            'type': 'metadata',
            'content': meta
        })
        
        # Process main content
        main = root.find('ns:main', self.namespace)
        title_element = main.find('ns:title', self.namespace)
        
        if title_element is not None:
            title_num = title_element.findtext('ns:num', '', self.namespace)
            heading = title_element.findtext('ns:heading', '', self.namespace)
            
            title_info = {
                'number': title_num,
                'heading': heading
            }
            
            chunks.append({
                'id': title_element.get('identifier', ''),
                'type': 'title',
                'title': f"Title {title_num}",
                'title_number': title_num,
                'heading': heading,
                'meta': meta
            })
            
            # Process all chapters
            for chapter in main.findall('ns:chapter', self.namespace):
                chapter_chunks = self.process_chapter(chapter, title_info)
                chunks.extend(chapter_chunks)
        
        return chunks

    def get_chunks_by_type(self, chunks: List[Dict[str, Any]], chunk_type: str) -> List[Dict[str, Any]]:
        """Filter chunks by type"""
        return [chunk for chunk in chunks if chunk.get('type') == chunk_type]