import secrets
import contentful_management 
import csv


space_ID = secrets.api_test_space_ID
#access_token = secrets.test_env_token
management_api_token = secrets.test_env_token
api_environment_id = 'api-test'
#initiate the client
client = contentful_management.Client(management_api_token)


#******global things 
#create a holder for the institution dictionaries 
list_of_institutions_with_fields = []

def build_institution_list():

    #STEP 0: create a holder for the institution IDs
    institution_id_list = []

    #STEP 1: get all of the 'surveyInstitution' entries 
    #returns some sort of object of the entries
    entries_just_institutions = client.entries(space_ID, api_environment_id).all({'content_type': 'surveyInstitution'})
    #append all of the object ids to institution_id_list
    for i in entries_just_institutions:
        #extract the institution ID
        entry_id = i.id
        #add the institution id to the list
        institution_id_list.append(entry_id)
        #print for testing/debugging 
        # print(entry_id)
    
    #STEP 2: add institutions (with fields) to list_of_institution_with_fields
    for i in institution_id_list:
        #get the entry
        entry = client.entries(space_ID, api_environment_id).find(i)
        #pull out the fields
        fields = entry.fields()
        #add the contentful id of the entry
        fields['institution_contentful_id'] = i
        #append to list_of_institutions_with_fields
        list_of_institutions_with_fields.append(fields)

    #STEP 3 update list_of_institutions_with_fields to include uid for data platform entries 
    for i in list_of_institutions_with_fields:
        #this is going to be how you extract the list of data platform references 
        #create a temporary list to hold all of the ids
        list_of_data_platforms = []
        for e in i['data_platform']:
            #add each platform id to the temporary list
            list_of_data_platforms.append(e.id)
        #replace existing data_platform entry with the list because that will be easier to work with
        i['data_platform'] = list_of_data_platforms
        # print(list_of_data_platforms)
    print("completed build_institution_list")


build_institution_list()



#now you have a list of all of the institutions with their data platforms 
#and add them
for i in list_of_institutions_with_fields:
    #this will create a list of just the platforms (may be a list of one)
    this_institutions_data_platforms = i['data_platform']
    #counter to keep track of how many platforms 
    platform_counter = 0
    #iterate through it to get the info about the individual data platforms
    for e in this_institutions_data_platforms:
        #get the entry 
        entry = client.entries(space_ID, api_environment_id).find(e)
        #get the fields in the entry 
        fields = entry.fields()
        #print(fields)
        #print('&&&&&&')
        #constructs the open_data_volume_name and _number so that it can iterate
        open_data_volume_name = 'open_data_volume_name'+str(platform_counter)
        open_data_volume_number = 'open_data_volume_number'+str(platform_counter)
        open_data_volume_url = 'open_data_volume_url'+str(platform_counter)
        #creates a dictionary to add to the i entry 
        platform_count_dict = {open_data_volume_name: fields['open_data_platform'], open_data_volume_number: fields['open_data_volume'], open_data_volume_url: fields['open_data_platform_url']}
        #puts the whole platform_count_dict at the end of the existing i entry 
        i.update(platform_count_dict)
        #iterates the platform_counter
        platform_counter += 1
        #print(platform_count_dict)
        #print('^^^^^^^')
print('added data platforms')


#this is where you clean up the data with small tweaks
for i in list_of_institutions_with_fields:
    #the 'pretty_url' field is just the stub. This step adds the full url
    updated_pretty_url = 'https://survey.glamelab.org/institutions/'+ i['pretty_url']
    i['pretty_url'] = updated_pretty_url

    #if the first_open_access_instance date is empty it defaults to 1/1/70. That is read as "null" when the site is being built. This changes the output to match that. 
    if i['first_open_access_instance'] == '1970-01-01T00:00:00.000Z':
        i['first_open_access_instance'] = 'null'






#every key in the dict must be in this list, but having a key in this list without a corresponding value in an item is not a problem
#that's why you have a bunch of 'open_data_volume_XY' entries at the end
fieldnames = ['institution_name', 'institution_name_english', 'pretty_url', 'country', 'part_of', 'institution_type', 'institution_website', 'institution_wikidata', 'first_open_access_instance', 'first_open_access_instance_citation', 'open_access_scope', 'open_access_policy', 'tk_tce_policy', 'rights_statement_compliance', 'rights_statement_metadata', 'rights_statement_metadata_url', 'admission_policy', 'institution_api', 'institution_github',  'open_data_volume_name0', 'open_data_volume_number0', 'open_data_volume_url0','open_data_volume_name1', 'open_data_volume_number1', 'open_data_volume_url1','open_data_volume_name2', 'open_data_volume_number2', 'open_data_volume_url2', 'open_data_volume_name3', 'open_data_volume_number3', 'open_data_volume_url3', 'open_data_volume_name4', 'open_data_volume_number4', 'open_data_volume_url4', 'open_data_volume_name5', 'open_data_volume_number5', 'open_data_volume_url5']

#these are the fieldnames that exist in the dictionary but will be skipped.
#this works because the instantiation of DictWriter below uses the `extrasaction='ignore'` argument, which means that when it finds a key not in the fieldnames list it just skips it (default behavior is to stop and raise an issue)
#you are just keeping them in case you need to restore them in the future for some reason
#['institution_contentful_id','data_platform','institution_description',]

#name of output file 
with open('contentful2csv.csv', 'w') as csv_file:
    #imports the fieldnames from above
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames, extrasaction='ignore')
    #writes the header row based on the fieldnames 
    writer.writeheader()
    #writes one row per institution blob
    writer.writerows(list_of_institutions_with_fields)

print('.csv complete')