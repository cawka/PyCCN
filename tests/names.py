from pyndn import _pyndn, NDN, Name
import sys

comps = ['this', 'is', 'some', 'name']
print(comps)

ndn_name = _pyndn.name_comps_to_ndn(comps)
comps2 = _pyndn.name_comps_from_ndn(ndn_name)
print(comps2)

#for comp1, comp2 in zip(map(lambda x: bytearray(x), comps), comps2):
for comp1, comp2 in zip([bytearray(x, "ascii") for x in comps], comps2):
	if comp1 != comp2:
		raise AssertionError("Got a different output: '%s' != '%s'" % (comp1, comp2))

n = Name(['hello', 'world'])

print(str(n))
if str(n) != "/hello/world":
	raise AssertionError("expected /hello/world")

n = Name("ndn:///testing/1/2/3/")
print(str(n))
if str(n) != "/testing/1/2/3":
	raise AssertionError("expected /testing/1/2/3 got: " + str(n))

if len(n) != 4:
	raise AssertionError("expected 4 components, got: " + len(n))

print(n.components)
assert(n.components == [b'testing', b'1', b'2', b'3'])

n = Name([1, '2', bytearray(b'3'), bytes(b'4')])
print(str(n))
assert(str(n) == "/1/2/3/4")

n = Name()
print(str(n))
n = n.appendSegment(5)
print(str(n))

assert(str(n) == "/%00%05")

