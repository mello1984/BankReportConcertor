import fitz
import re

source_pdf = r'G:/Files/210202_104937.pdf'
result_tsv = r'G:/Files/transactions {}-{}.tsv'

pattern_dates = r'\d\d\.\d\d\.\d\d\d\d \d\d\.\d\d\.\d\d\d\d'
with fitz.Document(source_pdf) as source:
    text = '\n'.join([page.get_textpage().extractText().strip().lower() for page in source])
text = text.splitlines()

start, stop, period, control_plus, control_minus = 0, 0, '', 0, 0
for i in range(len(text)):
    if re.match(pattern_dates, text[i]) and start == 0:
        start = i
    if 'всего поступлений' in text[i] and stop == 0:
        stop = i
        control_plus = float(re.sub(r'[^\d.]', '', re.match(r'.*([–+] [\d,.]*) ᵽ', text[i]).group(1)))
    if 'всего расходов' in text[i]:
        control_minus = -float(re.sub(r'[^\d.]', '', re.match(r'.*([–+] [\d,.]*) ᵽ', text[i]).group(1)))
    if 'операции за период' in text[i]:
        period = re.match(r'.*(\d\d\.\d\d\.\d\d\d\d) по (\d\d\.\d\d\.\d\d\d\d)', text[i])
lines = text[start:stop]

tr, string = [], ''
for s in lines:
    if re.match(pattern_dates, s):
        tr.append(string)
        string = s
    else:
        string = string + ' ' + s
tr.append(string)

pattern = r'(\d\d\.\d\d\.\d\d\d\d) (\d\d\.\d\d\.\d\d\d\d) ([+-].* ᵽ) ([+-].* ᵽ) (.*?) (.*)'
trs, sum_plus, sum_minus = [], 0, 0
for i in range(1, len(tr)):
    s = re.match(pattern, re.sub(r'( \*\*.*)|,', '', tr[i]).replace('  ', ' '))
    amount = re.sub(r'[ ᵽ]', '', s.group(3))
    sum_plus += [0, float(amount)][float(amount) > 0]
    sum_minus += [0, float(amount)][float(amount) < 0]

    arr = [s.group(1), s.group(2), amount.replace('.', ','), s.group(5)]
    [arr.append(q.strip()) for q in s.group(6).split('\\')[:3]]

    if 'cashback' in arr[4]:
        arr[3] = arr[4] = 'cashback'
    if not re.search(r'[а-я]', arr[4]):
        arr[4] = re.sub(r'[^a-zа-я ]', '', arr[4]).strip()
    trs.append(arr)

result_file = result_tsv.format(period.group(2), period.group(1))
with open(result_file, 'w') as fo:
    fo.write('date card transaction\tdate account transaction\tamount\ttype\tdescription\tplace1\tplace2\n')
    result = '\n'.join(['\t'.join(t) for t in trs])
    fo.write(result)

print(result_file, 'OK')
print('plus', control_plus, [sum_plus, 'OK'][abs(control_plus - sum_plus) <= 1])
print('minus', control_minus, [sum_minus, 'OK'][abs(control_minus - sum_minus) <= 1])
