import json
d = json.load(open("transform_result.json"))
json.dump(d["candidate"], open("candidate.json", "w"), indent=2)
