#!/usr/bin/env python3
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

for i in range(last + 1):
    cur_sum = HC[i] + HWC[i]
    readings_sum = (last_reading + (cur_sum - last_sum) / last_cal)
    readings_mregr = beta_hat[0] * HC[i] + beta_hat[1] * HWC[i] + beta_hat[2]
    print('Reading: meter %.3f sum cal %.3f error %.3f; multi regression: %.3f '
          'error %.3f ' %
          (METER[i], readings_sum, abs(METER[i] - readings_sum),
           readings_mregr, abs(METER[i] - readings_mregr)))
