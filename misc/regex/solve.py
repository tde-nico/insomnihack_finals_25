import re

with open('flag_clean.txt', 'r', encoding='utf-8') as f:
	regex = f.read()

regex = regex.replace('\n', '').replace('(?^)', '')


stack = []
start = 0
for i, c in enumerate(regex):
	if c == '(':
		stack.append(c)
	elif c == ')':
		stack.pop()
		if len(stack) == 0:
			reg = regex[start:i+1]
			start = i+1
			if '#' in reg:
				continue

			r = re.compile(reg)

			for c in sorted(list(set(reg))):
				if r.match(c):
					print(c, end='')

print()

# INS{wtff🌍ff_l🐸ol_wut123}
