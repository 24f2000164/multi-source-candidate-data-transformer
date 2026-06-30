import json
d = json.load(open("transform_result.json"))
print("success:", d["success"])
print("exit_code:", d["exit_code"])
print("reports:", list(d["reports"].keys()))
print("validation summary:", d["reports"]["validation"]["summary"])
