import json
import sys
import protocol

print(json.dumps(protocol.observe(sys.argv[1]), sort_keys=True))
