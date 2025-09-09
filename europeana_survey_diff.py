import secrets
import requests

#this will hold all of the org-specific dicts in europeana
europeana_master_org_list = []

#UNCOMMENT THIS WHEN YOU ARE RUNNING IT FOR REAL
#create a holder for the institution dictionaries (from contentful)
#list_of_institutions_with_fields = []

#THIS IS JUST FOR TESTING SO YOU DON'T NEED TO BUILD THE FULL INSTITUTION LIST
list_of_institutions_with_fields = [{'institution_name': 'Muzeum Afrykanistyczne Olkusz', 'institution_name_english': 'The Gotland Museum', 'pretty_url': 'muzeum-afrykanistyczne-olkusz', 'country': 'Poland', 'part_of': '', 'institution_type': 'Museum', 'institution_website': 'https://www.mok.olkusz.pl/index.php/muzea/29-muzeum-afrykanistyczne', 'institution_wikidata': 'https://www.wikidata.org/wiki/Q11786895', 'institution_description': 'INSTITUTIONAL DESCRIPTION IS HERE', 'first_open_access_instance': '2021', 'first_open_access_instance_citation': 'https://web.archive.org/web/2021*/https://sketchfab.com/blogs/community/1000-new-cultural-heritage-3d-models-dedicated-to-the-public-domain/', 'open_access_scope': 'Some eligible data', 'open_access_policy': '', 'tk_tce_policy': '', 'rights_statement_compliance': 'Public domain', 'rights_statement_metadata': 'None', 'rights_statement_metadata_url': '', 'admission_policy': 'Information needed', 'institution_api': '', 'institution_github': '', 'data_platform': '6spyF0PHMC2z04QZmBekH6'},{'institution_name': 'Hallwylska museet', 'institution_name_english': 'Hallwyl Museum', 'pretty_url': 'hallwylska-museet', 'country': 'Sweden', 'part_of': '', 'institution_type': 'Museum', 'institution_website': 'https://hallwylskamuseet.se', 'institution_wikidata': 'https://www.wikidata.org/wiki/Q4346239', 'institution_description': 'Hallwyl Museum (Swedish: Hallwylska museet) is a Swedish national museum housed in the historical Hallwyl House in central Stockholm located on 4, Hamngatan facing Berzelii Park. The house once belonged to the Count and Countess von Hallwyl, but was donated to the Swedish state in 1920 to eventually become a museum. In 1938, the museum was officially opened.', 'first_open_access_instance': '2012', 'first_open_access_instance_citation': 'https://web.archive.org/web/20210101000000*/https://pro.europeana.eu/files/Europeana_Professional/Publications/Making%20Impact%20on%20a%20Small%20Budget%20-%20LSH%20Case%20Study.pdf', 'open_access_scope': 'Some eligible data', 'open_access_policy': '', 'tk_tce_policy': '', 'rights_statement_compliance': 'Public domain', 'rights_statement_metadata': 'None', 'rights_statement_metadata_url': '', 'admission_policy': 'Free', 'institution_api': '', 'institution_github': 'https://github.com/lshSWE', 'data_platform': ['2s4mxAQXQg1ESxDC1c46HE', '4cAlwcLcFVDhQ1701I6gWI'], 'institution_contentful_id': '8db7f3f4d738486aa69993e6dc91d25c'}]

