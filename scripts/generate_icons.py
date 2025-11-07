import os
from simpleicons.icons import si_python, si_cplusplus

def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    icons_dir = os.path.join(root, 'assets', 'icons')
    os.makedirs(icons_dir, exist_ok=True)
    # Guardar SVGs con colores clásicos
    with open(os.path.join(icons_dir, 'python.svg'), 'wb') as f:
        f.write(si_python.get_xml_bytes(fill='#3776AB'))
    with open(os.path.join(icons_dir, 'cplusplus.svg'), 'wb') as f:
        f.write(si_cplusplus.get_xml_bytes(fill='#00599C'))
    print('SVG icons written to', icons_dir)

if __name__ == '__main__':
    main()