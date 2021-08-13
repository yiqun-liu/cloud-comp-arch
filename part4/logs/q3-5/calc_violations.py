import sys

def main(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()

    violations, total = 0, 0
    for line in lines:
        if not line.startswith('read'):
            continue
        total += 1
        p95 = float(line.split()[12])
        if p95 > 2000:
            violations += 1

    print(violations, total, violations / total)

if __name__ == '__main__':
    main(sys.argv[1])