def build_institution_list():

    #STEP 0: create a holder for the institution IDs
    institution_id_list = []

    #STEP 1: get all of the 'surveyInstitution' entries 

    #variables for dealing with contentful pagination 
    limit = 100
    skip = 0

    while True:
        entries = client.entries(space_ID, api_environment_id).all({
            'content_type': 'surveyInstitution',
            'limit': limit,
            'skip': skip
        })

        if not entries:
            break

        for entry in entries:  # entries is iterable directly
            institution_id_list.append(entry.sys['id'])  # or entry.id

        if len(entries) < limit:
            break  # no more pages
        
        print(f'downloaded first {skip + 100} institutions')
        skip += limit
    
    #STEP 2: add institutions (with fields) to list_of_institution_with_fields
    getting_institution_data_counter = 1
    for i in institution_id_list:
        #get the entry
        entry = client.entries(space_ID, api_environment_id).find(i)
        #pull out the fields
        fields = entry.fields()
        #add the contentful id of the entry
        fields['institution_contentful_id'] = i
        #append to list_of_institutions_with_fields
        list_of_institutions_with_fields.append(fields)
        print(f'getting data for institution number {getting_institution_data_counter}')
        getting_institution_data_counter += 1

    #STEP 3 update list_of_institutions_with_fields to include uid for data platform entries 
    for i in list_of_institutions_with_fields:
        #this is going to be how you extract the list of data platform references 
        #create a temporary list to hold all of the ids
        list_of_data_platforms = []
        try:
            for e in i['data_platform']:
                #add each platform id to the temporary list
                list_of_data_platforms.append(e.id)
            #replace existing data_platform entry with the list because that will be easier to work with
            i['data_platform'] = list_of_data_platforms
        except:
            print(f"(line 58) no platform for {i}")
        # print(list_of_data_platforms)
    print("completed build_institution_list")

def fill_europeana_master_org_list():
    #start at 1, stop before 5, just for testing 
    #TODO: when you launch this for real, you'll want 1 - 8,000 (or something suitably high), and then a rule along the lines of "if the count is above 5000 and you get an error, exit"
    for i in range(1,5):
        #each org gets a dict, which is appended to the master_org_list
        org_dict = {}

        #construct the api query url
        query_url = 'https://api.europeana.eu/entity/organization/' + str(i) + '.json?wskey=' + secrets.europeana_api_key

        #print(f'query url = {query_url}')

        #call the api
        api_response = requests.get(query_url)
        #format the data
        api_response_formatted = api_response.json()

        #this is to keep track of the id number used to get the org
        org_dict['id_number'] = i

        #'id' in the response is the full url to the org
        id_url = api_response_formatted['id']
        org_dict['id_url'] = id_url

        #print(f'ID is {api_response_formatted['id']}')

        #europeana supports institution names in multiple languages - they are in prefLabel
        #so first, get the dictionary of the names/languages
        name_dict = api_response_formatted['prefLabel']
        #get all of the keys (language identifiers)
        name_dict_keys = list(name_dict.keys())
        #create a list for all of the non-english names 
        non_en_name_list = []
        for i in name_dict_keys:
            #identify the en name specifically because contentful has a en name field
            if i == 'en':
                #add it to the org_dict
                org_dict['englishName'] = api_response_formatted['prefLabel'][i]
            #add everything else to a non-en list that you will end up iterating through 
            else:
                non_en_name_list.append(api_response_formatted['prefLabel'][i])
        #now that the loop is done, you can add all of the non_en_name_list to org_dict
        org_dict['otherName'] = non_en_name_list

        #add the completed org dict to the master_org_list
        europeana_master_org_list.append(org_dict)
        #print(org_dict)

en_name_contentful = []
name_contentful = []

def get_just_the_names_from_contentful():
    for i in list_of_institutions_with_fields:
        name_contentful.append(i['institution_name'])
        en_name_contentful.append(i['institution_name_english'])


#TODO: list_matching will return a match. The next step is to have it add matches to a new list (as a log) and delete them from the europeana_master_org_list. Then, once that is done, you turn europeana_master_org_list into the list of institutions that someone needs to check out (export as a text file? send an email? who knows?).  It works because all of the lists that are already in contentful have been deleted

def list_matching():
    #for each entry in the europeana_master_org_list
    for i in europeana_master_org_list:
        #otherName is a list because there can be many, so you need to iterate through it
        for e in i['otherName']:
            #if the entry is in name_contentful
            if e in name_contentful:
                print('non-en match!')
        #if the europeana en name matches an en_name_contentful
        if i['englishName'] in en_name_contentful:
             print('en match!')
        
        


fill_europeana_master_org_list()

print(europeana_master_org_list)

get_just_the_names_from_contentful()

#print(name_contentful)
#print(en_name_contentful)

list_matching()

# print(europeana_master_org_list)
# for i in europeana_master_org_list:
#     print(i)
#     print('***')
