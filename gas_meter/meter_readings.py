#!/usr/bin/env python3
import math
import numpy as np
from sklearn import linear_model

FIELD_DATETIME = 0
FIELD_METER = 1
FIELD_HC = 2
FIELD_HWC = 3
FIELD_VALID = 4
FIELD_COMMENT = 5

log_file = open('meter_readings.csv', 'r')
log = log_file.readlines()

METER = []
HC = []
HWC = []
print('Stored readings:\n')
for line in log:
    s = line.strip().split(',')
    if int(s[FIELD_VALID]):
        METER.append(float(s[FIELD_METER]))
        HC.append(int(s[FIELD_HC]))
        HWC.append(int(s[FIELD_HWC]))
        print('\t%s' % line)
    else:
        print('\tSkipping ' + line)

clf = linear_model.LinearRegression()
y = np.array(METER)
X = np.array([np.array(HC), np.array(HWC)])
# transpose so input vectors are along the rows
X = X.T
# add bias term
X = np.c_[X, np.ones(X.shape[0])]
beta_hat = np.linalg.lstsq(X, y, rcond=None)[0]

print('\nMultiple regression:')
print(beta_hat)

#https://techniczny.wordpress.com/2018/04/08/pomiar-zuzycia-gazu-przez-raspberry-pi-i-ebus/
print('\nCoefficient for the sum of Hc1 and Hwc1')
last = len(METER) - 1
last_reading = METER[last]
last_hc1 = HC[last]
last_hwc1 = HWC[last]
last_sum = last_hc1 + last_hwc1
last_cal = last_sum / last_reading
print('Meter: %s calibration %s\n' % (last_reading, last_cal))

print("Note! jinja 2.3.10 doesn't support scientific notation, work around:")
def exp10(x):
    try:
        exp = int(math.log10(x))
        return x / 10**exp, exp
    except ValueError:
        return x, 0

print('Use: meter = X[0] * HC + X[1] * HWC + X[2]')

man_0, exp_0 = exp10(beta_hat[0])
man_1, exp_1 = exp10(beta_hat[1])
man_2, exp_2 = exp10(beta_hat[2])

print('{%% set X = [%s/10**%s, %s/10**%s, %s] %%}' %
      (man_0, abs(exp_0), man_1, abs(exp_1), man_2))

print('X = [%s, %s, %s]' % (beta_hat[0], beta_hat[1], beta_hat[2]))

DT = []
METER = []
HC = []
HWC = []
for line in log:
    s = line.strip().split(',')
    DT.append(s[FIELD_DATETIME])
    METER.append(float(s[FIELD_METER]))
    HC.append(int(s[FIELD_HC]))
    HWC.append(int(s[FIELD_HWC]))

print('\nTesting on the whole data set')
for i in range(len(METER)):
    cur_sum = HC[i] + HWC[i]
    readings_sum = (last_reading + (cur_sum - last_sum) / last_cal)
    readings_mregr = beta_hat[0] * HC[i] + beta_hat[1] * HWC[i] + beta_hat[2]
    print('%s Reading: meter %.3f sum cal %.3f error %.3f; multi regression: %.3f '
          'error %+.3f ' %
          (DT[i], METER[i], readings_sum, (readings_sum - METER[i]),
           readings_mregr, (readings_mregr - METER[i])))
