import secrets
import contentful_management 
import time 




space_ID = secrets.api_test_space_ID
#access_token = secrets.test_env_token
management_api_token = secrets.test_env_token
api_environment_id = secrets.api_env
#initiate the client
client = contentful_management.Client(management_api_token)

#******global things 
#create a holder for the institution dictionaries 
list_of_institutions_with_fields = []
#variable to hold the log file
log_contents = []


def build_institution_list():

    #STEP 0: create a holder for the institution IDs
    institution_id_list = []



    #updated version of STEP 1 to deal with contentful pagination
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



build_institution_list()

#for all of the institutions in the institution list  
for i in list_of_institutions_with_fields:

    #if the admission_policy entry is none
    if i.get('admission_policy') == 'None':
        #if i.get('institution_name') == 'Blue Mountains Library (Local Studies)':
        print(i.get('institution_name'))
        print(i.get('admission_policy'))
        print('*******')

        #get the contentful ID
        institution_contentful_id = i['institution_contentful_id']


        #get the entry you may modify 
        entry = client.entries(space_ID, api_environment_id).find(institution_contentful_id)

        #update it (None instead of just '' because just '' threw an error)
        entry.fields()['admission_policy'] = "N/A"
        #save the updated entry back to contentful
        #entry.save()    
        #publish the updated entry
        #entry.publish()            
        #append it to the log
        updated_institution_name = entry.fields()['institution_name']
        log_entry = {'institution_name':updated_institution_name,
                    'institution_contentful_id':institution_contentful_id
                    }
        log_contents.append(log_entry)



#write the change log
timestamp = time.strftime('%Y%m%d')
log_file_name = 'logs/'+timestamp+'none_purge.txt'

with open(log_file_name, 'w') as f:
    for line in log_contents:
        f.write(f"{line}\n")