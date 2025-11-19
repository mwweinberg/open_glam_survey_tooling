import secrets
import contentful_management 
import csv


space_ID = secrets.api_test_space_ID
#access_token = secrets.test_env_token
management_api_token = secrets.test_env_token
api_environment_id = secrets.api_env
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
        #print(f'institution_id_list length = {len(institution_id_list)}')

    # #updated version of STEP 1 to deal with contentful pagination
    # limit = 100
    # skip = 0


    # while True:
    #     entries = client.entries(space_ID, api_environment_id).all({
    #         'content_type': 'surveyInstitution',
    #         'limit': limit,
    #         'skip': skip
    #     })

    #     if not entries:
    #         break

    #     for entry in entries:  # entries is iterable directly
    #         institution_id_list.append(entry.sys['id'])  # or entry.id

    #     if len(entries) < limit:
    #         break  # no more pages
        
    #     print(f'downloaded first {skip + 100} institutions')
    #     skip += limit
    
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


build_institution_list()