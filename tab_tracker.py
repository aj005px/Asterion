from url_extractor import splitter,time_manager

domain, url = splitter()
time_spent = time_manager(url)

tab = {
    "url": None,
    "domain": None,
    "visits": 0,
    "time_spent": 0
}

tab["url"] = url
tab["domain"] = domain
tab["time_spent"] = time_spent
tab["visits"] = 1

print(tab)
