import os
from time import sleep
from bob.pro_helper import helpers
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from termcolor import colored
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys



# Dictionary for Jenkins Build Urls 
# key - name of jenkins project 
# value - url of jenkins project
Build_Git_Repo_Urls = {
    "smtp_repo": "https://github.medallia.com/govcloud/smtp/releases/new",
    "s3_repo": "https://github.medallia.com/medallia/s3-reverse-proxy/releases/new",
    "smtp": "https://jenkins.eng.medallia.com/controller2/job/govcloud/job/govcloud-org/job/smtp/job/master/",
    "s3-reverse-proxy": "https://jenkins.eng.medallia.com/controller3/job/medallia/job/medallia-org/job/s3-reverse-proxy/job/master/",
    "govcloudpush": "https://jenkins.eng.medallia.com/controller2/job/govcloud/job/GovCloudPush/build?delay=0sec",
    }

def build_push(images, tags, release):
    #Generating User credentials and storing for future use
    
    #Some variables needed for the script 
    smtp_release_log = release[0]
    s3_release_log = release[1]
    smtp_tag = tags[0]
    s3_tag = tags[1]

    c = helpers.getUserCreds()
    username = c["username"]
    password = c["password"]
    
    #Selenium chrome webdriver settings
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(options=chrome_options)
    driver.delete_all_cookies()

    
    #Opening smtp jenkins build url
    driver.get(Build_Git_Repo_Urls["smtp_repo"])
    sleep(3)
    
    #Sending the Okta Email and Password and selecting the push notification verfication button. 
    okta = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input#input28")))
    okta.send_keys(str(username))
    oktaPass = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input#input36.password-with-toggle")))
    oktaPass.send_keys(str(password))
    sleep(2)
    oktaSignin = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input.button.button-primary")))
    oktaSignin.click()
    oktaVerify = WebDriverWait(driver, 3).until(EC.presence_of_all_elements_located((By.XPATH, '//*[contains(text(), "Select")]')))
    oktaVerify[2].click()
    sleep(10)


    ####Publish new release in SMTP####
    ## Click tag dropdown, select the right tag for the release
    tag = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div#tag-list.position-relative.d-inline-block.mr-md-1.mb-1")))
    tag.click()
    sleep(2)
    tagInputBox = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input.SelectMenu-input.form-control")))
    tagInputBox.send_keys(smtp_tag)
    tagInputBox.send_keys(Keys.ENTER)
    sleep(2)

    ## Get the release title box && Description box and send release version && body
    releaseMsg = "{release_notes} Update base image for SMTP {t}".format(t=smtp_tag, release_notes=smtp_release_log)
    releaseTitle = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input#release_name.form-control.flex-auto.mr-0")))
    releaseTitle.send_keys(smtp_tag)
    releaseBody = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.ID, "release_body")))
    releaseBody.send_keys(releaseMsg)
    sleep(2)

    ## Get the publish release button and click on to make a new release 
    publish = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn.btn-primary.js-publish-release")))
    publish.click()
    sleep(2)

    ####Publish new release for s3-reverse-proxy#### 
    
    driver.execute_script("window.open('about:blank', 'secondtab');")
    driver.switch_to.window("secondtab")
    driver.get(Build_Git_Repo_Urls["s3_repo"])
    sleep(3)
    ## Click tag dropdown, select the right tag for the release
    tag = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div#tag-list.position-relative.d-inline-block.mr-md-1.mb-1")))
    tag.click()
    sleep(2) 
    tagInputBox = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input.SelectMenu-input.form-control")))
    tagInputBox.send_keys(s3_tag)
    tagInputBox.send_keys(Keys.ENTER)
    sleep(2)
    
    ## Get the release title box && Description box and send release version && body
    releaseMsg = "{release_notes} Update base image for S3-reverse-proxy".format(t=s3_tag, release_notes=s3_release_log)
    releaseTitle = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input#release_name.form-control.flex-auto.mr-0")))
    releaseTitle.send_keys(s3_tag)
    releaseBody = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.ID, "release_body")))
    releaseBody.send_keys(releaseMsg)
    sleep(4)

    ## Get the publish release button and click on to make a new release
    publish = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn.btn-primary.js-publish-release")))
    publish.click()
    
    sleep(4)
    driver.execute_script("window.open('about:blank', 'thirdtab');")
    driver.switch_to.window("thirdtab")
    driver.get(Build_Git_Repo_Urls["smtp"])
    #Selecting the Build Now button
    s=driver.find_element(By.XPATH, "//a[@title='Build Now']")
    s.click()
    #Waiting for one second 
    sleep(3)

    #Opening up the second tab in same browser
    driver.execute_script("window.open('about:blank', 'fourthtab');")

    #Switching to second tab and opening up s3-reverse-proxy 
    driver.switch_to.window("fourthtab")
    driver.get(Build_Git_Repo_Urls["s3-reverse-proxy"])
    #Waitng for s3-reverse-proxy build page to load
    sleep(5)
    #Selecting the rever 
    r=driver.find_element(By.XPATH, "//a[@title='Build Now']")

    #Clicking on build now button
    r.click()
    sleep(4)

    ###Going to GOVCLOUD PUSH to push images ####
    driver.execute_script("window.open('about:blank', 'fifthtab');")
    driver.switch_to.window("fifthtab")
    sleep(2)
    driver.get(Build_Git_Repo_Urls["govcloudpush"])
    print(colored("Waiting for 10 Minutes for SMTP && S3 build to finish before pushing images to ECR", "yellow"))
    sleep(10)

    #Getting Docker Image text box in GOVCLOUD build page and sending the images to it.
    imageBox = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".setting-input")))
    imageBox.send_keys(images)
    buildButton = WebDriverWait(driver, 40).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button#yui-gen1-button")))
    sleep(5)
    image_msg = "If everything looks good, type 'c' and hit ENTER to push the images into ECR"
    helpers.waitForUser(image_msg)
    buildButton.click()
    sleep(5)
    driver.close()