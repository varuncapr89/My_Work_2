import pickle
import os

### Instantiating mbase state dictionary
mbase_state = {}
mbase_state['state'] = {}
mbase_state['state']['prs'] = {}
mbase_state['state']['tags'] = {}
mbase_state['state']['images'] = {}
mbase_state['state']['log'] = {}

## Bob State file ##
bob_state_file_path = "../bob_mbase_state"


## This function saves the state of PR's created by Bob to a file to retrieve it back if it is running again ##
def saveStatePr(list):

    mbase_state['state']['prs']['smtp'] = list[0]
    mbase_state['state']['prs']['s3'] = list[1]
    mbase_state_file = open(f"{bob_state_file_path}", "wb")
    pickle.dump(mbase_state, mbase_state_file)
    mbase_state_file.close()

## This function saves the state of tag's created by Bob to a file to retrieve it back if it is running again ##
def saveStateTag(list):
    mbase_state['state']['tags']['smtp'] = list[0]
    mbase_state['state']['tags']['s3'] = list[1]
    mbase_state_file = open(f"{bob_state_file_path}", "wb")
    pickle.dump(mbase_state, mbase_state_file)
    mbase_state_file.close()

## This function saves the state of image strings created by Bob to a file to retrieve it back if it is running again ## 
def saveStateImages(images):
    mbase_state['state']['images']['smtp'] = images[0]
    mbase_state['state']['images']['s3'] = images[1]
    mbase_state_file = open(f"{bob_state_file_path}", "wb")
    pickle.dump(mbase_state, mbase_state_file)
    mbase_state_file.close()

## This function saves the state of commit string for release fetched by Bob to a file to retrieve it back if it is running again ##
def saveStateReleaseLog(log):
    mbase_state['state']['log']['smtp'] = log[0]
    mbase_state['state']['log']['s3'] = log[1]
    mbase_state_file = open(f"{bob_state_file_path}", "wb")
    pickle.dump(mbase_state, mbase_state_file)
    mbase_state_file.close()

## This function gets the state of tags created by Bob to a file to retrieve it back if it is running again ##
def getStateTag():
    if os.path.exists(f"{bob_state_file_path}"):
        mbase_current_state_file = open(f"{bob_state_file_path}", "rb")
        current_state = pickle.load(mbase_current_state_file)
        return current_state['state']
## This function gets the state of PR's created by Bob to a file to retrieve it back if it is running again ## 
def getStatePr():
    if os.path.exists(f"{bob_state_file_path}"):
        mbase_current_state_file = open(f"{bob_state_file_path}", "rb")
        current_state = pickle.load(mbase_current_state_file)
        return current_state['state']


    


    