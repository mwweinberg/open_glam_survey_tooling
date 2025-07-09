import secrets
import contentful_management 
from bs4 import BeautifulSoup
import requests
import re
import time
import yagmail


space_ID = secrets.api_test_space_ID
#access_token = secrets.test_env_token
management_api_token = secrets.test_env_token
api_environment_id = 'api-test'
#initiate the client
client = contentful_management.Client(management_api_token)



#create a holder for the institution dictionaries 
list_of_institutions_with_fields = []
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

def get_open_data_volume_from_wikidata_url(url_from_field):
    #download the page
    r = requests.get(url_from_field)
    #do beautifulsoup
    soup = BeautifulSoup(r.content, 'lxml')

    #this will work if the page has a big "Statistics XXX files so far!" thing at the top 
    try:
        #find the div with the number
        div = soup.find('div', attrs={'class':'mw-content-ltr mw-parser-output'})
        #find the table in that div
        table = div.find('table', style='vertical-align: middle; background: #fafafa; width: 100%;')
        #find the td in that table, get the text, and strip out any commas
        target_td = table.find('td').text.strip().replace(',', '')
        #return the value 
        return(target_td)
    except:
        #this grabs it from further down below 
        #for example, this page as of 6/1/25 https://commons.wikimedia.org/wiki/Category:Museumsdorf_Cloppenburg
        try:
            #find the div with the number
            div = soup.find('div', attrs={'id':'mw-category-media'}) 
            #pull the full sentence with the number 
            p = div.find('p').text.strip()
            #cuts off the first part of the sentence 
            pattern_1 = r"The following \d+ files are in this category, out of"
            updated_string = re.sub(pattern_1, "", p).strip()
            #cuts off the second part of the sentence 
            pattern_2 = r" total\."
            #and all that is left is the number 
            final_string = re.sub(pattern_2, "", updated_string).strip()
            return(final_string)
        except:
            print(f"Could not get a total from {url_from_field}")
            return("broken")

def get_flickr_upload_count_by_url(url_from_field):

    api_key = secrets.flickr_api_key


    #STEP 1: use url to get flickr ID
    api_url = 'https://www.flickr.com/services/rest/'

    #list of arguments to send to the API
    flickr_url_to_flickr_uid_params = {
        "method":"flickr.urls.lookupUser",
        "api_key":api_key,
        "url": url_from_field,
        "format": "json",
        "nojsoncallback": "1"
    }

    #get API data
    url_to_UID_response = requests.get(api_url, params=flickr_url_to_flickr_uid_params)
    #turn it into json
    url_to_UID_data = url_to_UID_response.json()
    
    #pull out the target UID
    target_UID = url_to_UID_data['user']['id']
    

    #STEP 2: use flickr ID to get the upload count

    try:

        flickr_uid_to_upload_count_params = {
            "method":"flickr.people.getInfo",
            "api_key":api_key,
            "user_id":target_UID,
            "format": "json",
            "nojsoncallback": "1"
        }

        UID_to_count_response = requests.get(api_url, params=flickr_uid_to_upload_count_params)
        UID_to_count_data = UID_to_count_response.json()
        #print(UID_to_count_data)

        #the API returns an int 
        unformatted_volume_int = UID_to_count_data['person']['photos']['count']['_content']
        #this adds commas in the right places (i.e. 5,000)
        formatted_volume_int = "{:,}".format(unformatted_volume_int)
        #turn it into a string and return 
        target_count = str(formatted_volume_int)

    except:
        print(f"Could not get a total from {url_from_field}")
        target_count = "broken"
        

    print(target_count)
    return target_count

