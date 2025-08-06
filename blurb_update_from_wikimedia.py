import secrets
import contentful_management 

import requests
import re

import time 

import yagmail


space_ID = secrets.api_test_space_ID
#access_token = secrets.test_env_token
management_api_token = secrets.test_env_token
api_environment_id = secrets.api_env
#initiate the client
client = contentful_management.Client(management_api_token)

#******global things 
#create a holder for the institution dictionaries 
list_of_institutions_with_fields = []
#variable to decide how long the blurbs will be (in characters)
target_blurb_length = 500
#variable to hold the log file
log_contents = []
#send email bit
send_email = 0
#log email addresses
send_email_address = ["mweinberg@nyu.edu", "hello@michaelweinberg.org"]

def build_institution_list():

    #STEP 0: create a holder for the institution IDs
    institution_id_list = []

    #STEP 1: get all of the 'surveyInstitution' entries 
    #returns some sort of object of the entries
    # entries_just_institutions = client.entries(space_ID, api_environment_id).all({'content_type': 'surveyInstitution'})
    # #append all of the object ids to institution_id_list
    # for i in entries_just_institutions:
    #     #extract the institution ID
    #     entry_id = i.id
    #     #add the institution id to the list
    #     institution_id_list.append(entry_id)
    #     #print for testing/debugging 
    #     # print(entry_id)
    #     #print(f'institution_id_list length = {len(institution_id_list)}')

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

def get_blurb_from_wikidata_link(wikidata_url):

    #*****extract wikidata ID from the full url
    #regex the number
    match = re.search(r"Q\d+", wikidata_url)
    #error message 
    if not match:
        #raise ValueError("Invalid Wikidata URL or ID not found.")
        print(f'invalid wikidata url or ID for {wikidata_url}')
        return ''
    else: 
        #assign first (and only) match to variable wiki_id
        wiki_id = match.group(0)

        #******get the title from wikidata to use for the wikipedia API
        #construct URL for wikidata api endpoint 
        wikidata_api_url = (f'https://www.wikidata.org/w/api.php?action=wbgetentities&ids={wiki_id}&format=json&props=sitelinks')
        #get the data from wikidata
        wikidata_response = requests.get(wikidata_api_url)
        #error handling
        if wikidata_response.status_code != 200:
            print(f"Failed to fetch data from wikidata API for {wiki_id}")
            return('')
        #format response into json 
        wikidata_data = wikidata_response.json()
        try:
            #parse for links
            sitelinks = wikidata_data['entities'][wiki_id]['sitelinks']
            #error handling
            if 'enwiki' not in sitelinks:
                #raise Exception(f"English Wikipedia link not found for {wiki_id}")
                print(f"English Wikipedia link not found for wiki_id {wiki_id}")
                return('')
            #get the institutional title as used in english wikipedia 
            wikipedia_title = sitelinks['enwiki']['title']
        except:
            print(f'line 138 error with wikidata for {wikidata_data}')
            return('')

        #*****get the extract
        #construct the URL
        wikipedia_api_url = (
                f"https://en.wikipedia.org/w/api.php?action=query&format=json&prop=extracts"
                f"&titles={wikipedia_title}&formatversion=2"
                f"&exchars={target_blurb_length}&explaintext=0"
            )
        #get data payload
        wikipedia_response = requests.get(wikipedia_api_url)
        #error handling
        if wikipedia_response.status_code != 200:
            #raise Exception(f"Failed to fetch data from Wikipedia API at {wikidata_api_url}")
            print(f"Failed to fetch data from Wikipedia API at {wikidata_api_url}")
            return('')
        #parse response
        try:
            wikipedia_data = wikipedia_response.json()
            inst_blurb = wikipedia_data['query']['pages'][0].get('extract', "No extract available")
            #cuts off the blurb right before the start of the first header
            cleaned_up_blurb = re.split(r"\n\s*==\s*.*?\s*==", inst_blurb, maxsplit=1)[0].strip()
        except:
            print(f("no blurb for wiki_id {wiki_id}"))
            return('')

        #print(inst_blurb)
        return(cleaned_up_blurb)

build_institution_list()

#run the institution list through the blurb-getter & update blurbs 
for i in list_of_institutions_with_fields:

    #if the entry has a value for the wikidata url
    #if i['institution_wikidata']:
    if i.get('institution_wikidata'):
        #get the blurb
        new_institution_blurb = get_blurb_from_wikidata_link(i['institution_wikidata'])
        #get the relevant contentful ID 
        institution_contentful_id = i['institution_contentful_id']


        #get the entry you may modify 
        entry = client.entries(space_ID, api_environment_id).find(institution_contentful_id)
        #if the `institution_description` does not exist
        if 'institution_description' not in entry.fields():
                #create it 
                entry.fields()['institution_description'] = {}
                #update it 
                entry.fields()['institution_description'] = new_institution_blurb
                # #save the updated entry back to contentful
                entry.save()
                #publish the updated entry
                entry.publish()
                #append it to the log
                updated_institution_name = entry.fields()['institution_name']
                log_entry = {'institution_name':updated_institution_name,
                            'institution_contentful_id':institution_contentful_id, 
                            'old_blurb' : '',
                            #'old_blurb': current_institution_blurb,
                            'new_blurb': new_institution_blurb
                            }
                log_contents.append(log_entry)
        #if the `institution_description` do not exist
        else:
            #get the current version of the blurb
            current_institution_blurb = entry.fields()['institution_description']
            #if the blurb has changed
            if current_institution_blurb != new_institution_blurb:
                #update it 
                entry.fields()['institution_description'] = new_institution_blurb
                # #save the updated entry back to contentful
                entry.save()    
                #publish the updated entry
                entry.publish()            
                #append it to the log
                updated_institution_name = entry.fields()['institution_name']
                log_entry = {'institution_name':updated_institution_name,
                            'institution_contentful_id':institution_contentful_id, 
                            'old_blurb': current_institution_blurb,
                            'new_blurb': new_institution_blurb
                            }
                log_contents.append(log_entry)
                #set the send email bit
                send_email = 1

        #be nice to the API
        time.sleep(.1)
    else:
        print('no value for the wikidata url')

#write the change log
timestamp = time.strftime('%Y%m%d')
log_file_name = 'logs/'+timestamp+'blurb_update.txt'

with open(log_file_name, 'w') as f:
    for line in log_contents:
        f.write(f"{line}\n")

#send the update email if the email bit has been flipped
if send_email == 1:
    # create yagmail instance
    yag = yagmail.SMTP('certification@oshwa.org', secrets.yagmail_key)
    #add the subject line
    subject = 'OGS blurb updates for '+timestamp
    #create the empty body string
    body_string = ""
    #fill in the body 
    #if log_contents is empty
    if not log_contents:
        body_string = "no updates today!"
    else: 
        for i in log_contents:
            update = i['institution_name'] + ' blurb was updated from:\n\n' + i['old_blurb'] +'\n\n' + 'to:\n\n' + i['new_blurb'] + '\n----------\n\n'
            body_string = update + body_string
    #send the email 
    yag.send(to = send_email_address, subject = subject, contents = body_string)
    print('email sent')
else:
    print("no changes")