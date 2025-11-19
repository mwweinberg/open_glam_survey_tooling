import secrets
import contentful_management 
import csv
import time


space_ID = secrets.api_test_space_ID
#access_token = secrets.test_env_token
management_api_token = secrets.test_env_token
api_environment_id = secrets.api_env
#initiate the client
client = contentful_management.Client(management_api_token)

strange_error_log = []

#******global things 
#create a holder for the institution dictionaries 
list_of_institutions_with_fields = []

def build_institution_list():

    #STEP 0: create a holder for the institution IDs
    institution_id_list = []

    #STEP 1: get all of the 'surveyInstitution' entries 

    ######UNCOMMENT THIS TO JUST PULL 100 ENTRIES
    #returns some sort of object of the entries
    entries_just_institutions = client.entries(space_ID, api_environment_id).all({'content_type': 'surveyInstitution'})
    #append all of the object ids to institution_id_list
    # change [:n] to limit to a smaller sample
    for i in entries_just_institutions[:10]:
        #extract the institution ID
        entry_id = i.id
        #add the institution id to the list
        institution_id_list.append(entry_id)

            #print for testing/debugging 
            # print(entry_id)
            #print(f'institution_id_list length = {len(institution_id_list)}')
    ######END UNCOMMENT THIS JUST TO PULL 100 ENTRIES SECTION

    #updated version of STEP 1 to deal with contentful pagination
    ####START NORMAL STEP 1 SECTION
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
    #####END NORMAL STEP 1 SECTION
    
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
            print('')
        # print(list_of_data_platforms)
    print("completed build_institution_list")


build_institution_list()



#now you have a list of all of the institutions with their data platforms 
#and add them
getting_platforms_data_counter = 1
for i in list_of_institutions_with_fields:
    try:
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
            print('&&&&&&')
            #print(fields)
            #print('&&&&&&')
            #constructs the open_data_volume_name and _number so that it can iterate
            open_data_volume_name = 'open_data_volume_name'+str(platform_counter)
            open_data_volume_number = 'open_data_volume_number'+str(platform_counter)
            open_data_volume_url = 'open_data_volume_url'+str(platform_counter)
            open_data_volume_rs = 'open_data_volume_rs'+str(platform_counter)

            #####START RIGHT STATEMENT INFO SECTION

            # #get the rights_statement info for the platform (may be more than one)
            right_statement_counter = 0
            #the objects in this list have a bunch of metadata (<Link[Entry] id='28kfRD9rU7AL3IhXjd4I05'>)
            this_platform_rights_statements = fields['rights_statements']
            #so you need to iterate through them and just pull the relevant ids
            this_platform_rights_statements_ids = []
            for q in this_platform_rights_statements:
                this_platform_rights_statements_ids.append(q.id)

            # print('*****')
            # print(this_platform_rights_statements_ids)
            # print('****')
            platform_rs_list = []
            for h in this_platform_rights_statements_ids:
                rs_entry = client.entries(space_ID, api_environment_id).find(h)
                rs_fields = rs_entry.fields()
                rs_identity = rs_fields['title']
                platform_rs_list.append(rs_identity)
                # print('*****')
                # print(rs_identity)
                # print('*****')
                # rs_name = 'rs_name'+str(right_statement_counter)
                # platform_rs_dict.update({rs_name:rs_identity})
            # for h in this_platform_rights_statements:
            #     rs_entry = client.entries(space_ID, api_environment_id).find(h)
            #     rs_fields = rs_entry.fields()
            #     print('*****')
            #     print(rs_fields)
            #     print('*****')

            ######END RIGHT STATEMENT INFO SECTION


            #creates a dictionary to add to the i entry 
            platform_count_dict = {open_data_volume_name: fields['open_data_platform'], open_data_volume_number: fields['open_data_volume'], open_data_volume_url: fields['open_data_platform_url'], open_data_volume_rs:platform_rs_list}
            #puts the whole platform_count_dict at the end of the existing i entry 
            i.update(platform_count_dict)
            #iterates the platform_counter
            platform_counter += 1
            #print(platform_count_dict)
            #print('^^^^^^^')
            print(f'getting data platforms for institution number {getting_platforms_data_counter}')
            getting_platforms_data_counter += 1
    except Exception as e:
        print(f"(line 96) no data platform for {i}")
        print('')
