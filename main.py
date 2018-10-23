#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import re
import pyquery
import cv2 as cv


def parse_questions(data):
    j = pyquery.PyQuery(data)
    question_types = []
    for d in j('form[name="form1"] > table > tr > td > table > tr > td > table[cellpadding="0"]').items():
        tmp = re.findall(r'、(.*?)\(.*?共.*?([0-9]+).*?道', d.text(), re.S)[0]
        question_types.append({'name': tmp[0], 'num': tmp[1], 'src': d, 'questions': []})
    for question_type in question_types:
        if question_type['name'] == '单项选择题':
            for q_src in question_type['src'].find('table').items():
                id = re.findall(r'name="answer_(.*?)"', q_src.html())[0]
                q = {'id': id, 'q': '', 'a': []}
                n = 0
                for t in q_src.find('tr').items():
                    if n == 0:
                        q['q'] = re.findall(r'\.(.*)', t.text())
                    else:
                        print(t.text())
                        print('-----')
                        text = t.text().replace('\n', ' ')
                        print(text)
                        print('-----')
                        if re.search(r'\(.*?\) (.*)', t.text(), re.S):
                            q['a'].append({'v': re.search(r'value="(.*?)"', t.html(), re.S).group(1),
                                           'k': re.search(r'\(.*?\) (.*)', text).group(1)})
                        else:
                            q['a'].append({'v': ' ',
                                           'k': ' '})
                    n = n + 1
                question_type['questions'].append(q)
        elif question_type['name'] == '判断题':
            for q_src in question_type['src'].find('table').items():
                id = re.findall(r'name="answer_(.*?)"', q_src.html())[0]
                q = {'id': id}
                question_type['questions'].append(q)
        elif question_type['name'] == '客观题':
            pass
        elif question_type['name'] == '不定项选择题':
            for q_src in question_type['src'].find('table').items():
                id = re.findall(r'name="answer_(.*?)_.*?"', q_src.html())[0]
                q = {'id': id, 'q': '', 'a': []}
                n = 0
                for t in q_src.find('tr').items():
                    if n == 0:
                        q['q'] = re.findall(r'\.(.*)', t.text())[0]
                    else:
                        q['a'].append({'v': re.search(r'value="answer_.*?_(.*?)"', t.html(), re.S).group(1),
                                       'k': re.search(r'\(.*?\) (.*)', t.text()).group(1)})
                    n = n + 1
                question_type['questions'].append(q)
        elif question_type['name'] == '阅读理解、完形填空题':
            q_t = None
            for q_src in question_type['src'].find('table').items():
                for a_src in q_src.find("tr").items():
                    if a_src.html():
                        tmp = re.search(r'answer_(.*?)".*?value="(.*?)".*?>\(.*?\)(.*?)[\n\t]', a_src.html(), re.S)
                        if tmp:
                            id = tmp.group(1)
                            if q_t is None:
                                q_t = {'id': id, 'o': []}
                                question_type['questions'].append(q_t)
                            if q_t['id'] != id:
                                q_t = {'id': id, 'o': []}
                                question_type['questions'].append(q_t)
                            q_t['o'].append({'v': tmp.group(2), 'k': tmp.group(3)})
    return question_types


