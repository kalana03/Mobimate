import scraper
from bs4 import BeautifulSoup

url = "https://www.mobitel.lk/broadband/plans-and-rates-prepaid"
soup = scraper.scrape(url)

plans_section = soup.find('div', class_='page_tabing_title_area')
if plans_section is None:
    raise ValueError('Could not find plans section in HTML')

plan_btns = plans_section.find_all('div', class_='title_parent')

plans = []

i = 1
for plan in plan_btns:
    p = "tabtitle_" + str(i)

    pln = plan.find('a')
    
    if pln is None:
        continue
    plans.append([pln.get_text(), pln.get('href')])

print(plans)

# print("Packages: ")
# i=0
# for plan in plans:
#     i += 1
#     print (str(i) + "." + plan[0])
