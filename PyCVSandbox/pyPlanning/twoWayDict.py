class TwoWayDict(dict):
    def __len__(self):
        return dict.__len__(self) / 2
	
    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        dict.__setitem__(self, value, key)

d = TwoWayDict()
d[(1,2)] = "red"
d[(1,4)] = "blue"
d[(1,6)] = "green"

print d[(1,2)], d["red"]
print d[(1,6)], d["green"]
print d[(1,4)], d["blue"]