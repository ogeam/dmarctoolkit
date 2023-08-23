import  parsedmarc
import  checkdmarc
import  collections
import  os
import  traceback

class DmarcReport():

    def __init__(self,props):

        self.report_type       = props['report_type'] if 'report_type' in props  else None
        self.xml_schema        = props['xml_schema'] if 'xml_schema' in props  else None
        self.report_metadata   = props['report_metadata'] if 'report_metadata' in props  else None
        self.policy_published  = props['policy_published'] if 'policy_published' in props  else None
        self.records           = props['records'] if 'records' in props  else None
        self.file_path         = props['file_path']   if 'file_path' in props  else None
        self.file_path         = props if type(props)!= dict else self.file_path 
        self.raw_data          = None
        try:
            if os.path.exists(self.file_path):
                self.parse_report_file()
                self.init_data(self.raw_data)
        except:
            traceback.print_exc()

    def get_metadata(self, metadata,prefix='report_metadata'):
  
         metadata_obj = {}
         for index in metadata:
            metadata_obj[prefix+'_'+index]=metadata[index]
         return metadata_obj

    def  init_data(self,data):
        self.report_type       = data['report_type']
        self.xml_schema        = data['report']['xml_schema']
        self.report_metadata   = self.get_metadata(data['report']['report_metadata'])
        self.policy_published  = self.get_metadata(data['report']['policy_published'], 'policy_published')
        self.records           = self.get_report_fields(data['report']['records'])

    def get_object_map(self, obj_var):
        report_map   = {}
        if type(obj_var) is dict or type(obj_var) ==collections.OrderedDict:
            for k,v in obj_var.items():
                if type (v) is dict or type(v) ==collections.OrderedDict:
                    for prop,val in v.items():
                       if type (val) is dict or type(val) ==collections.OrderedDict or type(val) is list:
                         value = []
                         if type(val) is list:
                             for item in val:
                                 for m,n in item.items():
                                     temp ={}
                                     temp[prop+'-'+m]=n   
                                     value.append(temp)
                         elif type(val) is dict or type(val) ==collections.OrderedDict:
                             value ={}
                             for k,l in val.items():
                                 value[prop+'-'+k]=l       
                         else:
                           value =val      
                         report_map.update(self.get_object_map(value))
                       else:
                         report_map[k+'-'+prop] = val
                else: 
                    report_map[k] = v
        elif type(obj_var) is list:
           for element in obj_var:
              if type(element) is dict or type(element) ==collections.OrderedDict:
                  report_map.update(self.get_object_map(element))
              else:
                 report_map[element] = obj_var[element]       
        return report_map

    def get_report_fields(self,report_data):
        report_fields = []
        for record in report_data:
            report_fields.append(self.get_object_map(record))
        return report_fields

    def print(self,data=None):
        obj_var = data if data else self.raw_data
        if type(obj_var) is dict or type(obj_var) ==collections.OrderedDict:
            for k,v in obj_var.items():
                print(f'{k}: {v}')
                if type (v) is dict  or type(v) ==collections.OrderedDict:
                    for k,v in v.items():
                        print(f'{k}: {v}')
        elif type(obj_var) is list:
            for element in obj_var:
                print(element)
                if type (element) is dict or type(element) is list or type(element) ==collections.OrderedDict:
                    self.print(element)
        else:
            print(obj_var)


    def parse_report_file(self):
        report_data   = parsedmarc.parse_report_file(self.file_path)
        self.raw_data = report_data
    #report_columns =  list(report_data.keys())
    #print(report_columns)  = ['report_type', 'report']
    #print("report type: "+str( type(report_data)))
    #console_log(report_data)
    """
    report_type  = report_data['report_type']
    data         = report_data['report']
    xml_schema   = data['xml_schema']
    metadata     = data['report_metadata']
    records      = data['records']
    for record in records:
       for k,v in record.items():
          print(f'{k}: {v}')
    """
 
def get_dmarc_for_domain(domain):
    results = checkdmarc.get_dmarc_record(domain)
    #console_log(results)
    
    """
    for k in results:
        print(k)
  
    print("checking dmarc info for "+domain)
    record        =  results['record']
    location      =  results['location']
    parsed_result =  results['parsed']
    for k,v in parsed_result['tags'].items():
        print(f'{k}: {v}')
    for k in parsed_result['warnings']:
        print(k)
    """