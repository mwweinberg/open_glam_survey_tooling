import secrets
import requests

#this will hold all of the org-specific dicts
master_org_list = []

#start at 1, stop before 5, just for testing 
#TODO: when you launch this for real, you'll want 1 - 8,000 (or something suitably high), and then a rule along the lines of "if the count is above 5000 and you get an error, exit"
for i in range(1,5):
    #each org gets a dict, which is appended to the master_org_list
    org_dict = {}

    #construct the api query url
    query_url = 'https://api.europeana.eu/entity/organization/' + str(i) + '.json?wskey=' + secrets.europeana_api_key

    print(f'query url = {query_url}')

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
    master_org_list.append(org_dict)
    #print(org_dict)
print(master_org_list)
for i in master_org_list:
    print(i)
    print('***')