def parse_answer(data):
    j = pyquery.PyQuery(data)
    answer_types = []
    for d in j('table[align="center"] > tr > td > table > tr > td > table > tr > td >table').items():
        tmp = re.search(r'、(.*?)\(.*?共(.*?)道', d.text(), re.S)
        if tmp:
            answer_types.append({'name': tmp.group(1), 'num': tmp.group(2), 'src': d, 'answers': []})
    for answer_type in answer_types:
        if answer_type['name'] == '单项选择题':
            for a_src in answer_type['src'].find('table').items():
                content = a_src.html()
                a_opt_code = re.search(r'正确答案：</font>(.*?)<', content, re.S).group(1)
                a_opt = re.search(r'\(' + a_opt_code + '\)(.*?)</td', content, re.S)
                answer_type['answers'].append(pyquery.PyQuery('<i>' + a_opt.group(1) + '</i>').text())
        elif answer_type['name'] == '判断题':
            for a_src in answer_type['src'].find('table').items():
                content = a_src.html()
                a_opt_code = re.search(r'正确答案：</font>(.*?)<', content, re.S).group(1)
                answer_type['answers'].append(a_opt_code)
        elif answer_type['name'] == '不定项选择题':
            for a_src in answer_type['src'].find('table').items():
                content = a_src.html()
                a_opt_code = re.search(r'正确答案：</font>(.*?)<', content, re.S).group(1)
                a_t = []
                for c in a_opt_code.split(' '):
                    a_opt = re.search(r'\(' + c + '\)(.*?)</td', content, re.S)
                    a_t.append(pyquery.PyQuery('<i>' + a_opt.group(1) + '</i>').text())
                answer_type['answers'].append(a_t)
        elif answer_type['name'] == '阅读理解、完形填空题':
            for a_src in answer_type['src'].find('table').items():
                v = {}
                for a in a_src.find('tr').items():
                    tmp = re.search(r'\(([A-Z])\)(.*?)[\n\t]', str(a.html()).replace('\xa0', ''), re.S)
                    if tmp:
                        v[tmp.group(1)] = tmp.group(2)
                    else:
                        tmp = re.search(r'正确答案：</font>(.*?)<', str(a.html()).replace('\xa0', ''), re.S)
                        if tmp:
                            answer_type['answers'].append(v[tmp.group(1)])
                            v = {}
    return answer_types


