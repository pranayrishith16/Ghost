import json

class USJSONProcessor:
    def __init__(self):
        pass
        
    def process_json_file(self,json_path:str):
        """
        Main method: This is the main file that process an XML file
        """
        chunks = []

        with open(json_path,'r') as f:
            data = json.load(f)

        uscdoc = data.get('uscDoc',{})
        #get meta information
        meta = uscdoc.get('meta',{})
        
        main_level = None

        #get title information
        if 'main' in uscdoc:
            main = uscdoc.get('main',{})
            title = main.get('title',{})
            title_num = title.get('num',{})
            title_heading = title.get('heading',{})
            print(title_num,title_heading)


        elif 'appendix' in uscdoc:
            appendix = uscdoc.get('appendix',{})
            appendix_num = appendix.get('num',{})
            appendix_heading = appendix.get('heading',{})
            print(appendix_num,appendix_heading)
        