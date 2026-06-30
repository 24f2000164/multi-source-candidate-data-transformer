import json
d = json.load(open("merge_result.json"))
print("success:", d["success"])
print("reports:", list(d["reports"].keys()))
print("email chosen:", d["candidate"]["contact"]["email"])
print("skills:", d["candidate"]["skills"])
print("warnings:", d["reports"]["merge"]["warnings"])