def main():
    headers_auth = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.8",
        "Connection": "keep-alive",
        "Cache-Control": "max-age=0"
    }
    headers_study = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.8",
        "Connection": "keep-alive",
        "Cache-Control": "max-age=0"
    }
    headers_cx = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.8",
        "Connection": "keep-alive",
        "Cache-Control": "max-age=0"
    }

    first_load = True
    first_code = ''

    response = requests.get("http://auth.xnjd.cn/login", headers=headers_auth)
    if response.status_code == 404:
        print('网站维护中...')
        return
    jsession_auth = re.search(r'JSESSIONID=(.*?);', str(response.headers)).group(1)
    headers_auth['Cookie'] = "JSESSIONID=" + jsession_auth + ";"
    content = response.text
    lt = re.search(r'name="lt" value="(.*?)"', content).group(1)
    execution = re.search(r'name="execution" value="(.*?)"', content).group(1)
    eventId = re.search(r'name="_eventId" value="(.*?)"', content).group(1)

    username = ''
    password = ''

    post_data = {
        "username": username,
        "password": password,
        "lt": lt,
        "execution": execution,
        "_eventId": eventId,
        "cassubmit.x": "27",
        "cassubmit.y": "24",
        "cassubmit": "%E7%99%BB+%E5%BD%95"
    }
    response = requests.post("http://auth.xnjd.cn/login", data=post_data, headers=headers_auth)
    castgc = re.search(r'CASTGC=(.*?);', str(response.headers)).group(1)
    headers_auth['Cookie'] = 'JSESSIONID=' + jsession_auth + "; CASTGC=" + castgc
    result = re.search(r'<div id="msg" class="(.*?)">', response.text).group(1)
    if result == 'success':
        print('登录成功')
    else:
        print("账号密码错误")
        return
    response = requests.get('http://auth.xnjd.cn/login?service=http%3A%2F%2Fstudy.xnjd.cn%2FIndex_index.action',
                            headers=headers_auth, allow_redirects=False)
    response = requests.get(response.headers['Location'], headers=headers_auth, allow_redirects=False)
    headers_study['Cookie'] = 'JSESSIONID=' + re.search(r'ID=(.*?);', str(response.headers)).group(1)
    response = requests.get('http://study.xnjd.cn/Index_index.action', headers=headers_study, allow_redirects=False)
    name = re.search(r'<li class="first"><img src="/images/person.png" alt="person icon"/><a href="#">(.*?)</a></li>',
                     response.text).group(1)
    print('姓名:' + name)
    table = re.search(r'<table class="bluetable">(.*?)</table>', response.text, re.S).group(1)
    courses = re.findall(r'<tr><td>.*?</td><td>(.*?)</td><td>.*?</td><td>.*?</td>.*?href=".*?courseId=(.*?)"', table,
                         re.S)
    print('课程数:' + str(len(courses)))
    for i in range(0, len(courses)):
        print(str(i + 1) + '.' + courses[i][0] + ' ' + courses[i][1])
    response = requests.get('http://cs.xnjd.cn/course/exercise/Student_list.action?courseId=' + courses[0][1],
                            allow_redirects=False)
    headers_cx['Cookie'] = 'JSESSIONID=' + re.search(r'ID=(.*?);', str(response.headers)).group(1)
    response = requests.get(response.headers['Location'], headers=headers_auth, allow_redirects=False)
    response = requests.get(response.headers['Location'], headers=headers_cx, allow_redirects=False)
    response = requests.get(response.headers['Location'], headers=headers_cx, allow_redirects=False)
    for i in range(0, len(courses)):
        courseID = courses[i][1]
        response = requests.get('http://cs.xnjd.cn/course/exercise/Student_list.action?courseId=' + courseID,
                                headers=headers_cx)
        homeworks = re.findall(r'<td align=left>(.*?)</td>.*?homeworkId=(.*?)"', response.text, re.S)
        for homework in homeworks:
            homeworkID = homework[1]
            response = requests.get(
                'http://cs.xnjd.cn/course/exercise/Student_doIt.action?'
                'courseId=' + courseID +
                '&homeworkId=' + homeworkID,
                headers=headers_cx)
            content = response.text
            if re.search(r'(操作成功！客观题已经全部正确)', content, re.S):
                print(homework[0] + ':完成')
                continue
            all_ex = re.search(r'allExerciseId" value=(.*?)>', content, re.S).group(1)
            student_id = re.search(r'glo_student_id" value="(.*?)"', content, re.S).group(1)
            all_Type = re.search(r'glo_allType" value="(.*?)"', content, re.S).group(1)
            course_url = re.search(r'course_url" value="(.*?)"', content, re.S).group(1)
            class_code = re.search(r'class_code" value="(.*?)"', content, re.S).group(1)
            center_code = re.search(r'center_code" value="(.*?)"', content, re.S).group(1)
            content = content.replace("&nbsp;", " ").replace("\r", "")
            print(content)
            questions_data = parse_questions(content)
            print(questions_data)
            # 获取验证码
            if first_load:
                response = requests.get(
                    'http://cs.xnjd.cn/course/exercise/Student_validationCode.action?courseId=' + courseID,
                    headers=headers_cx, stream=True)
                with open('demo.jpg', 'wb') as fd:
                    for chunk in response.iter_content(128):
                        fd.write(chunk)
                cv.namedWindow('image')
                cv.imshow('image', cv.imread('demo.jpg'))
                cv.waitKey(0)
                cv.destroyWindow('image')
                # cv.destroyAllWindows()
                first_code = input("请输入验证码:")
                first_load = False
            post_data = {
                'method': 'submithomework',
                'all_ex': all_ex,
                'course_code': courseID,
                'homework_id': homeworkID,
                'student_id': student_id,
                'all_type': all_Type,
                'center_code': '',
                'class_code': '',
                'course_url': course_url,
                'qulifyCode': first_code,
                'timestamp': 'Wed Oct 25 2017 15:32:14 GMT 0800 (中国标准时间)',
                'lefttime': '|0',
                'repeat_type': '2',
                'homework_type': '%E8%AE%A1%E5%AE%8C%E6%88%90%E9%A2%98%E7%9B%AE%E6%95%B0'
            }
            print(post_data)
            # 提交数据
            response = requests.post('http://cs.xnjd.cn/course/exercise/Ajax_stusavetmp.action', data=post_data,
                                     headers=headers_cx)
            # 获取答案
            response = requests.get(
                'http://cs.xnjd.cn/course/exercise/Student_history.action?courseId=' + courseID + '&homeworkId=' + homeworkID,
                headers=headers_cx)
            answers_data = parse_answer(response.text.replace("&nbsp;", " ").replace("\r", ""))
            result = match(questions_data, answers_data)
            save_post_data = {
                'method': 'savetmpontime',
                'all_ex': all_ex,
                'course_code': courseID,
                'homework_id': homeworkID,
                'student_id': student_id,
                'all_type': all_Type,
                'center_code': center_code,
                'class_code': class_code,
                'course_url': course_url,
                'qulifyCode': '',
                'timestamp': 'Wed Oct 25 2017 15:32:14 GMT 0800 (中国标准时间)',
                'lefttime': '0|0',
                'repeat_type': '2',
                'homework_type': '%E8%AE%A1%E5%AE%8C%E6%88%90%E9%A2%98%E7%9B%AE%E6%95%B0'
            }
            for r in result:
                save_post_data[r] = result
            print(save_post_data)
            # 提交数据
            # 保存临时答案
            response = requests.post('http://cs.xnjd.cn/course/exercise/Ajax_stusavetmp.action', data=save_post_data,
                                     headers=headers_cx)
            print(response.text)
            submit_post_data = {
                'method': 'submithomework',
                'all_ex': all_ex,
                'course_code': courseID,
                'homework_id': homeworkID,
                'student_id': student_id,
                'all_type': all_Type,
                'center_code': center_code,
                'class_code': class_code,
                'course_url': course_url,
                'qulifyCode': first_code,
                'timestamp': 'Wed Oct 25 2017 15:32:14 GMT 0800 (中国标准时间)',
                'lefttime': '0|0',
                'repeat_type': '2',
                'homework_type': '%E8%AE%A1%E5%AE%8C%E6%88%90%E9%A2%98%E7%9B%AE%E6%95%B0'
            }
            for r in result:
                submit_post_data[r] = result[r]
            print(submit_post_data)
            # 提交数据
            response = requests.post('http://cs.xnjd.cn/course/exercise/Ajax_stusavetmp.action', data=submit_post_data,
                                     headers=headers_cx)
            print(response.text)
            response = requests.get(
                'http://cs.xnjd.cn/course/exercise/Student_history.action?courseId=' + courseID + '&homeworkId=' + homeworkID,
                headers=headers_cx)

            print('结束')


