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

def scrape_google_maps(search_query, total):
    business_list = BusinessList()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("https://www.google.com/maps", timeout=60000)
        page.wait_for_timeout(5000)

        page.locator('//input[@id="searchboxinput"]').fill(search_query)
        page.wait_for_timeout(3000)

        page.keyboard.press("Enter")
        page.wait_for_timeout(5000)

        page.hover('//a[contains(@href, "https://www.google.com/maps/place")]')

        previously_counted = 0
        while True:
            page.mouse.wheel(0, 10000)
            page.wait_for_timeout(3000)

            if (
                page.locator(
                    '//a[contains(@href, "https://www.google.com/maps/place")]'
                ).count()
                >= total
            ):
                listings = page.locator(
                    '//a[contains(@href, "https://www.google.com/maps/place")]'
                ).all()[:total]
                listings = [listing.locator("xpath=..") for listing in listings]
                print(f"Total Scraped: {len(listings)}")
                break
            else:
                if (
                    page.locator(
                        '//a[contains(@href, "https://www.google.com/maps/place")]'
                    ).count()
                    == previously_counted
                ):
                    listings = page.locator(
                        '//a[contains(@href, "https://www.google.com/maps/place")]'
                    ).all()
                    print(f"Arrived at all available\nTotal Scraped: {len(listings)}")
                    break
                else:
                    previously_counted = page.locator(
                        '//a[contains(@href, "https://www.google.com/maps/place")]'
                    ).count()
                    print(
                        f"Currently Scraped: ",
                        page.locator(
                            '//a[contains(@href, "https://www.google.com/maps/place")]'
                        ).count(),
                    )

        for listing in listings:
            listing.click()
            page.wait_for_timeout(5000)

            name_xpath = '//div[contains(@class, "fontHeadlineSmall")]'
            address_xpath = '//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]'
            website_xpath = '//a[@data-item-id="authority"]//div[contains(@class, "fontBodyMedium")]'
            phone_number_xpath = '//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]'
            reviews_span_xpath = '//span[@role="img"]'

            business = Business()

            if listing.locator(name_xpath).count() > 0:
                business.name = listing.locator(name_xpath).inner_text()
            else:
                business.name = ""
            if page.locator(address_xpath).count() > 0:
                business.address = page.locator(address_xpath).inner_text()
            else:
                business.address = ""
            if page.locator(website_xpath).count() > 0:
                business.website = page.locator(website_xpath).inner_text()
            else:
                business.website = ""
            if page.locator(phone_number_xpath).count() > 0:
                business.phone_number = page.locator(phone_number_xpath).inner_text()
            else:
                business.phone_number = ""
            if listing.locator(reviews_span_xpath).count() > 0:
                business.reviews_average = float(
                    listing.locator(reviews_span_xpath)
                    .get_attribute("aria-label")
                    .split()[0]
                    .replace(",", ".")
                    .strip()
                )
                business.reviews_count = int(
                    listing.locator(reviews_span_xpath)
                    .get_attribute("aria-label")
                    .split()[2]
                    .strip()
                )
            else:
                business.reviews_average = ""
                business.reviews_count = ""

            business_list.business_list.append(business)

        browser.close()
    
    return business_list.business_list

def scrape_bing_maps(search_query, total):
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

    return [asdict(business) for business in business_list.business_list]
    


@app.route('/scrap/<path:job_profile>/<path:city>/<int:total>')
def scrape_maps(job_profile, city, total):
    search_query = f"{job_profile} in {city}"
    fetched_data = []
    how_many_printed = 0

    if how_many_printed < total:
        fetched_data = scrape_google_maps(search_query, total)
        how_many_printed = len(fetched_data)

    if how_many_printed < total:
        bing_data = scrape_bing_maps(search_query, total - how_many_printed)
        fetched_data.extend(bing_data)

    return jsonify(fetched_data)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5551, debug=True)