import json
d = json.load(open("project_result.json"))
print("success:", d["success"])
print("projection field_count:", d["reports"]["projection"]["field_count"])
