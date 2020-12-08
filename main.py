from http.server import BaseHTTPRequestHandler, HTTPServer
from itertools import groupby
import datetime

dict = {
    'Первое утверждение верно, второе утверждение верно, связь верна': 'А',
    'Первое утверждение верно, второе утверждение верно, связь неверна': 'Б',
    'Первое утверждение верно, второе утверждение неверно, связь неверна': 'В',
    'Первое утверждение неверно, второе утверждение верно, связь неверна': 'Г',
    'Первое утверждение неверно, второе утверждение неверно, связь неверна': 'Д'
}
types = {
    'radio-check': 'выбрать верный(е) варианты',
    'table': 'Задание с таблицей',
    'sopost': 'Сопоставьте элементы'
}


errors = ['Not_found', "too many answers!", "answers not found", "question not found"]
true = '  (Скорее верно)'
false = '  (Вероятно, ошибка распознавания)'
separator = ';'


class HttpProcessor(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('content-type', 'text/html')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(b"hello !")

    def do_POST(self):
        self.send_response(200)
        self.send_header('content-type', 'text')
        self.send_header('Access-Control-Allow-Origin', 'https://ks.rsmu.ru')
        self.end_headers()

        content_len = int(self.headers.get('Content-Length'))
        post_body = self.rfile.read(content_len).decode('utf-8')
        req = post_body.strip().replace(' ', ' ').split('\n')
        #print_2_file = [["path", self.path]]
        print("path: ", self.path)

        if self.path == '/':
            print()
            print(post_body.strip().split('\n'))

            req = post_body.strip().replace(' ', ' ').split('\n')
            print((search_ans(req[0], req[1].replace('ё', 'е'), req[2])))
            self.wfile.write(bytes('\n'.join(search_ans(req[0], req[1].replace('ё', 'е'), req[2])), encoding='utf-8'))
        elif self.path == '/error':
            # theme question type error = 'ans_not_found'
            # theme question type = 'table-check' table_answers
            # theme question type = 'table' ' '
            # theme question type = 'sopost' table_answers span_text
            print(post_body.strip().split('\n'))
            theme = post_body.strip().replace('\t', '').replace(' ', ' ').split('\n')[0]

            with open(theme + '_errors.txt', 'a+', encoding='utf-8') as f:
                f.seek(0)
                number = 1
                resp = post_body.strip().replace('\t', '').replace(' ', ' ').split('\n')
                error_exist = False
                error_maybe_exist = False
                number_error = -1
                for line in f:
                    if '#' in line:
                        number += 1
                    if resp[1] in line:
                        # print(line + '\n' + resp[1])
                        number_error = number
                    # print(number_error == number, line[:len(line)-1] in resp[3].replace('true', true).replace('false', false))
                    # print(line + '\n' + resp[3].replace('true', true).replace('false', false))
                    if number_error == number and line[:len(line) - 1] in resp[3].replace('true', true).replace('false',
                                                                                                                false):
                        error_exist = True

                if not error_exist:
                    f.write('#' + str(number) + '\n')
                    for block in resp[1:]:
                        for el in block.split(';'):
                            try:
                                f.write(types[el] + '\n')
                            except KeyError:
                                if el:
                                    f.write(el.replace('true', true).replace('false', false) + '\n')
                        f.write('\n')

            self.wfile.write(bytes("Success!", encoding='utf-8'))
# Radio or Checkbox
        elif self.path == '/radio' or self.path == '/checkbox':
            theme = req[0]
            question = req[1]
            variants = req[2][:-1].split(separator)
            variants_compare = []
            answers = []
            que_number = -1
            cur_number = ['']
            sending = 'Not_found'
            find_answers = False
            print(req)
            # find and check all questions and variants
            with open(theme + '.txt', 'r', encoding='utf-8') as f:
                for line in f:
                    if '#' in line:
                        # include number and verify
                        que_number = line
                    elif find(question, line):
                        cur_number.append(que_number)
                        variants_compare.append([False] * len(variants))
                        if '' in cur_number:
                            cur_number.remove('')
                        answers.append([])
                    elif cur_number[-1] == que_number:
                        for i in range(len(variants)):
                            if find(variants[i], line):
                                variants_compare[-1][i] = True
                                if line.startswith('+'):
                                    answers[-1].append(str(i))
            # удаление дубликатов похоже)
            for i in range(len(answers)):
                for j in range(len(answers[i])):
                    for k in range(len(answers[i])):
                        if k != j and answers[i][k] in answers[i][j]:
                            answers[i].remove(answers[i][k])
            print(cur_number)
            print(variants_compare)
            print(answers)
            print(variants)
            if cur_number[0] == '':
                sending = "question not found"
                write_error(
                    theme,
                    question,
                    self.path,
                    sending,
                    cur_number=cur_number,
                    variants=variants,
                    variants_compare=variants_compare)
            #    print_2_file.append([sending])
                print(sending)
            else:
                for i in range(len(cur_number)):
                    if False not in variants_compare[i] and answers[i] != []:
                        find_answers = True
                        if ' 1' in cur_number[i] or ' 0' in cur_number[i]:
                            num, verify = cur_number[i][1:-1].split(' ')
                        else:
                            num = cur_number[i][1:-1]
                            verify = ''
                        sending = num + '\n' + verify + '\n' + separator.join(answers[i])
                        if self.path == '/radio' and len(answers[i]) > 1:
                            sending = "too many answers!"
                            write_error(
                                theme,
                                question,
                                self.path,
                                sending,
                                cur_number=cur_number,
                                variants=variants,
                                variants_compare=variants_compare)
            #                print_2_file.append([sending])
                            # experimental
                            sending = num + '\n' + verify + '\n' + max(answers[i], key=lambda s: len(variants[int(s)]))
                            print(sending)
            #            print_2_file.append(['true', variants[int(answers[i][0])]])
                        print('true: ', variants[int(answers[i][0])])
                if not find_answers:
                    sending = "answers not found"
                    write_error(
                        theme,
                        question,
                        self.path,
                        sending,
                        cur_number=cur_number,
                        variants=variants,
                        variants_compare=variants_compare)
               #     print_2_file.append([sending])
                    print(sending)

            # print_2_file.append(cur_number)
            # for i in range(len(answers)):
            #     print_2_file.append(list(map(str, variants_compare[i])))
            #     print_2_file.append(answers[i])
            # print_2_file.append(variants)
            # print_2_file.append(['radio or checkbox: ', sending])
            print(cur_number)
            print(variants_compare)
            print(answers)
            print(variants)
            print('radio or checkbox: ', sending)
            write_log(
                theme,
                question,
                self.path,
                sending,
                cur_number=cur_number,
                variants=variants,
                variants_compare=variants_compare)
            self.wfile.write(bytes(sending, encoding='utf-8'))
# Undef
        elif self.path == '/undefined':
            theme = req[0]
            question = req[1]
            variants = req[3][:-1].split(separator)
            spans = list(dict.fromkeys(req[2][:-1].split(separator))) #
            variants_compare = []
            spans_compare = []  #
            answers = []
            que_number = -1
            cur_number = ['']
            sending = 'Not_found'
            find_answers = False
            # find and check all questions and variants
            with open(theme + '.txt', 'r', encoding='utf-8') as f:
                for line in f:
                    if '#' in line:
                        # include number and verify
                        que_number = line
                    elif find_und(question, line):
                        cur_number.append(que_number)
                        variants_compare.append([False] * len(variants))
                        spans_compare.append([False] * len(spans))  #
                        if '' in cur_number:
                            cur_number.remove('')
                        answers.append([])
                    elif cur_number[-1] == que_number:
                        for i in range(len(spans)):  #
                            if find_und(spans[i], line):  #
                                spans_compare[-1][i] = True  #
                        for i in range(len(variants)):
                            if find_und(variants[i], line):
                                variants_compare[-1][i] = True
                                for j in range(len(spans)):  #
                                    if find_und(spans[j], line):  #
                                        answers[-1].append(str(j) + ':' + str(i))  #

            for i in range(len(cur_number)):
                if False not in variants_compare[i] and False not in spans_compare[i]:
                    find_answers = True
                    print('num, ver: ', cur_number[i][1:-1].split(' '))
                    if ' 1' in cur_number[i] or ' 0' in cur_number[i]:
                        num, verify = cur_number[i][1:-1].split(' ')
                    else:
                        num = cur_number[i][1:-1]
                        verify = ''
                    sending = num + '\n' + verify + '\n' + separator.join(answers[i])
                    if len(answers[i]) > len(variants):
                        sending = "too many answers!"
                        write_error(
                            theme,
                            question,
                            self.path,
                            sending,
                            cur_number=cur_number,
                            spans=spans,
                            spans_compare=spans_compare,
                            variants=variants,
                            variants_compare=variants_compare)
            #            print_2_file.append([sending])
                        print(sending)
            #        print_2_file.append(['true: '])
                    print('true: ')
                    for pairs in answers[i]:
                        pair = pairs.split(':')
            #            print_2_file[-1].append(spans[int(pair[0])] + ' -> ' + variants[int(pair[1])])
                        print(spans[int(pair[0])], ' -> ', variants[int(pair[1])])
            if not find_answers:
                sending = "answers not found"
                write_error(
                    theme,
                    question,
                    self.path,
                    sending,
                    cur_number=cur_number,
                    spans=spans,
                    spans_compare=spans_compare,
                    variants=variants,
                    variants_compare=variants_compare)
            #    print_2_file.append([sending])
                print(sending)

            elif cur_number[0] == '':
                sending = "question not found"
                write_error(
                    theme,
                    question,
                    self.path,
                    sending,
                    cur_number=cur_number,
                    spans=spans,
                    spans_compare=spans_compare,
                    variants=variants,
                    variants_compare=variants_compare)

            # print_2_file.append(cur_number)
            # for i in range(len(answers)):
            #     print_2_file.append(list(map(str, variants_compare[i])))
            #     print_2_file.append(list(map(str, spans_compare[i])))
            #     print_2_file.append(answers[i])
            # print_2_file.append(variants)
            # print_2_file.append(['undefined: ', sending])
            print(cur_number)
            print(variants_compare)
            print(spans_compare)
            print(answers)
            print(variants)
            print('undefined: ', sending)
            write_log(
                theme,
                question,
                self.path,
                sending,
                cur_number=cur_number,
                spans=spans,
                spans_compare=spans_compare,
                variants=variants,
                variants_compare=variants_compare)
            self.wfile.write(bytes(sending, encoding='utf-8'))
# Text
        elif self.path == '/text':
            rubbish = ['Ответ необходимо указать заглавной буквой русского алфавита, пользуясь схемой.',
                       'Ответ необходимо указать заглавной буквой русского алфавита, пользуясь следующей схемой:',
                       'Установите правильность каждого из утверждения и их связь между собой.']
            theme = req[0]
            question = req[1].replace(rubbish[0], '').replace(rubbish[1], '').replace(rubbish[2], '').strip()
            print('question: ', question)
            answers = []
            que_number = -1
            cur_number = ['']
            sending = 'Not_found'
            find_answers = False
            # find and check all questions and variants
            with open(theme + '.txt', 'r', encoding='utf-8') as f:
                for line in f:
                    if '#' in line:
                        # include number and verify
                        que_number = line
                    elif find(question, line):
                        cur_number.append(que_number)
                        if '' in cur_number:
                            cur_number.remove('')
                    elif cur_number[-1] == que_number:
                        if line.startswith('+'):
                            answers.append([dict[line[1:-1]]])

            for i in range(len(cur_number)):
                if len(answers) > 0:
                    find_answers = True
                    if ' 1' in cur_number[i] or ' 0' in cur_number[i]:
                        num, verify = cur_number[i][1:-1].split(' ')
                    else:
                        num = cur_number[i][1:-1]
                        verify = ''
                    sending = num + '\n' + verify + '\n' + answers[i][0]
                    if len(answers[i]) > 1:
                        sending = "too many answers!"
                        write_error(
                            theme,
                            question,
                            self.path,
                            sending,
                            cur_number=cur_number)
                        print(sending)
                    print('true: ', answers[i])

            if cur_number[0] == '':
                sending = "question not found"
                write_error(
                    theme,
                    question,
                    self.path,
                    sending,
                    cur_number=cur_number)

            #print_2_file.append(cur_number)
            # for ans in answers:
            #     print_2_file.append(ans)
            #print_2_file.append(['text: ', sending])
            print(cur_number)
            print(answers)
            print('text: ', sending)
            write_log(
                theme,
                question,
                self.path,
                sending,
                cur_number=cur_number)
            self.wfile.write(bytes(sending, encoding='utf-8'))
# End
        elif self.path == '/end':
            theme = req[0]
            answers = req[1].split('__')
            log = req[1].split('__')
            all_answers = req[2].split('__')
            print(req[3])
            try:
                count_mistakes = int(req[3][0])
            except ValueError:
                count_mistakes = -666

            with open(theme + '.txt', 'r', encoding='utf-8') as f:
                lines = f.readlines()
            for i in range(len(lines)):
                if count_mistakes == 0:
                    for answer in answers:
                        num = answer.split(separator)[0]
                        if ('#' + str(num) + '\n') in lines[i] or ('#' + str(num) + ' 0\n') in lines[i]:
                            lines[i] = '#' + str(num) + ' 1\n'
                else:
                    for answer in all_answers:
                        if answer not in errors:
                            num = answer.split(separator)[0]
                            if ('#' + str(num) + '\n') in lines[i]:
                                lines[i] = '#' + str(num) + ' 0\n'

# its old yet
#             if count_mistakes == 0:
#                 with open(theme + '.txt', 'r', encoding='utf-8') as f:
#                     lines = f.readlines()
#                 for i in range(len(lines)):
#                     for answer in answers:
#                         num = answer.split(separator)[0]
# # here maybe error
#                         if ('#' + str(num) + '\n') in lines[i]:
#                             lines[i] = '#' + str(num) + ' 1\n'
#             #                print_2_file.append(['question verified!', ' '.join(answers)])
#                             print('question verified!', answers)
#                             answers.remove(answer)
#
#
            with open(theme + '.txt', 'w', encoding='utf-8') as f:
                f.writelines(lines)
            #print_2_file.append(' '.join(req))

            print(req)
            write_log(
                theme,
                "count mistakes: " + req[3] + '\n' + req[4],
                self.path + '\n' + count_verify(theme),
                '  '.join(log) + '\n' + '  '.join(all_answers))
            self.wfile.write(bytes("End", encoding='utf-8'))

        else:
            print(req)
            self.wfile.write(bytes("1\n2\nSuccess!", encoding='utf-8'))


def write_log(theme, question, _type_, sending, **keys):
    with open(datetime.datetime.today().strftime("%Y_%m_%d_") + 'plugin.log', 'a+', encoding='utf-8') as f:
        f.seek(0)
        count = 1
        for line in f:
            if '##' in line:
                count += 1
        f.write('\n##' + str(count) + '\n')
        f.write('path: ' + _type_ + '\n')
        f.write(theme + '\n')
        f.write(question + '\n')
        if _type_ == '/radio' or _type_ == '/checkbox' or _type_ == '/undefined':
            _cur_number_ = keys['cur_number']
            print('cur_num: ', _cur_number_)
            for num in _cur_number_:
                f.write(num.replace('\n', '').ljust(7, ' '))
            f.write('\n')
            if _type_ == '/undefined':
                _spans_ = keys['spans']
                _spans_compare_ = keys['spans_compare']
                print('spans:\n', _spans_)
                print(_spans_compare_)
                for i in range(len(_spans_)):  #
                    for j in range(len(_spans_compare_)):  #
                        f.write(str(_spans_compare_[j][i]).ljust(7, ' '))  #
                    f.write(_spans_[i] + '\n')  #
                f.write('\n')  #
            _variants_ = keys['variants']
            _variants_compare_ = keys['variants_compare']
            print('variants:\n', _variants_)
            print(_variants_compare_)
            for i in range(len(_variants_)):
                for j in range(len(_variants_compare_)):
                    f.write(str(_variants_compare_[j][i]).ljust(7, ' '))
                f.write(_variants_[i] + '\n')
        f.write(sending + '\n\n')


def search_answer(theme, question, _type_, **key):
    variants_compare = []
    spans_compare = []  #
    answers = []
    que_number = -1
    cur_number = ['']
    sending = 'Not_found'
    find_answers = False
    with open(theme + '.txt', 'r', encoding='utf-8') as f:
        for line in f:
            if '#' in line:
                # include number and verify
                que_number = line
            elif find(question, line):
                cur_number.append(que_number)
                if _type_ == '/radio' or _type_ == '/checkbox' or _type_ == '/undefined':
                    _variants_ = key['variants']
                    variants_compare.append([False] * len(_variants_))
                    if _type_ == '/undefined':
                        _spans_ = key['spans']
                        spans_compare.append([False] * len(_spans_))  #
                if '' in cur_number:
                    cur_number.remove('')
                answers.append([])
            elif cur_number[-1] == que_number:
                if _type_ == '/radio' or _type_ == '/checkbox':
                    for i in range(len(_variants_)):
                        if find(_variants_[i], line):
                            variants_compare[-1][i] = True
                            if line.startswith('+'):
                                answers[-1].append(str(i))
                elif _type_ == '/undefined':
                    for i in range(len(_spans_)):  #
                        if find(_spans_[i], line):  #
                            spans_compare[-1][i] = True  #
                    for i in range(len(_variants_)):
                        if find(_variants_[i], line):
                            variants_compare[-1][i] = True
                            for j in range(len(_spans_)):  #
                                if find(_spans_[j], line):  #
                                    answers[-1].append(str(j) + ':' + str(i))  #
                elif _type_ == '/text':
                    if line.startswith('+'):
                        answers.append([dict[line[1:-1]]])

    for i in range(len(cur_number)):
        if False not in variants_compare[i] and False not in spans_compare[i]:
            find_answers = True
            sending = cur_number[i][1:] + '\n' + separator.join(answers[i])
            print('true: ')
            for pairs in answers[i]:
                pair = pairs.split(':')
                print(_spans_[int(pair[0])], ' -> ', _variants_[int(pair[1])])
    if not find_answers:
        sending = "answers not found"
        write_error(
            theme,
            question,
            _type_,
            sending,
            cur_number=cur_number,
            variants=_variants_,
            variants_compare=variants_compare)
        print("answers not found")
    elif cur_number[0] == '':
        sending = "question not found"
        write_error(
            theme,
            question,
            _type_,
            sending,
            cur_number=cur_number,
            variants=_variants_,
            variants_compare=variants_compare)
        print("question not found")


def error_exist_yet(theme, question):
    er_num = 0
    with open(theme + '_errors.txt', 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('##'):
                er_num = int(line[2:].split(' ')[0]) + 1
            if question in line:
                f.close()
                return True, -1
    return False, er_num


def write_error(theme, question, _type_, error_string, **keys):
    error_exist_yet_flag, er_num = error_exist_yet(theme, question)
    print("Err exist, number, error_string and type: ", error_exist_yet_flag, er_num, error_string, _type_)
    if not error_exist_yet_flag:
        with open(theme + '_errors.txt', 'a', encoding='utf-8') as f:
            f.write('##' + str(er_num) + '\n')
            f.write(error_string + "\n")
            f.write(question + '\n')
            if error_string == 'answers not found' or 'too many answers!':
                if _type_ == '/radio' or _type_ == '/checkbox' or _type_ == '/undefined':
                    _cur_number_ = keys['cur_number']
                    print('cur_num: ', _cur_number_)
                    for num in _cur_number_:
                        f.write(num.replace('\n', '').ljust(7, ' ') )
                    f.write('   ' + _type_ + '\n')
                    if _type_ == '/undefined':
                        _spans_ = keys['spans']
                        _spans_compare_ = keys['spans_compare']
                        print('spans:\n', _spans_)
                        print(_spans_compare_)
                        for i in range(len(_spans_)):  #
                            for j in range(len(_spans_compare_)):  #
                                f.write(str(_spans_compare_[j][i]).ljust(7, ' '))  #
                            f.write(_spans_[i] + '\n')  #
                        f.write('\n')  #
                    _variants_ = keys['variants']
                    _variants_compare_ = keys['variants_compare']
                    print('variants:\n', _variants_)
                    print(_variants_compare_)
                    for i in range(len(_variants_)):
                        for j in range(len(_variants_compare_)):
                            f.write(str(_variants_compare_[j][i]).ljust(7, ' '))
                        f.write(_variants_[i] + '\n')
            f.write('\n\n')


def search_ans(theme, que, type):
    ans = []
    try:
        with open(theme + '.txt', encoding='utf-8') as f:
            for line in f:
                if find(que, line):
                    if type == 'radio-check':
                        while line != '\n':
                            line = f.readline()
                            if line.startswith('+'):
                                ans.append(line[1:len(line) - 1])
                    elif type == 'sopost':
                        while line != '\n':
                            line = f.readline()
                            ans.append(line[:len(line) - 1])
                    elif type == 'table':
                        while line != '\n' and line != '':
                            line = f.readline()
                            if line.startswith('+'):
                                ans.append(dict[line[1:len(line) - 1]])
    except FileNotFoundError:
        print('FileNotFoundError: ' + theme)

    return ans


def find_und(str1, str2):
    return change(str1) in change(str2)


def find(str1, str2):
    return change(str1) == change(str2)


def change(string):
    return string.replace(':', '.') \
        .replace('ё', 'е') \
        .replace('(', '') \
        .replace(')', '') \
        .replace(' ', ' ') \
        .replace('  ', ' ') \
        .replace('+', '') \
        .replace('\n', '') \
        .replace('ое', 'ого') \
        .replace('ие', 'ия') \
        .replace('-', '')


def count_verify(name):
    count_ver = 0
    count_call = 0
    count_all = 0
    with open(name + '.txt', 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('#'):
                count_all += 1
                if ' 1\n' in line:
                    count_ver += 1
                    count_call += 1
                elif ' 0' in line:
                    count_call += 1
    answer = 'number of verified: ' + str(count_ver) + '\n' + \
             'number of call: ' + str(count_call) + ' / ' + str(count_all) + '\n' + \
             'number of errors: ' + str(count_errors(name))
    return answer


def count_errors(theme):
    er_num = 0
    with open(theme + '_errors.txt', 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('##'):
                er_num += 1
    return er_num


serv = HTTPServer(("localhost", 8080), HttpProcessor)
serv.serve_forever()


def clear_verified(name):
    with open(name + '.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        print(lines)
        new_lines = []
        for line in lines:
            if line.startswith('#') and (' 1\n' in line or ' 0\n' in line):
                new_lines.append(line.split(' ')[0] + '\n')
            else:
                new_lines.append(line)
    with open(name + '.txt', 'w', encoding='utf-8') as f:
        f.seek(0)
        print(new_lines)
        f.writelines(new_lines)


def example():
    count_radio = 0
    count_checkbox = 0
    count_undef = 0
    count_text = 0
    count_end = 0
    count_question = 10
    with open(datetime.datetime.today().strftime("%Y_%m_%d_") + 'plugin.log', 'r', encoding='utf-8') as f:
        for line in f:
            if 'path:' in line:
                if '/radio' in line:
                    count_radio += 1
                if '/checkbox' in line:
                    count_checkbox += 1
                if '/undefined' in line:
                    count_undef += 1
                if '/text' in line:
                    count_text += 1
                if '/end' in line:
                    count_end += 1
        print('radio: ', count_radio, '\t(', count_radio/count_end/count_question*100, ' %)')
        print('checkbox: ', count_checkbox, '\t(', count_checkbox/count_end/count_question*100, ' %)')
        print('undef: ', count_undef, '\t(', count_undef/count_end/count_question*100, ' %)')
        print('text: ', count_text, '\t(', count_text/count_end/count_question*100, ' %)')

