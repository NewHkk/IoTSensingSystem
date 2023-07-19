import json
import re
from _datetime import datetime
import pytz
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail

from pyecharts import options as opts
from pyecharts.charts import Gauge, Line, Bar
from rest_framework.views import APIView

from .admin import NodeMessageResource
from .models import Node, NodeMessage

import requests

# nodes = [
#     {'id': 1, 'name': '西北角'},
#     {'id': 2, 'name': '东南角 '},
#     {'id': 3, 'name': '中央'},
# ]
# node_messages = [
#     {"id": "1", "battery_level": "80.1", "temperature": "37.5", "humidity": "77.3", "illumination": "33"}
# ]
zh_dict = {
    'battery_level': '电量',
    'temperature': '温度',
    'humidity': '湿度',
    'illumination': '光照',
    'mq2PPM': '可燃气体浓度',
    'is_fired': "明火",
}
# 写入日志
import logging

today = datetime.today().strftime("%Y_%m_%d")
# 配置日志输出到文件
logging.basicConfig(filename=f'logfiles/{today}.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


@csrf_exempt
def offline(request, node_id):
    node = Node.objects.get(id=node_id)
    node_message = node.nodemessage_set.first()  # 获得（最新数据）
    if node_message is None:
        return HttpResponse(999)
    time_now = datetime.now()
    # 将当前时间转换为UTC时间
    utc_timezone = pytz.timezone('UTC')
    utc_time_now = time_now.astimezone(utc_timezone)
    time_difference = utc_time_now - node_message.created
    seconds = time_difference.total_seconds()
    return HttpResponse(seconds)


last_send = None


@csrf_exempt
def send_email(request):
    """上下线提醒：发送邮件并写入日志"""
    if request.method == 'POST':
        print("request.POST", request.POST)
        node_id = request.POST.get('node_id')
        message = request.POST.get('message')
        print(f"node_id={node_id},message={message}\n\n")
        time_now = datetime.now()
        success = send_mail(
            subject=f"节点{node_id}信息",
            message=f"节点{node_id}在{time_now}:{message}",
            from_email="龙芯",
            recipient_list=['xxxx'],
            fail_silently=False,
        )
        print(f"发送邮件{success}\n\n")

        # 写入日志
        logging.info(f"节点{node_id}在{time_now}:{message}")

        return HttpResponse("send email")


def home(request):
    nodes = Node.objects.all().reverse()

    # beijing_timezone = pytz.timezone('Asia/Shanghai')
    # for node in nodes:
    #     node_message = node.nodemessage_set.first()  # 获得（最新数据）
    #     time_now = datetime.now()
    #     # 将当前时间转换为UTC时间
    #     utc_timezone = pytz.timezone('UTC')
    #     utc_time_now = time_now.astimezone(utc_timezone)
    #     time_difference = utc_time_now - node_message.created
    #     seconds = time_difference.seconds
    #     # "%Y-%m-%d %H:%M:%S"

    context = {'nodes': nodes}
    return render(request, 'base/home.html', context)


def loginPage(request):
    page = 'login'
    if request.user.is_authenticated:
        print('user.is_authenticated')
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')
        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, 'User does not exits')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)  # 成功登录
            return redirect('home')
        else:
            messages.error(request, 'Username OR password does not exist.')
    context = {'page': page}
    return render(request, 'base/login.html', context)


def logoutUser(request):
    logout(request)
    return redirect('login')


@csrf_exempt
def get_save_msg(request):
    '''接受消息并保存'''

    if request.method == 'POST':
        print({
            'path': request.path,
            'method': request.method,
            'get_data': request.GET,  # 包含了所有以?xxx=xxx的方式上传上来的参数
            'post_data': request.POST,  # 包含了所有以POST方式上传上来的参数
            "body": request.body,
        })

        # receive_data = json.loads(json.dumps(request.POST))  # for simulated POST in `test_makepost`

        # r eceive_data = json.loads(request.body.decode())  # for real
        # print(receive_data)

        preprocess = re.findall(r'{.*?}', str(request.body))[0]
        receive_data = json.loads(eval("'{}'".format(preprocess)))
        # 发送post到服务器
        try:
            requests.post(url='http://101.33.245.249:6060/getpost/',
                          data=receive_data,
                          )
        except Exception as e:
            print("发送数据到服务器失败\n", e)

        node, created = Node.objects.get_or_create(id=int(receive_data['node']))
        NodeMessage.objects.create(
            node=node,
            battery_level=receive_data.get("battery_level", -1),
            temperature=receive_data.get("temperature", -1),
            humidity=receive_data.get("humidity", -1),
            illumination=receive_data.get("illumination", -1),
            mq2PPM=receive_data.get("mq2PPM", -1)
        )
        # print(request.POST)
    return JsonResponse({"msg": "success"})