def get_open_data_volume_from_europeana_url(url_from_field):
    europeana_api_key = secrets.europeana_api_key
    #some urls  look like:
    #https://www.europeana.eu/search?qf=DATA_PROVIDER%3A%22Museum%20Rotterdam%22&query=&reusability=open
    if 'DATA_PROVIDER' in url_from_field:
        print('DATA_PROVIDER entry')
        extracted_uid_pattern = r'%22(.*?)%22'
        extracted_museum_name = re.search(extracted_uid_pattern, url_from_field).group(1)
        formatted_extracted_museum_name = extracted_museum_name.replace('%20', '+')
        count_query_url = 'https://api.europeana.eu/record/search.json?wskey=' + europeana_api_key + '&sort=score+desc,contentTier+desc,random_europeana+asc,timestamp_update+desc,europeana_id+asc&qf=DATA_PROVIDER:"' + formatted_extracted_museum_name + '"&qf=contentTier:(1+OR+2+OR+3+OR+4)&query=*:*&reusability=open'

        
    #others look like
    #https://www.europeana.eu/en/collections/organisation/4550-national-library-of-finland?page=1&reusability=open
    else:

        #FIRST you need to get the uid from the URL you have and use that to get the second uid from the API
        #if you query the API with the old (long) uid, it will automatically return the entry for the new (short) uid. 
        #this makes extracting both uids slightly more complicated

        #regex to find the uid from the url
        extracted_uid_pattern = r"organisation/(\d+)-"
        #does the regex
        extracted_uid_object = re.search(extracted_uid_pattern, url_from_field)
        #when there is a match, pull the actual number out
        if extracted_uid_object:
            uid_for_api_call = extracted_uid_object.group(1)
            #print(f'uid_for_api_call is {uid_for_api_call}')
        else:
            print(f"unable to extract UID from {url_from_field}")
            return 'broken'

        #construct the API call
        uid_lookup_api_url = 'https://api.europeana.eu/entity/organization/' + uid_for_api_call + '.json?wskey=' + europeana_api_key
        #call the api
        extracted_uid_api_response = requests.get(uid_lookup_api_url)
        #format the data
        extracted_uid_api_reseponse_formatted = extracted_uid_api_response.json()
        #the first extracted uid comes from the 'id' field url
        api_id_field = extracted_uid_api_reseponse_formatted['id']
        extracted_uid_0 = api_id_field.replace('http://data.europeana.eu/organization/', '')
        #api returns a bunch of 'sameAs' links. If there is a second uid, it will be in there
        sameas_links = extracted_uid_api_reseponse_formatted['sameAs']
        #work through the links to find the right one
        found_a_europeana_url = 0
        for i in sameas_links:
            if 'http://data.europeana.eu/organization/' in i:
                #remove the front of the url so you are left with the uid
                extracted_uid_1 = i.replace('http://data.europeana.eu/organization/', '')
                #this prevents this if/else statment from overwriting extracted_uid_1 with "empty" if non-europeana links follow the europeana one in the list
                found_a_europeana_url = 1
            #if the link is not europeana AND the if statement above hasn't already set the value for extracted_uid_1
            elif found_a_europeana_url == 0:
                #set this to empty so it is ignored in step 2
                extracted_uid_1 = "empty"
        #print(f'extracted_uid_0 is {extracted_uid_0}')
        #print(f'extracted_uid_1 is {extracted_uid_1}')

        #SECOND you need to build the one- or two-uid url to make the api call
        
        if extracted_uid_1 == 'empty':
            #construct a 1 uid url
            count_query_url = 'https://api.europeana.eu/record/search.json?wskey=' + europeana_api_key + '&qf=foaf_organization:"http://data.europeana.eu/organization/' + extracted_uid_0 +'"&query=foaf_organization:"http://data.europeana.eu/organization/' + extracted_uid_0 + '"&reusability=open'
            #print(f'one query url: {count_query_url}')
        else:
            #construct a 2 uid url
            count_query_url = 'https://api.europeana.eu/record/search.json?wskey=' + europeana_api_key + '&qf=foaf_organization:"http://data.europeana.eu/organization/' + extracted_uid_0 +'"+OR+foaf_organization:"http://data.europeana.eu/organization/' + extracted_uid_1 +'"&query=foaf_organization:"http://data.europeana.eu/organization/' + extracted_uid_0 + '"+OR+foaf_organization:"http://data.europeana.eu/organization/' + extracted_uid_1 + '"&reusability=open'
            #print(f'two query url: {count_query_url}')
            

    #THIRD, now that you have the target url (from if or else) you need to get the count from the API
    #get the api payload
    object_count_api_response = requests.get(count_query_url)
    #turn it into a json
    extracted_object_count_api_response = object_count_api_response.json()
    #get the count (int)
    unformatted_object_count = extracted_object_count_api_response['totalResults']
    #add the commas
    formatted_volume_count = "{:,}".format(unformatted_object_count)
    #turn it into a string
    target_count = str(formatted_volume_count)

    #print(target_count)
    return target_count