print('added data platforms')


#this is where you clean up the data with small tweaks
for i in list_of_institutions_with_fields:
    #the 'pretty_url' field is just the stub. This step adds the full url
    updated_pretty_url = 'https://survey.glamelab.org/institutions/'+ i['pretty_url']
    i['pretty_url'] = updated_pretty_url

    #if the first_open_access_instance date is empty it defaults to 1/1/70. That is read as "null" when the site is being built. This changes the output to match that. 
    if i.get('first_open_access_instance') == '1970-01-01T00:00:00.000Z':
        i['first_open_access_instance'] = 'null'
    

    ###create the open_data_volume_total column
    #small function to convert open_data_volume_numbers into ints, returning log if something is really strange 
    def safe_int(value):
        """Convert to int, returning 0 if not possible"""
        if value is None:
            return 0
        try:
            return int(str(value).replace(',', ''))
        except ValueError:
            print(f"*****ERROR {i}")
            strange_error_log.append(i)
            return 0       
    #the ,'0' syntax in get() makes 0 the default value if open_data_volume_numberX does not exist
    # and the '.replace(',', '')' clears out any lingering commas in the values 
    total_number = safe_int(i.get('open_data_volume_number0')) + safe_int(i.get('open_data_volume_number1')) + safe_int(i.get('open_data_volume_number2'))
    i['open_data_volume_total'] = total_number
    print(f"total number: {total_number}")

    ###some first_open_access_instance fields are blank, some are YYYY, and some are YYYY-MM-DD
    ###this section normalizes all YYYY-MM-DD to just YYYY
    #pull the entry for first_open_access_instance using .get so things won't crash if there is no value
    first_open_access_instance_holder = i.get('first_open_access_instance')
    #if it exists (some of them are empty, so this checks that) AND the length of it = 10 (the number of characters in the YYYY-MM-DD format)
    if first_open_access_instance_holder and len(first_open_access_instance_holder) == 10:
        #then replace the value with the first four characters, which should be YYYY
        i['first_open_access_instance'] = first_open_access_instance_holder[:4]
        






#every key in the dict must be in this list, but having a key in this list without a corresponding value in an item is not a problem
#that's why you have a bunch of 'open_data_volume_XY' entries at the end
fieldnames = ['institution_name', 'institution_name_english', 'pretty_url', 'country', 'part_of', 'institution_type', 'institution_website', 'institution_wikidata', 'first_open_access_instance', 'first_open_access_instance_citation', 'open_access_scope', 'open_access_policy', 'tk_tce_policy', 'rights_statement_compliance', 'rights_statement_metadata', 'rights_statement_metadata_url', 'admission_policy', 'institution_api', 'institution_github', 'open_data_volume_total',  'open_data_volume_name0', 'open_data_volume_number0', 'open_data_volume_url0', 'open_data_volume_rs0', 'open_data_volume_name1', 'open_data_volume_number1', 'open_data_volume_url1', 'open_data_volume_rs1','open_data_volume_name2', 'open_data_volume_number2', 'open_data_volume_url2', 'open_data_volume_rs2', 'open_data_volume_name3', 'open_data_volume_number3', 'open_data_volume_url3', 'open_data_volume_rs3', 'open_data_volume_name4', 'open_data_volume_number4', 'open_data_volume_url4', 'open_data_volume_rs4', 'open_data_volume_name5', 'open_data_volume_number5', 'open_data_volume_url5', 'open_data_volume_rs5']

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

#this is a log of any institutions that have non-number values in their open data counts
timestamp = time.strftime('%Y%m%d')
error_log_file_name = 'logs/'+timestamp+'contentful2csv.txt'
with open(error_log_file_name, 'w') as f:
    for line in strange_error_log:
        f.write(f"{line}\n")
        f.write('***\n')
