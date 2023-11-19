# Modified LinkedIn data scraping script, original by Luke Barousse

Luke's scraping script wasn't working for my browser, perhaps due to date and region. I have therefore modified it so that it will. Please follow Luke's guide for installation etc.
https://github.com/lukebarousse/Job_Analysis


Less significantly, the .get_element_by_[method]\() has been deprecated. New behaviour is .find_element\[/s]\(By.[method], "[identifier]").
https://selenium-python.readthedocs.io/locating-elements.html

I have included my version of chromedriver.exec (Intel Mac). Python version 3.11.

# Disclaimer

NOTICE: The use of robots or other automated means to access LinkedIn without the express permission of LinkedIn is STRICTLY PROHIBITED.
IMPORTANT NOTE: LinkedIn will BLOCK you from searching if you are scraping too much data and/or you don't have permission.

# Additional libraries
- Numpy v1.25.2
- Icecream v2.1.3 (excellent debugging print statement upgrade)
- Regex (standard library)
- Beautiful Soup 4 [bs4] v0.0.1 on PyCharm (html parser)
