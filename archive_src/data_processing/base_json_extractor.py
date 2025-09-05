import json

class USJSONProcessor:
    def __init__(self):
        pass
        
    def process_json_file(self,json_path:str):
        """
        Main method: This is the main file that process an XML file
        """
        results = {
            'file_name':json_path.name,
            'success':False,
            'chunks':[],
            'error':None,
            'title_number':None,
            'title_heading':None
        }

        with open(json_path,'r') as f:
            data = json.load(f)

        uscdoc = data.get('uscDoc',{})
        #get meta information
        meta = uscdoc.get('meta',{})
        
        main_level = None
        bad_files = []
        #get title information
        if 'main' in uscdoc:
            main = uscdoc.get('main',{})
            title = main.get('title',{})
            title_num = title.get('num',{}).strip()
            title_heading = title.get('heading',{}).strip()

            if 'chapter' in title:
                chapters = title.get('chapter',{})
                results['success'] = True
                results['chunks'] = chapters
                results['title_number'] = title_num
                results['title_heading'] = title_heading
            else:
                results['error'] = 'Does not have chapter as direct child'
        else:
            results['error'] = 'Does not have main as direct child'
            
        
        return results
