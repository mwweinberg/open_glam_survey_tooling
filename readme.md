This repo has tools for updating entries in the [Open GLAM Survey](https://survey.glamelab.org/).  The scripts require a secrets.py file that is not included in the repo.


**blurb_update_from_wikimedia.py** is the script to update the institution blurbs from wikimedia.  It uses the english language wikimedia entry for the institution and captures either the first 500 characters or everything before the first heading, whichever is shorter.  

**update_counts.py** is the script to update volume counts from an ever-expanding(?) number of platforms. The initial commit included functions to update the counts from wikimedia and flickr.  

**contentful2csv.py** is the script to output all of contentful into a csv. That csv is 'contentful2csv.csv' and will be saved in the same directory. 

**europeana_survey_diff.py** is to check which institutions are in europeana but not in the survey 

**conup_** is the prefix for a bunch of one-off(ish) scripts to update data in contentful (keeping them in the main directory avoids having to reproduce secrets.py in subfolders)

- *date_fix.py* is a script to fix the "first open access instance citation" field, which had some bad data at one point.  This script can probably also be modified to mass update anything on an institution page. 

- *none_purge.py* changed add of the admission_policy "None" values to "N/A 