def get_answer_type(name, answer_types):
    for answer_type in answer_types:
        if answer_type['name'] == name:
            return answer_type


def match(q_types, a_types):
    print(q_types)
    print(a_types)
    result = {}
    for q_type in q_types:
        if q_type['name'] == '单项选择题':
            a_type = get_answer_type('单项选择题', a_types)
            for q_num in range(0, len(q_type['questions'])):
                k = a_type['answers'][q_num]
                for opt in q_type['questions'][q_num]['a']:
                    if opt['k'] == k:
                        result['answer_' + str(q_type['questions'][q_num]['id'])] = opt['v']
        elif q_type['name'] == '不定项选择题':
            a_type = get_answer_type('不定项选择题', a_types)
            for q_num in range(0, len(q_type['questions'])):
                q_ = q_type['questions'][q_num]
                qid = 'answer_' + q_['id']
                r = ''
                for a_opt in a_type['answers'][q_num]:
                    for opt in q_['a']:
                        if opt['k'] == a_opt:
                            r = r + '|' + opt['v']
                result[qid] = r[1:]
        elif q_type['name'] == '判断题':
            a_type = get_answer_type('判断题', a_types)
            for q_num in range(0, len(q_type['questions'])):
                qid = 'answer_' + q_type['questions'][q_num]['id']
                r = a_type['answers'][q_num]
                if r == '说法错误':
                    result[qid] = 0
                else:
                    result[qid] = 1
        elif q_type['name'] == '阅读理解、完形填空题':
            a_type = get_answer_type('阅读理解、完形填空题', a_types)
            for q_num in range(0, len(q_type['questions'])):
                k = a_type['answers'][q_num]
                for opt in q_type['questions'][q_num]['o']:
                    if opt['k'] == k:
                        qid = 'answer_' + re.search(r'^(.*)_', q_type['questions'][q_num]['id']).group(1)
                        if qid not in result:
                            result[qid] = opt['v']
                        else:
                            result[qid] = result[qid] + '|' + opt['v']
    print(result)
    return result


if __name__ == '__main__':
    # match()
    main()