@csrf_exempt
def test_makepost(request):
    return render(request, 'base/test_makepost.html', )


#################
# pyecharts start
#################
def response_as_json(data):
    json_str = json.dumps(data)
    response = HttpResponse(
        json_str,
        content_type="application/json",
    )
    response["Access-Control-Allow-Origin"] = "*"
    return response


def json_response(data, code=200):
    data = {
        "code": code,
        "msg": "success",
        "data": data,
    }
    return response_as_json(data)


def json_error(error_string="error", code=500, **kwargs):
    data = {
        "code": code,
        "msg": error_string,
        "data": {}
    }
    data.update(kwargs)
    return response_as_json(data)


JsonResponse = json_response
JsonError = json_error


def gauge_base(pk=1, dataname="battery_level") -> Gauge:
    # 获取node_id关联的消息
    node = Node.objects.get(id=pk)
    node_messages = node.nodemessage_set.first()  # 获得第一条数据（最新数据）
    # print(f'room_messages={node_messages}')
    formatter_dict = {
        'temperature': '{value}℃',
        'illumination': '{value}',
        'mq2PPM': '{value}',
        'is_fired': '{value}',
    }
    max_v = {'mq2PPM': 20000,
             'default': 100}
    my_color = [(0.3, "#67e0e3"), (0.7, "#37a2da"), (1, "#fd666d")]
    if dataname == 'battery_level':
        my_color = [(0.3, "#fd666d"), (0.7, "#37a2da"), (1, "#67e0e3")]
    c = (
        Gauge()
        .add(
            zh_dict[dataname],
            [(zh_dict[dataname], getattr(node_messages, dataname))],  # 设置数据
            axisline_opts=opts.AxisLineOpts(
                linestyle_opts=opts.LineStyleOpts(
                    color=my_color, width=30
                )
            ),
            detail_label_opts=opts.LabelOpts(font_size=20, color='#333',
                                             formatter=formatter_dict.get(dataname, "{value}%")),
            max_=max_v.get(dataname, 100),

        )
        .set_global_opts(
            # title_opts=opts.TitleOpts(title=dataname),
            legend_opts=opts.LegendOpts(is_show=False),

        )
        .dump_options_with_quotes()
    )

    if dataname == "is_fired":
        if getattr(node_messages, dataname):
            list1 = [1]
        else:
            list1 = [0]
        c = (
            Bar()
            .add_xaxis(["有明火"])
            .add_yaxis('火', list1, itemstyle_opts=opts.ItemStyleOpts(color="#DC143C"), )

            .dump_options_with_quotes()

        )
    return c


# time charts
def line_base(node_id=1, dataname="battery_level"):
    # 获取node_id关联的消息
    node = Node.objects.get(id=node_id)
    node_messages = node.nodemessage_set.all()[:50].values()  # 获得前n条数据（最新数据）

    beijing_timezone = pytz.timezone('Asia/Shanghai')
    data_list = [x[dataname] for x in node_messages]
    # "%Y-%m-%d %H:%M:%S"
    time_list = [x['created'].astimezone(beijing_timezone).strftime("%H:%M:%S") for x in node_messages]
    time_list.reverse()
    data_list.reverse()
    # print(time_list)
    line = (
        Line()
        .add_xaxis(time_list)
        .add_yaxis(zh_dict[dataname], data_list, label_opts=opts.LabelOpts(is_show=False))
        .set_global_opts(
            # title_opts=opts.TitleOpts(title="Grid-Line", pos_right="5%"),
            legend_opts=opts.LegendOpts(pos_right="10%"),
        )
        .dump_options_with_quotes()
    )
    return line


class GaugeView(APIView):
    def get(self, request, pk=1, dataname="battery_level", ):
        return JsonResponse(json.loads(gauge_base(pk, dataname)))


