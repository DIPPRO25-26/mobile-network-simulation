import random
import pathlib

def calc_luhn(i):
    s = [*map(int, i)]
    total = 0
    for i, x in enumerate(s):
        if i % 2:
            # zbroj znamenki (dvoznamenkastog broja)
            total += (x*2) // 10 + (x*2) % 10
        else:
            total += x
    return (10 - total) % 10


tacdb_file = pathlib.Path(__file__).with_name("tacdb.csv")
with tacdb_file.open() as f:
    data = f.readlines()
    taclist = [x.split(',')[0] for x in data]


def gen_imei():
    tac = random.choice(taclist)
    serial = random.randint(10**5, 10**6-1)
    x = f"{tac}{serial}"
    check_digit = calc_luhn(x)
    return f"{x}{check_digit}"

if __name__ == "__main__":
    for _ in range(10):
        print(gen_imei())
