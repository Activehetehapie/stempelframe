a = 5
b = 4
c = lambda: a + b
d = lambda: c() + b
print(c(), d())
a += 1
print(c(), d())
print(d())