class LineView(APIView):
    def get(self, request, node_id=1, dataname="battery_level"):
        # print(f'node_id={node_id}, dataname={dataname}\n\n')
        return JsonResponse(json.loads(line_base(node_id, dataname)))


class IndexView(APIView):
    def get(self, request, *args, **kwargs):
        return HttpResponse(content=open("./base/templates/base/node_charts.html").read())


def nodechartsPage(request, pk):
    node = Node.objects.get(id=pk)

    context = {'node': node}
    return render(request, 'base/node_charts.html', context)


# 节点某个类型的数据随时间变化的曲线
def nodeLinechartsPage(request, node_id, datatype):
    # print("nodeLinechartsPage..............")
    node = Node.objects.get(id=node_id)
    context = {'node': node, 'datatype': datatype}
    return render(request, 'base/node_linechart.html', context)


#################
# pyecharts end
#################

def exportCSV(request, node_id):
    """导出节点信息随时间变化"""
    # print("node_id", node_id)
    node_message_resource = NodeMessageResource()

    if node_id == '-1':
        dataset = node_message_resource.export()
        filename = 'all_node'
    else:
        node = Node.objects.get(id=node_id)
        node_messages = node.nodemessage_set.all()  #
        dataset = node_message_resource.export(node_messages)
        filename = node.id

    response = HttpResponse(dataset.xls, content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = f'attachment; filename="{filename}.xls"'
    return response


last_abnormal_message = ['数据正常', '数据正常', '数据正常', '数据正常']


def abnormal(request, node_id):
    """节点异常信息报警"""
    node = Node.objects.get(id=node_id)
    node_messages = node.nodemessage_set.all()[:30].values()  # 获得前n条数据（最新数据）
    node_messages = list(node_messages)
    if len(node_messages) == 0:
        return HttpResponse("数据正常")

    battery_level_lst = []
    temperature_lst = []
    humidity_lst = []
    illumination_lst = []
    mq2PPM_lst = []
    for node_message in node_messages:
        battery_level_lst.append(node_message.get('battery_level'))
        temperature_lst.append(node_message.get('temperature'))
        humidity_lst.append(node_message.get('humidity'))
        illumination_lst.append(node_message.get('illumination'))
        mq2PPM_lst.append(node_message.get('mq2PPM'))

    def get_abnormal_percent(_lst, percent_threshold=0.1):
        avg_v = sum(_lst) / len(_lst)
        max_v = max(_lst)
        min_v = min(_lst)
        if (max_v - avg_v) / avg_v > percent_threshold or (avg_v - min_v) / avg_v > percent_threshold:
            return True
        else:
            return False

    battery_level_abnormal = get_abnormal_percent(battery_level_lst, 0.2)
    temperature_abnormal = get_abnormal_percent(temperature_lst)
    humidity_abnormal = get_abnormal_percent(humidity_lst)
    illumination_abnormal = get_abnormal_percent(illumination_lst)
    mq2PPM_abnormal = any([x > 5000 for x in mq2PPM_lst])  # get_abnormal_percent(mq2PPM_lst)

    abnormal_message = ""
    if battery_level_abnormal:
        abnormal_message += "电池异常 "
    if temperature_abnormal:
        abnormal_message += "温度异常 "
    if humidity_abnormal:
        abnormal_message += "湿度异常 "
    if illumination_abnormal:
        abnormal_message += "光照异常 "
    if mq2PPM_abnormal:
        abnormal_message += "可燃气体异常 "

    if abnormal_message == "":
        abnormal_message = "数据正常"

    # 从数据正常变成异常， 发送报警邮件
    if abnormal_message != "数据正常" and last_abnormal_message[int(node_id)] == '数据正常':
        time_now = datetime.now()
        logging.info(f"节点{node_id}在{time_now}:{abnormal_message}")
        success = send_mail(
            subject=f"节点{node_id}信息",
            message=f"节点{node_id}在{time_now}:{abnormal_message}",
            from_email="xxxx",
            recipient_list=['xxxx'],
            fail_silently=False,
        )
        print(f"发送邮件{success}\n\n")

    last_abnormal_message[int(node_id)] = abnormal_message

    print(abnormal_message)
    return HttpResponse(abnormal_message)
