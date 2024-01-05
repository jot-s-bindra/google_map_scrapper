from flask import Flask, jsonify, request
from playwright.sync_api import sync_playwright
from dataclasses import dataclass, asdict, field
import json

app = Flask(__name__)

@dataclass
class Business:
    """holds business data"""
    name: str = None
    phone_number: str = None
    address: str = None
    website: str = None

@dataclass
class BusinessList:
    business_list: list[Business] = field(default_factory=list)

@app.route('/scrape_google_maps/<path:job_profile>/<path:city>')
def scrape_bing_maps_with_params(job_profile, city):
    search_query = f"{job_profile} in {city}"
    total = request.args.get('total') if request.args.get('total') else 1

    business_list = BusinessList()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("https://www.bing.com/maps", timeout=60000)
        page.wait_for_timeout(5000) 

        page.locator('//input[@id="maps_sb"]').fill(search_query)  
        page.wait_for_timeout(3000)

        page.keyboard.press("Enter")
        page.wait_for_timeout(5000)

        listings = page.locator("//div[@class='entity-listing-container']//div[@class='b_rich']//ul[@class='b_vList b_divsec']//li[@data-priority]").all()

        for listing in listings[:total]:
            listing.click()
            page.wait_for_selector('//h2[@class="nameContainer"]')
            name_xpath = '//h2[@class="nameContainer"]'
            phone_number_xpath = "//a[contains(@class, 'longNum')]"
            address_xpath = "//div[@class='b_infocardFactRows']/span[contains(text(),'Address')]"
            website_xpath = '//div[contains(@aria-label, "Website")]/a'

            business = Business()
            business.name = page.locator(name_xpath).inner_text()
            business.phone_number = page.locator(phone_number_xpath).inner_text()

            address_found = False
            try:
                business.address = page.locator(address_xpath).inner_text()
                address_found = True
            except Exception as e:
                pass

            if not address_found:
                address_xpath_alt = "//div[contains(@aria-label, 'Address')]/div"
                try:
                    business.address = page.locator(address_xpath_alt).inner_text()
                except Exception as e:
                    business.address = "Address not found"

            website_found = False
            try:
                business.website = page.locator(website_xpath).inner_text()
                website_found = True
            except Exception as e:
                pass

            if not website_found:
                website_xpath_alt = "//div[@class='b_infocardFactRows']/a[contains(@href,'http')]"
                try:
                    business.website = page.locator(website_xpath_alt).inner_text()
                except Exception as e:
                    business.website = "Website not found"

            business_list.business_list.append(business)

        browser.close()

    return jsonify([asdict(business) for business in business_list.business_list])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

