import sys
import os
import pyqrcode
from jinja2 import Environment, FileSystemLoader
from pandas import read_excel


def main(filepath, folder):
    if not os.path.exists(folder):
        os.mkdir(folder)

    data = read_excel(sys.argv[1], header=None,
                names=['refno', 'uid', 'title', 'firstname', 'lastname'])
    students = []
    for _, student in data.iterrows():
        qrcode = pyqrcode.create(student['uid'])
        qrcode.png('{}/{}.png'.format(folder, student['uid']), scale=6)
        students.append(student)

    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('qrcode-template.html')
    output = open('{}.html'.format(folder), 'w')
    output.write(template.render(students=students, folder=folder).encode('utf-8'))
    output.close()

if __name__ == '__main__':
    if len(sys.argv) == 3:
        filepath = sys.argv[1]
        folder = sys.argv[2]
        main(filepath, folder)
    else:
        raise SystemError
