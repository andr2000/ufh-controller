#!/usr/bin/env python3
import itertools
import numpy

log_file = open('meter_readings.log', 'r')
log = log_file.readlines()

print('Stored readings:\n')
data = []
for line in log:
    data.append(line.strip().split(';'))
    print('\t%s' % line)

# FIXME: get rid of repeated elements: AB BA
perms = itertools.permutations(data, 2)
for i in perms:
    # Form matrices: the result of the permutations above is:
    # (['2020-01-11 22:55:00', '1849.662', '1735840618', '96401092']
	#  ['2020-01-11 21:12:00', '1848.412', '1733683455', '96401092'])
    eq1 = i[0]
    eq2 = i[1]
    print('Solving\n\t%s\n\t%s\n' %(eq1, eq2))
    A = numpy.array([[int(eq1[2]), int(eq1[3])], [int(eq2[2]), int(eq2[3])]])
    B = numpy.array([float(eq1[1]), float(eq2[1])])
    try:
        X = numpy.linalg.inv(A).dot(B)
    except numpy.linalg.LinAlgError:
        # Singular matrix: this can happen if meter readings
        # have adjusted, but BAI counters not: for instance if other consumers
        # than BAI were active
        print('\tSkipping\n')
        pass
    print(X)

#https://techniczny.wordpress.com/2018/04/08/pomiar-zuzycia-gazu-przez-raspberry-pi-i-ebus/
print('\nCoefficient for the sum of Hc1 and Hwc1\n')
last = len(data) - 1
last_reading = float(data[last][1])
last_hc1 = int(data[last][2])
last_hwc1 = int(data[last][3])
last_cal = (last_hc1 + last_hwc1) / last_reading
print('Meter: %s calibration %s\n' % (last_reading, last_cal))

for i in data:
    meter = float(i[1])
    hc1 = int(i[2])
    hwc1 = int(i[3])
    cur_sum = hc1 + hwc1
    last_sum = last_hc1 + last_hwc1
    readings = (last_reading + (cur_sum - last_sum) / last_cal)
    print('Reading: %.3f real %.3f error %.3f' %
          (readings, meter, abs(meter - readings)))