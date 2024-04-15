import time
import datetime
import re
from bs4 import BeautifulSoup as bs
from icecream import ic
import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options #firefox/chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import csv
import logging
from dotenv import load_dotenv

list_jobs_external = []

keywords_to_count = ["SQL, Excel, Python, R, Tableau, Power BI, machine learning, AI, database, business, statistics, statistical analysis, big data, VBA, AWS, GO"]
keywords_to_count_lower = [word.lower() for word in keywords_to_count]
counts_list = np.zeros(len(keywords_to_count_lower))


ic("Starting...")
def create_logfile():
    date_time = datetime.datetime.today().strftime("%d-%b-%y_%H:%M:%S")
    logfile = f"log/{date_time}.log"
    logging.basicConfig(filename=logfile, filemode='w', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', force=True)

    logging.info(f'Log file {logfile} created')
    print(f"*********Logfile created************")
    return logging


def create_file(file):
    # delete existing file if re-running
    logging.info("Checking if current daily csv exists...")
    if os.path.exists(file):
        os.remove(file)
        logging.info(f"{file} deleted")
    else:
        logging.info(f"{file} ain't exist")

    # create file and add header
    logging.info("Creating daily csv file...")
    header = ['date_time', 'search_keyword', 'search_count', 'job_id', 'job_title', 'company', 'location', 'remote',
              'update_time', 'applicants', 'job_pay', 'job_time', 'job_position', 'company_size', 'company_industry',
              'job_details']
    with open(file, 'w') as f:
        w = csv.writer(f)
        w.writerow(header)
        logging.info(f"{file} created")


def login(logging):
    url_login = "https://www.linkedin.com/"

    # pulls login information from file called '.env'
    # this file added to .gitignore so login details not shared
    load_dotenv()
    # .env file is of structure:
    # LINKEDIN_USERNAME=email@gmail.com
    # LINKEDIN_PASSWORD=password
    print("getting usrname&pswd")
    LINKEDIN_USERNAME = os.getenv('LINKEDIN_USERNAME')
    LINKEDIN_PASSWORD = os.getenv('LINKEDIN_PASSWORD')
    print("done")

    # setup chrome to run headless
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")

    # login to LinkedIn
    logging.info(f"Logging in to LinkedIn as {LINKEDIN_USERNAME}...")
    wd = webdriver.Chrome(options=chrome_options) #firefox
    wd.delete_all_cookies()
    wd.get(url_login)
    print(f"session_key")
    time.sleep(20)
    print(f"At {url_login}, entered {LINKEDIN_USERNAME}")
  
    wd.find_element(By.XPATH, "//*[@id='session_key']").send_keys(LINKEDIN_USERNAME) #new method
    time.sleep(5)
    wd.find_element(By.ID, "session_password").send_keys(LINKEDIN_PASSWORD)
    print(f"session_password")
    time.sleep(5)
    #wd.find_element(By.XPATH, "//button[@class='sign-in-form__submit-btn']").click()
    wd.find_element(By.CSS_SELECTOR, "[data-id='sign-in-form__submit-btn']").click()
    print("Signing in")
    time.sleep(30)
    # random confirm acount information pop up that may come up
    try:
        print("trying")
        time.sleep(5)
        wd.find_element(By.XPATH, "//button[@class='primary-action-new']").click()
    except:
        print("exception")
        pass
    logging.info("Log in complete. Scraping data...")
    print("Log in complete. Scraping data...")

    return wd


def page_search(wd, search_location, search_keyword, search_remote, search_posted, search_page, search_count, file,
                logging):
    # wait time for events in seconds
    page_wait = 10
    click_wait = 4
    async_wait = 5

    # when retrying, number of attempts
    attempts = 2

    # navigate to search page
    #time.sleep(15)
    url_search = f"https://www.linkedin.com/jobs/search/?f_TPR={search_posted}&keywords={search_keyword}&location={search_location}&start={search_page}" #removed some search terms
    wd.get(url_search)
    print(url_search)

    # find the number of results
    print(f"finding job listing box, waiting {page_wait}s...")
    time.sleep(page_wait)  # add sleep so don't get caught
    #search_count = wd.find_element(By.XPATH, "//small[@class='display-flex t-normal']").text     #original: display-flex t-12 t-black--light t-normal
    #search_count = wd.find_element(By.XPATH, "//*[@class,'jobs-search-results-list__subtitle']").text
    #span_tags = wd.find_elements(By.XPATH, "//span")

    print(f"Printing page source: \n{wd.page_source}")

    #with open("web_page_content.html", "w", encoding="utf-8") as file: #do not enable unless debugging as the later file open and append requires only prev file to be open
    #    file.write(wd.page_source)

    span_element = wd.find_element(By.CLASS_NAME, "results-context-header__job-count")
    print(f"Found class: \n{span_element}")
    search_count = span_element.get_attribute("innerHTML").replace('+','').replace(',','')
    print(search_count)
    print(type(search_count))
    #time.sleep(10)
    #split = search_count.rsplit(" ")
    search_count = int(search_count)

    logging.info(
        f"Loading page {round(search_page / 25) + 1} of {round(search_count / 25)} for {search_keyword}'s {search_count} results...")

    # get all the job_id's for xpath for current page to click each element
    # running into errors with slow load (11-Aug)
    for attempt in range(attempts):
        try:
            results = wd.find_element(By.CLASS_NAME, "jobs-search__results-list").find_elements(By.TAG_NAME, "li") #scaffold-layout__list-container : jobs-search-results__list list-style-none
            print(f"{len(results)} search results")
            result_ids = [result.find_element(By.CLASS_NAME, "job-search-card").get_attribute('data-entity-urn') for result in results if result.get_attribute('data-entity-urn') != '']
            print(f"Result IDs found - {result_ids}")
            break
        except:
            time.sleep(click_wait)  # wait a few attempts, if not throw an exception and then skip to next page

    print(f"Result IDs: {result_ids}")
    # cycle through each job_ids and steal the job data...muhahaha!
    list_jobs = []  # initate a blank list to append each page to
    for id in result_ids:
        print(f"ID {id}")
        #np.savetxt("debugging.html", np.array([wd.page_source]), fmt='%s')
        try:
            print(f"trying id {id}...")
            #job_id = id.get_attribute("data-entity-urn").split(":")[-1] #numerical id, used in url
            # select a job and start extracting information
            wd.find_element(By.XPATH, f"//div[@data-entity-urn='{id}']").click()
            logging.info("clicked into urn")
            #time.sleep(1)
            #print("printing page source...")
            #ic(f"Page source \n{wd.page_source}")
            #logging.info(wd.page_source)
            job_id = id.split(":")[-1]
        except:
            ic(f"Exception raised for ID '{id}'")
            #logging.info(wd.page_source)
            job_id = "not found"
            continue
            # exception likely to job deleteing need to go to next id

        wd.save_screenshot('ss1.png')
        #np.savetxt("debugging.html", np.array([wd.page_source]), fmt='%s')
        #logging.info(wd.page_source)
        #top-card-layout__entity-info-container
        #topcard__org-name-link
        ic(wd.find_element(By.CLASS_NAME, "top-card-layout__entity-info-container"))


        for attempt in range(attempts):
            print("Attempting to find job title")
            try:
                # from analysis 3 attempts at 5 second waits gets job titles 99.99% of time (11-Aug)
                job_title = wd.find_element(By.CLASS_NAME, "top-card-layout__title")  # keep having issues with finding element
                job_title = job_title.get_attribute("innerHTML")
                ic(job_title)
                #time.sleep(1)
                break
            except:
                print("No job title found")
                logging.info("No job title found")
                logging.info(wd.find_element(By.CLASS_NAME, "top-card-layout__entity-info-container"))

                job_title = ''
                time.sleep(2)

        # Having issues finding xpath of company (Added 11-Aug)
        #class="details-pane__content details-pane__content--show"
        time.sleep(5)
        htmlraw = wd.find_element(By.CLASS_NAME, "details-pane__content").text #details-pane__content details-pane__content--show
        ic(htmlraw)
        soup_details_pane = bs(htmlraw, 'html.parser').text
        ic(soup_details_pane)

        for i, keyskill in enumerate(keywords_to_count_lower):
            if keyskill in htmlraw.lower():
                counts_list[i] += 1

        for attempt in range(attempts):
            try:
                print("finding company, location, remote...")
                #job_top_card1 = wd.find_element_by_xpath("//span[@class='jobs-unified-top-card__subtitle-primary-grouping mr2 t-black']").find_elements_by_tag_name("span")

                company = wd.find_element(By.CLASS_NAME, "topcard__org-name-link").get_attribute("innerHTML")  #job_top_card1[0].text
                location = wd.find_element(By.CLASS_NAME, "topcard__flavor topcard__flavor--bullet").get_attribute("innerHTML") #topcard__flavor topcard__flavor--bullet
                if "Remote" in soup_details_pane:
                    remote = "Remote"
                else:
                    remote = ''
                break
            except:
                company = ''
                location = ''
                remote = ''
                time.sleep(2)

        for attempt in range(attempts):
            try:
                # multiple issues with job_top_card2 loading
                #job_top_card2 = wd.find_element_by_xpath("//span[@class='jobs-unified-top-card__subtitle-secondary-grouping t-black--light']").find_elements_by_tag_name("span")
                #posted-time-ago__text
                #update_time = wd.find_element(By.CLASS_NAME, "posted-time-ago__text").get_attribute("innerHTML") #UPDATE FOR NEXT VERSION
                update_time = 'nan'
                #num-applicants__caption
                applicants_raw = wd.find_element(By.CLASS_NAME, "num-applicants__caption").get_attribute("innerHTML").replace('\n','').replace('\\','')
                repattern = r'.* (\d+) .*'
                applicants = re.search(repattern, applicants_raw).group(1)
                break
            except:
                update_time = ''  # after #attempts leave as blank and move on
                applicants = ''  # after #attempts leave as blank and move on
                time.sleep(click_wait)

        # Due to (slow) ASYNCHRONOUS updates, need wait times to get job_info
        job_time = ''  # assigning as blanks as not important info and can skip if not obtained below
        job_position = ''
        job_pay = ''
        for attempt in range(attempts):
            try:
                # 1 - make sure HTML element is loaded
                time.sleep(page_wait)
                element = wd.find_element(By.CLASS_NAME, "description__text")
                # 2 - make sure text is loaded
                soup_job_details = bs(element, 'html.parser').text
                ic(soup_job_details)

                try:
                    job_info = soup_job_details
                    if job_info != '':
                        # seperate job information on time requirements and position
                        job_info = job_info.split("<p>").replace("<p><br>","").replace("</p>", " ") #job_pay job_time job_position
                        salary_pattern = re.compile(r'(£\d{2,3},\d{3} - £\d{2,3},\d{3})(.*)?')
                        matches = salary_pattern.match(job_info)
                        salary = matches.group(1)
                        benefits = matches.group(2)
                        job_pay = salary

                        break
                    else:
                        time.sleep(async_wait)
                except:
                    # error means page didn't load so try again
                    time.sleep(async_wait)
            except:
                # error means page didn't load so try again
                time.sleep(async_wait)

        # get company details and seperate on size and industry
        company_size = ''  # assigning as blanks as not important info and can skip if not obtained below
        company_industry = ''
        job_details = ''
        #for attempt in range(attempts):
        #    try:
        #        company_details = wd.find_element_by_xpath("//div[@class='mt5 mb2']/div[2]").text
        #        if " · " in company_details:
        #            company_size = company_details.split(" · ")[0]
        #            company_industry = company_details.split(" · ")[1]
        #        else:
        #            company_size = company_details
        #            company_industry = ''
        #        job_details = wd.find_element_by_id("job-details").text.replace("\n", " ")
        #        break
        #    except:
        #        time.sleep(click_wait)

        # append (a) line to file
        date_time = datetime.datetime.now().strftime("%d%b%Y-%H:%M:%S")
        search_keyword = search_keyword.replace("%20", " ")
        list_job = [date_time, search_keyword, search_count, job_id, job_title, company, location, remote, update_time,
                    applicants, job_pay, job_time, job_position, company_size, company_industry, job_details]
        list_jobs.append(list_job)

        list_jobs_external.append(list_job)

    ic(f"List jobs: {list_jobs}")

    ic(file)
    date_time = datetime.datetime.today().strftime("%d-%b-%y_%H:%M:%S")

    with open(file, 'a') as f:
        w = csv.writer(f)
        w.writerows(list_jobs)
        list_jobs = []

    logging.info(f"Page {round(search_page / 25) + 1} of {round(search_count / 25)} loaded for {search_keyword}")
    search_page += 25

    return search_page, search_count, url_search

# create logging file
print("logfile...")
logging = create_logfile()
print("...created")

# create daily csv file
date = datetime.date.today().strftime('%d-%b-%y')
file = f"output/{date}.csv"
create_file(file)

# login to linkedin and assign webdriver to variable
wd = login(logging)

# URL search terms focusing on what type of skills are required for Data Analyst & Data Scientist
search_keywords = ['Data Analyst', 'Data Scientist', 'Data Engineer']
    # Titles to remove as search is too long
    # ['Business Analyst', 'Operations Analyst', 'Marketing Analyst', 'Product Analyst',
    # 'Analytics Consultant', 'Business Intelligence Analyst', 'Quantitative Analyst',  'Data Architect',
    # 'Data Engineer', 'Machine Learning Engineer', 'Machine Learning Scientist']
search_location = "United%20Kingdom"
search_remote = "true" # filter for remote positions
search_posted = "r86400" # filter for past 24 hours



# Counting Exceptions
exception_first = 0
exception_second = 0

for search_keyword in search_keywords:
    search_keyword = search_keyword.lower().replace(" ", "%20")
    print(f"Search keyword {search_keyword}, from ")
    try:
        print(*search_keywords)
    except:
        pass

# Loop through each page and write results to csv
    search_page = 0 # start on page 1
    search_count = 1 # initiate search count until looks on page
    while (search_page < search_count) and (search_page != 1000):
        # Search each page and return location after each completion
        try:
            search_page, search_count, url_search = page_search(wd, search_location, search_keyword, search_remote, search_posted, search_page, search_count, file, logging)
        except Exception as e:
            logging.error(f'(1) FIRST exception for {search_keyword} on {search_page} of {search_count}, retrying...')
            logging.error(f'Current URL: {url_search}')
            logging.error(e)
            logging.exception('Traceback ->')
            exception_first += 1
            time.sleep(5)
            try:
                search_page, search_count, url_search = page_search(wd, search_location, search_keyword, search_remote, search_posted, search_page, search_count, file, logging)
                logging.warning(f'Solved Exception for {search_keyword} on {search_page} of {search_count}')
            except Exception as e:
                logging.error(f'(2) SECOND exception remains for {search_keyword}. Skipping to next page...')
                logging.error(f'Current URL: {url_search}')
                logging.error(e)
                logging.exception('Traceback ->')
                search_page += 25 # skip to next page to avoid entry
                exception_second += 1
                logging.error(f'Skipping to next page for {search_keyword}, on {search_page} of {search_count}...')

date_time = datetime.datetime.today().strftime("%d-%b-%y_%H:%M:%S")
np.savetxt(f"output/Results 2 {date_time}.csv", list_jobs_external, fmt='%s', header="date_time,search_keyword,search_count,job_id,job_title,company,location,remote,update_time,applicants,job_pay,job_time,job_position,company_size,company_industry,job_details")
np.savetxt("output/Count of key skills.csv", counts_list, fmt='%s')

# close browser
wd.quit()

logging.info(f'LinkedIn data scraping complete with {exception_first} first and {exception_second} second exceptions')


#https://www.linkedin.com/jobs/search/?f_TPR=r86400&f_WRA=true&geoId=103644278&keywords=Data%20Analyst&location=United%20Kingdom&start=0
