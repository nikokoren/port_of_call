"""Export the current TRMNL field array for direct use in the web editor."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    fields = (ROOT/'settings.yml').read_text().split('custom_fields:\n', 1)[1]
    fields = '\n'.join(line[2:] if line.startswith('  ') else line for line in fields.splitlines())+'\n'
    (ROOT/'custom_fields.yml').write_text(fields)
    print('Updated custom_fields.yml from settings.yml')


if __name__ == '__main__': main()