#small function to update the volume data after the platform-specific if/elifs below
#hopefully it reduces the chance of things breaking because you don't have to make changes many different places
def updated_data_report(returned_value, input_url):
    if returned_value == "broken":
        #don't change anything!
        output_open_data_volume = current_open_data_volume
    else:
        #updated value equals the updated value 
        output_open_data_volume = returned_value
        print("updated open data volume from "+input_url)
    return(output_open_data_volume)


build_institution_list()

#now you have a list of all of the institutions with their data platforms 
#go through each data platform to see if there is new data
for i in list_of_institutions_with_fields:
    #this will create a list of just the platforms (may be a list of one)
    this_institutions_data_platforms = i['data_platform']
    #iterate through it to get the info about the individual data platforms
    for e in this_institutions_data_platforms:
        #get the entry 
        entry = client.entries(space_ID, api_environment_id).find(e)
        #get the fields in the entry 
        fields = entry.fields()
        #get the current number of entries as a string to compare to the updated
        current_open_data_volume = str(fields['open_data_volume'])
        #variable for updated number of entries (to be filled by the if statements)
        updated_open_data_volume = ''

        #these if statements invoke platform-specific functions to get updated data
        #wikimedia
        if fields['open_data_platform'] == 'Wikimedia Commons':
            #print('wikimedia volume is ' + fields['open_data_volume'])
            #pass this to the function
            wikimedia_url = fields['open_data_platform_url']
            #get the value 
            wikimedia_value = get_open_data_volume_from_wikidata_url(wikimedia_url)
            #run the update
            updated_open_data_volume = updated_data_report(wikimedia_value, wikimedia_url)
        elif fields['open_data_platform'] == 'Flickr' or fields['open_data_platform'] == 'Flickr Commons':
            flickr_url = fields['open_data_platform_url']
            flickr_value = get_flickr_upload_count_by_url(flickr_url)
            updated_open_data_volume = updated_data_report(flickr_value, flickr_url)
        elif fields['open_data_platform'] == 'Europeana':
            europeana_url = fields['open_data_platform_url']
            europeana_value = get_open_data_volume_from_europeana_url(europeana_url)
            updated_open_data_volume = updated_data_report(europeana_value, europeana_url)
        #TODO: elifs for all of the other platforms - return values as strings with commas 
        #catch-all for everything without a function to update it - don't change anything!
        else:
            updated_open_data_volume = current_open_data_volume
        
        #if the data volume has changed
        if current_open_data_volume != updated_open_data_volume:
            print("DIFFERENCE! Current volume = " + current_open_data_volume + " and updated_data_volume is " + updated_open_data_volume)
            
            #update the data volume 
            entry.fields()['open_data_volume'] = updated_open_data_volume
            # #save the updated entry back to contentful
            entry.save()    
            #publish the updated entry
            #entry.publish()  

            #logging
            log_entry = {'institution_name':i['institution_name'],
                            #'institution_contentful_id':i[institution_contentful_id], 
                            'data_platform': fields['open_data_platform'],
                            'old_value': current_open_data_volume,
                            'new_value': updated_open_data_volume
                            }
            log_contents.append(log_entry)
            #flip the email bit
            send_email = 1
        else:
            print("THE SAME! Current volume = " + current_open_data_volume + " and updated_data_volume is " + updated_open_data_volume)    
        

#write the change log
timestamp = time.strftime('%Y%m%d')
log_file_name = 'logs/'+timestamp+'update_counts.txt'

with open(log_file_name, 'w') as f:
    for line in log_contents:
        f.write(f"{line}\n")

#send the update email if the email bit has been flipped
if send_email == 1:
    # create yagmail instance
    yag = yagmail.SMTP('openglamsurveyrobot@gmail.com', secrets.yagmail_key)
    #add the subject line
    subject = 'Volume count updates for '+timestamp
    #create the empty body string
    body_string = ""
    #fill in the body 
    #if log_contents is empty
    if not log_contents:
        body_string = "no updates today!"
    else: 
        for i in log_contents:
            update = i['institution_name'] + ' volume count was updated from:\n\n' + i['old_value'] +'\n\n' + 'to:\n\n' + i['new_value'] + '\n----------\n\n'
            body_string = update + body_string
    #send the email 
    yag.send(to = send_email_address, subject = subject, contents = body_string)
    print('email sent')
else:
    print("no changes")