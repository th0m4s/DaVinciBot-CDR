from threading import Thread
from timeit import repeat
from dvbcdr.intercom import Intercom
from dvbcdr.utils.maths import round_significant_decimals

import dvbcdr.utils.benchmark as bm
import numpy as np
import time

print("Generating NumPy dataset...")
np_dataset = bm.gen_numpy_set(6, 3000)

print("Generating Python dataset...")
py_dataset = bm.gen_python_set(3000)

results = []


def start_load(name):
    print("\nStarting benchmark '" + name + "'...")

    np_time = bm.numpy_load(np_dataset)
    print("  - NumPy time: ", np_time)

    py_time = bm.python_load(py_dataset)
    print("  - Python time:", py_time)

    results.append((name, np_time, py_time))

    return (np_time, py_time)


def print_summary():
    if len(results) > 1:
        print("\nSummary:")

        base_result = results[0]
        base_time = base_result[1] + base_result[2]
        for i in range(1, len(results)):
            current_times = results[i]
            current_total_time = current_times[1] + current_times[2]
            perc = (current_total_time - base_time) / base_time * 100
            print("  '" + current_times[0] + "' is " + str(round_significant_decimals(abs(perc), 4)) + "% " + ("slower" if perc > 0 else "faster"))


start_load("empty load")

intercom = Intercom()
intercom.subscribe("test_topic")
start_load("with receiving thread")


def send_messages():
    while True:
        intercom.publish("test_topic", 42)


intercom.wait_in_new_thread()
thread = Thread(target=send_messages, daemon=True)
thread.start()
start_load("with sending thread")

print_summary()


def publish_message():
    intercom.publish("test_topic", 42)


print("\nTime to publish 10k messages (20 times):")
start_publish = time.time()
reps = repeat(publish_message, repeat=20, number=10000)
time_diff = time.time() - start_publish

print("  Min:", round_significant_decimals(np.min(reps), 4),
      "\tAvg:", round_significant_decimals(np.mean(reps), 4),
      "\tMax:", round_significant_decimals(np.max(reps), 4),
      "\tTotal:", round_significant_decimals(time_diff, 4))

per_sec = [10000 / x for x in reps]
print("Messages per second:")
print("  Min:", int(np.min(per_sec)),
      "\tAvg:", int(np.mean(per_sec)),
      "\tMax:", int(np.max(per_sec)))
